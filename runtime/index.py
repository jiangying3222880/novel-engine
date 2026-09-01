#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · ZVEC 索引脚本（功能八 · 修复版）
Z1 已实测：zvec 0.7.0 在 Windows 可用；id 必须 ASCII，中文名存 entity_cn 字段。
F 定稿：中文姓名 = 唯一 entity_id（经 pypinyin 转 ASCII 键，zvec 约束）。

用法：
  python runtime/index.py build              # 全量重建（truth + 故事/元数据 + 正文，先清空旧库）
  python runtime/index.py upsert --chapter N # 增量索引第 N 章（meta + 正文，先删旧章）
  python runtime/index.py delete --chapter N # 按章删除（正文改写后重建）

配置：读取 runtime/config.yaml（paths.collection_path / paths.body_dir）。失败时用默认值。
"""
import os
import sys
import re
import shutil
import argparse

# ---- 环境 ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "deps"))  # 离线 vendored 依赖 (jieba/pyyaml/pypinyin)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# 索引库默认落在项目级 故事/索引；无项目时用引擎目录（测试）
INDEX_PATH = os.path.join(PROJECT_ROOT, "故事", "索引", "novel_index")
DENSE_DIM = 512  # bge-small-zh-v1.5

# 拼音归一映射：对象 → ASCII 键（entity_id）
ENTITY_ID_MAP = {}  # 中文全名 -> ascii 键，运行时自动建立


def _load_config(root):
    """读 runtime/config.yaml 作为配置源（BUG-4 修复：config 不再是死配置）。
    失败时返回默认值，不中断。"""
    cfg = {
        "mode": "bm25_fts",
        "collection_path": "故事/索引/novel_index",
        "bm25_path": "故事/索引/bm25/index.json",
        "body_dir": "正文",
    }
    try:
        import yaml
        cpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        with open(cpath, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        p = data.get("paths", {}) or {}
        r = data.get("retrieval", {}) or {}
        cfg["mode"] = r.get("mode", cfg["mode"])
        cfg["collection_path"] = p.get("collection_path", cfg["collection_path"])
        cfg["bm25_path"] = p.get("bm25_path", cfg["bm25_path"])
        cfg["body_dir"] = p.get("body_dir", cfg["body_dir"])
    except Exception:
        pass
    return cfg


_CONFIG = _load_config(PROJECT_ROOT)


def _ascii_key(cn_name):
    """中文名 → ASCII entity_id（拼音键，zvec 0.7.0 实测 id 必须 ASCII 且不含 /）。"""
    if cn_name in ENTITY_ID_MAP:
        return ENTITY_ID_MAP[cn_name]
    try:
        from pypinyin import lazy_pinyin
        key = "".join(lazy_pinyin(cn_name))
    except Exception:
        key = "u" + "_".join(str(ord(ch)) for ch in cn_name)
    key = re.sub(r"[^A-Za-z0-9_.\-]", "_", key)
    return key or "entity"


def _build_schema():
    import zvec
    return zvec.CollectionSchema(
        name="novel_index",
        fields=[
            zvec.FieldSchema(name="entity_cn", data_type=zvec.DataType.STRING),
            zvec.FieldSchema(name="doc_type", data_type=zvec.DataType.STRING),
            zvec.FieldSchema(name="chapter", data_type=zvec.DataType.INT32),
            zvec.FieldSchema(name="source_chapter", data_type=zvec.DataType.INT32),
            zvec.FieldSchema(name="visibility", data_type=zvec.DataType.STRING),
            zvec.FieldSchema(name="status", data_type=zvec.DataType.STRING),
            zvec.FieldSchema(name="text", data_type=zvec.DataType.STRING,
                             index_param=zvec.FtsIndexParam()),
        ],
        vectors=[zvec.VectorSchema(name="dense", dimension=DENSE_DIM,
                                   data_type=zvec.DataType.VECTOR_FP32)],
    )


def _get_collection():
    import zvec
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        return zvec.create_and_open(INDEX_PATH, _build_schema()), False
    return zvec.open(INDEX_PATH), True


def _reset_collection():
    """删除整个索引目录（build 时先清空，避免"只增不删"脏数据残留）。"""
    if os.path.isdir(INDEX_PATH):
        shutil.rmtree(INDEX_PATH, ignore_errors=True)


def _embed(text, dim=None):
    """dense embedding（Z3 落地）：jieba 分词 → 词 hash 桶 + 对数词频权重 → L2 归一化。"""
    dim = dim or DENSE_DIM
    import hashlib, math
    try:
        import jieba
        jieba.setLogLevel(60)
        tokens = [t for t in jieba.lcut(text) if len(t) >= 2]
    except Exception:
        tokens = [text[i:i + 2] for i in range(0, max(len(text) - 1, 0))]
    vec = [0.0] * dim
    freq = {}
    for tk in tokens:
        freq[tk] = freq.get(tk, 0) + 1
    for tk, c in freq.items():
        h = int(hashlib.md5(tk.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0 + 0.5 * math.log(c)
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _chunk_text(text, size=800):
    """正文按 500-1000 字分块。"""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= size:
        return [text] if text else []
    return [text[i:i + size] for i in range(0, len(text), size)]


def _doc_id(doc_type, entity, chapter):
    return f"{doc_type}.{_ascii_key(entity)}.{chapter}"


def _make_doc(doc_id, entity_cn, doc_type, chapter, source_chapter, visibility, status, text):
    """构造文档对象。zvec 可用 → zvec.Doc（含 dense 向量，供 ZVEC 模式）；
    zvec 不可用 → 纯 dict（供 BM25+FTS 默认模式，避免默认检索因 zvec 缺失而中断）。"""
    try:
        import zvec
        return zvec.Doc(
            id=doc_id,
            vectors={"dense": _embed(text)},
            fields={
                "entity_cn": entity_cn, "doc_type": doc_type,
                "chapter": chapter, "source_chapter": source_chapter,
                "visibility": visibility, "status": status or "",
                "text": text,
            },
        )
    except Exception:
        return {
            "id": doc_id,
            "text": text,
            "doc_type": doc_type,
            "entity_cn": entity_cn,
            "chapter": chapter,
            "source_chapter": source_chapter,
            "visibility": visibility,
            "status": status or "",
        }


# ---------- 字段解析（BUG-2 修复）----------
# truth 各文件的字段列名别名（按列名匹配，不依赖固定列位，模板列序变化也能适配）
_FIELD_ALIASES = {
    "source_chapter": ["source_chapter", "埋设章", "产生于章", "章号"],
    "visibility": ["visibility", "可见性"],
    "status": ["status", "状态"],
}


def _is_header(cells):
    """判断表格行是否为表头（含任一已知字段名）。"""
    for c in cells:
        cc = c.strip().lower()
        for aliases in _FIELD_ALIASES.values():
            for a in aliases:
                if a.lower() in cc:
                    return True
    return False


def _field_value(cells, header, field, default="", is_int=False):
    """按表头映射取字段值；缺失或非法返回 default。"""
    if header is None or field not in header:
        return default
    idx = header[field]
    if idx is None or idx >= len(cells):
        return default
    raw = cells[idx].strip()
    if is_int:
        m = re.search(r"\d+", raw)
        return int(m.group(0)) if m else default
    return raw or default


def _iter_truth_files(root):
    """扫描 故事/真相 各状态文件，每实体生成一条索引。
    修复 BUG-2：按表头列名解析 visibility / source_chapter / status（缺省 public/0），
    供 query.py 的防剧透 cutoff 与知情权过滤真正生效。"""
    truth_dir = os.path.join(root, "故事", "真相")
    if not os.path.isdir(truth_dir):
        return []
    # 各文件实体列（0基）。relationships/timeline 不产独立实体（关系/事件已在其他行+全文 FTS）。
    entity_col = {
        "characters.md": 1,   # 姓名列（中文全名）
        "hooks.md": 0,        # h_001
        "objects.md": 0,      # obj_001
        "world.md": 0,        # 核心规则/地点（跳过"时间线大事记"区块）
    }
    WORLD_SKIP_SECTION = "时间线大事记"
    docs = []
    for fn in sorted(os.listdir(truth_dir)):
        if not fn.endswith(".md") or fn not in entity_col:
            continue
        path = os.path.join(truth_dir, fn)
        try:
            # utf-8-sig：兼容 PowerShell 写出的带 BOM 文件（BOM 会让表头行首字符不是 | 而漏扫）
            with open(path, "r", encoding="utf-8-sig") as f:
                raw = f.read()
        except Exception:
            continue
        col = entity_col[fn]
        section = ""
        header = None  # 字段名 -> 列索引
        lines_list = [ln.strip() for ln in raw.splitlines()]
        i = 0
        while i < len(lines_list):
            line = lines_list[i]
            if line.startswith("#") and fn == "world.md":
                section = line.lstrip("#").strip()
                i += 1
                continue
            if not line.startswith("|"):
                i += 1
                continue
            if fn == "world.md" and section == WORLD_SKIP_SECTION:
                i += 1
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            is_sep = all(re.fullmatch(r"[-: ]+", c or "") for c in cells)
            # 表头判定：本行下一行是分隔行（|---|）→ 本行为表头（比关键词更通用，characters 等无字段列也能识别）
            next_is_sep = False
            if i + 1 < len(lines_list):
                nxt = lines_list[i + 1]
                if nxt.startswith("|"):
                    ncells = [c.strip() for c in nxt.strip("|").split("|")]
                    next_is_sep = all(re.fullmatch(r"[-: ]+", c or "") for c in ncells)
            if header is None and next_is_sep:
                header = {}
                for j, cname in enumerate(cells):
                    cc = cname.lower()
                    for field, aliases in _FIELD_ALIASES.items():
                        if field in header:
                            continue
                        for a in aliases:
                            if a.lower() in cc:
                                # 排除"推进状态"误匹配 status（hooks 的推进状态列不是状态机状态）
                                if field == "status" and "推进" in cc:
                                    continue
                                header[field] = j
                                break
                i += 1
                continue
            if header is None or is_sep:
                i += 1
                continue
            head = cells[col].strip("`")
            if not head or head in ("姓名", "ID", "角色ID", "物品ID", "伏笔ID", "章号", "章节") or "---" in head:
                i += 1
                continue
            source_chapter = _field_value(cells, header, "source_chapter", 0, is_int=True)
            visibility = _field_value(cells, header, "visibility", "public")
            status = _field_value(cells, header, "status", "")
            docs.append(_make_doc(
                doc_id=_doc_id("truth", head, 0),
                entity_cn=head, doc_type="truth", chapter=0,
                source_chapter=source_chapter, visibility=visibility, status=status,
                text=line,
            ))
            i += 1
    return docs


def _iter_meta_docs(root):
    """故事/元数据/chapter_*.md → 每条一条 meta 文档。
    修复 BUG-5 问题 2：章号从文件名解析（chapter_0007.md → 7），不再依赖正文里的 chapter_id 字段。"""
    meta_dir = os.path.join(root, "故事", "元数据")
    docs = []
    if not os.path.isdir(meta_dir):
        return docs
    for fn in sorted(os.listdir(meta_dir)):
        if not (fn.endswith(".md") and fn.startswith("chapter_")):
            continue
        path = os.path.join(meta_dir, fn)
        try:
            with open(path, encoding="utf-8-sig") as f:
                text = f.read()
        except Exception:
            continue
        m = re.search(r"chapter_(\d+)\.md", fn)
        ch = int(m.group(1)) if m else 0
        docs.append(_make_doc(
            doc_id=f"meta.{_ascii_key(fn)}.{ch}",
            entity_cn=fn, doc_type="meta", chapter=ch, source_chapter=ch,
            visibility="public", status="", text=text[:800],
        ))
    return docs


def _iter_正文_docs(root):
    """正文/ 分块（500-1000 字/块），按章。
    修复 BUG-5 问题 3：正文目录名从 config.yaml 的 paths.body_dir 读（缺省"正文"）。"""
    body_dir = os.path.join(root, _CONFIG["body_dir"])
    docs = []
    if not os.path.isdir(body_dir):
        return docs
    for fn in sorted(os.listdir(body_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(body_dir, fn)
        try:
            with open(path, encoding="utf-8-sig") as f:
                text = f.read()
        except Exception:
            continue
        m = re.search(r"(\d+)", fn)
        ch = int(m.group(1)) if m else 0
        for i, chunk in enumerate(_chunk_text(text)):
            docs.append(_make_doc(
                doc_id=f"body.{_ascii_key(fn)}.{i}",
                entity_cn=fn, doc_type="正文", chapter=ch, source_chapter=ch,
                visibility="public", status="", text=chunk,
            ))
    return docs


def _build(root, collection):
    """全量重建（BUG-1/10 修复）：先清空旧库，再索引 truth + meta + 正文。"""
    import zvec
    docs = _iter_truth_files(root) + _iter_meta_docs(root) + _iter_正文_docs(root)
    if docs:
        collection.upsert(zvec.DocList(docs))
    print(f"[index] 全量索引完成：{len(docs)} 条（truth+meta+正文）")
    return len(docs)


def _upsert_chapter(root, collection, chapter):
    """增量索引第 N 章（BUG-1 修复）：先删旧章索引，再索引该章 meta + 正文分块。"""
    try:
        collection.delete_by_filter(f"chapter == {chapter}")
    except Exception:
        pass
    docs = [d for d in (_iter_meta_docs(root) + _iter_正文_docs(root))
            if d.fields["chapter"] == chapter]
    if docs:
        collection.upsert(zvec.DocList(docs))
    print(f"[index] 增量索引第 {chapter} 章：{len(docs)} 条（meta+正文）")


def _delete_chapter(collection, chapter):
    try:
        collection.delete_by_filter(f"chapter == {chapter}")
        print(f"[index] 已删除第 {chapter} 章索引")
    except Exception as e:
        print(f"[index] 删除失败：{e}")


def main():
    global PROJECT_ROOT, INDEX_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["build", "upsert", "delete"])
    parser.add_argument("--chapter", type=int, default=None)
    parser.add_argument("--root", default=None, help="项目根目录（缺省：当前工作目录）")
    args = parser.parse_args()

    # --root 缺省用 cwd，让"在项目根跑 python runtime/index.py build"作用于项目
    PROJECT_ROOT = os.path.abspath(args.root or os.getcwd())
    # 从 config 读取索引路径（BUG-4 修复：路径统一）
    INDEX_PATH = os.path.join(PROJECT_ROOT, *_CONFIG["collection_path"].split("/"))

    try:
        if args.action == "build":
            # 先清空旧库，避免脏数据残留
            _reset_collection()
            collection, _ = _get_collection()
            try:
                _build(PROJECT_ROOT, collection)
            finally:
                collection.close()
        else:
            collection, existed = _get_collection()
            try:
                if args.action == "upsert":
                    _upsert_chapter(PROJECT_ROOT, collection, args.chapter or 0)
                elif args.action == "delete":
                    _delete_chapter(collection, args.chapter or 0)
            finally:
                collection.close()
    except Exception as e:
        print(f"[index] 失败：{e}")
        sys.exit(1)
    print("[index] done")


if __name__ == "__main__":
    main()
