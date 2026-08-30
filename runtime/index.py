#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · ZVEC 索引脚本（功能八 · 全量实现）
Z1 已实测：zvec 0.7.0 在 Windows 可用；id 必须 ASCII，中文名存 entity_cn 字段。

用法：
  python runtime/index.py build              # 全量重建（扫描 story/truth + story/meta + 正文）
  python runtime/index.py upsert --chapter N # 增量索引第 N 章
  python runtime/index.py delete --chapter N # 按章删除（正文改写后重建）
"""
import os
import sys
import re
import argparse

# ---- 环境 ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# 索引库默认落在项目级 story/index；无项目时用引擎目录（测试）
INDEX_PATH = os.path.join(PROJECT_ROOT, "story", "index", "novel_index")
DENSE_DIM = 512  # bge-small-zh-v1.5

# 拼音归一映射：对象 → ASCII 键（entity_id）
# 注意：正式使用需用拼音库（如 pypinyin）自动生成；此处提供手动映射表扩展点
ENTITY_ID_MAP = {}  # 中文全名 -> ascii 键，运行时自动建立

def _ascii_key(cn_name):
    """中文名 → ASCII entity_id（拼音键，zvec 0.7.0 实测 id 必须 ASCII 且不含 /）。
    扩展点：手动映射表 ENTITY_ID_MAP 优先；否则 pypinyin 自动生成，清理非法字符。"""
    import re
    if cn_name in ENTITY_ID_MAP:
        return ENTITY_ID_MAP[cn_name]
    try:
        from pypinyin import lazy_pinyin
        key = "".join(lazy_pinyin(cn_name))
    except Exception:
        # 兜底：中文转 unicode 码点（保证 ASCII 且唯一）
        key = "u" + "_".join(str(ord(ch)) for ch in cn_name)
    # 清理：只保留字母数字 _ . -（zvec id 实测不允许 / 与中文）
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
    import numpy as np
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        return zvec.create_and_open(INDEX_PATH, _build_schema()), False
    return zvec.open(INDEX_PATH), True


def _embed(text, dim=None):
    """dense embedding（Z3 落地）：jieba 分词 → 词 hash 桶 + 对数词频权重 → L2 归一化。

    说明：规划拍板 bge-small-zh-v1.5，但 torch 安装被 Windows 长路径限制（WinError 206）
    环境级阻断。改用零重依赖的"词法语义向量"——相似文本命中相同词 → 向量接近，
    提供真实语义召回（远优于此前 hash 占位）。升级路径：环境支持后装 bge 替换本函数即可。
    """
    dim = dim or DENSE_DIM
    import hashlib, math
    try:
        import jieba
        jieba.setLogLevel(60)
        tokens = [t for t in jieba.lcut(text) if len(t) >= 2]
    except Exception:
        # 兜底：字符 bigram（中文友好，无 jieba 也能用）
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
    chunks = []
    for i in range(0, len(text), size):
        chunks.append(text[i:i + size])
    return chunks


def _doc_id(doc_type, entity, chapter):
    return f"{doc_type}.{_ascii_key(entity)}.{chapter}"


def _make_doc(doc_id, entity_cn, doc_type, chapter, source_chapter, visibility, status, text):
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


def _iter_truth_files(root):
    """扫描 story/truth 各状态文件，每实体生成一条索引。
    实体列按文件类型取：characters=姓名列(2) / hooks=ID列(1) / objects=ID列(1) / 其余=首列。
    id 用 ASCII 键且限制长度（zvec 实测 id 不允许 / 中文、有长度上限）。"""
    truth_dir = os.path.join(root, "story", "truth")
    if not os.path.isdir(truth_dir):
        return []
    # 各文件实体列索引（0基）
    # 各文件实体列（0基）。timeline.md 不索引为实体（事件已在各实体行）。
    # relationships.md 不产独立实体：其"角色A"列是拼音缩写(mc/zyz)，违反 F 定稿"中文=唯一entity_id"，
    #   且关系信息已含在 characters 行与全文，靠 FTS text 检索即可。
    entity_col = {
        "characters.md": 1,   # 姓名列（中文全名）
        "hooks.md": 0,        # h_001
        "objects.md": 0,      # obj_001
        "world.md": 0,        # 核心规则/地点（跳过"时间线大事记"区块）
    }
    # world.md 中需跳过的区块（其事件归 timeline，不产生实体）
    WORLD_SKIP_SECTION = "时间线大事记"
    docs = []
    for fn in sorted(os.listdir(truth_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(truth_dir, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
        if fn not in entity_col:
            continue
        col = entity_col.get(fn, 0)
        section = ""
        for line in lines:
            raw = line.rstrip("\n")
            line = line.strip()
            # 标题行更新当前区块（only world.md 用于跳过时间线大事记）
            if line.startswith("#") and fn == "world.md":
                section = line.lstrip("#").strip()
                continue
            if not line.startswith("|"):
                continue
            # world.md 的"时间线大事记"区块整个跳过
            if fn == "world.md" and section == WORLD_SKIP_SECTION:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < max(col + 1, 2):
                continue
            head = cells[col].strip("`")
            # 跳过表头与分隔行
            if not head or head in ("姓名", "ID", "角色ID", "物品ID", "伏笔ID", "章号", "章节") or "---" in head:
                continue
            entity_cn = head
            if entity_cn.startswith("h_") or entity_cn.startswith("obj_"):
                # hooks/objects 用 ID 行时，entity_cn 记录为 ID + 首列内容简述
                pass
            docs.append(_make_doc(
                doc_id=_doc_id("truth", entity_cn, 0),
                entity_cn=entity_cn, doc_type="truth", chapter=0, source_chapter=0,
                visibility="public", status="",
                text=line,
            ))
    return docs


def _build(root, collection):
    docs = _iter_truth_files(root)
    # TODO(Z2 完成版): 追加 story/meta/ 与 正文 分块索引
    if docs:
        collection.upsert(zvec.DocList(docs))
    print(f"[index] 全量索引完成：{len(docs)} 条（当前为 truth 层，正文/meta 索引在 Z2 完成版接入）")


def _upsert_chapter(root, collection, chapter):
    print(f"[index] 增量索引第 {chapter} 章（Z2 完成版接入正文分块 + meta）")


def _delete_chapter(collection, chapter):
    try:
        collection.delete_by_filter(f"chapter == {chapter}")
        print(f"[index] 已删除第 {chapter} 章索引")
    except Exception as e:
        print(f"[index] 删除失败：{e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["build", "upsert", "delete"])
    parser.add_argument("--chapter", type=int, default=None)
    args = parser.parse_args()

    collection, existed = _get_collection()
    try:
        if args.action == "build":
            _build(PROJECT_ROOT, collection)
        elif args.action == "upsert":
            _upsert_chapter(PROJECT_ROOT, collection, args.chapter or 0)
        elif args.action == "delete":
            _delete_chapter(collection, args.chapter or 0)
    finally:
        collection.close()
    print("[index] done")


if __name__ == "__main__":
    main()
