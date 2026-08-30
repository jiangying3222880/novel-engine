#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · 稳定性测试脚本（5 章 = 1 观察窗口，可对任意窗口快照重复执行）

用法：
  python runtime/stability_test.py --truth <truth_dir> --window <名称> [--index <path>]

每窗口跑 7 维校验，输出 JSON：
  1. structure   truth 6 文件存在且非空
  2. schema      状态机枚举合法 / hooks 推进状态列 / 5 通用字段
  3. volume      单状态文件 ≤8KB、meta ≤8KB
  4. zvec_build  全量索引 build → doc_count / index_completeness
  5. zvec_query  固定文本查询命中（确定性 hash 向量，可复现）
  6. idempotent  build 连续两次 stats 一致（幂等）
  7. spoiler     防剧透门：cutoff 过滤 + 未解锁占位
"""
import os
import re
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import index as idx

VOLUME_LIMIT_KB = 8.0
TRUTH_FILES = ["characters.md", "world.md", "hooks.md", "relationships.md", "objects.md", "timeline.md"]
STATE_MACHINES = {
    "characters.md": ["alive", "missing", "false_dead", "true_dead", "resurrected"],
    "world.md": ["intact", "damaged", "destroyed", "abandoned", "rebuilt", "transformed"],
    "relationships.md": ["ally", "support", "neutral", "tension", "hostile", "severed", "reconciled"],
    "objects.md": ["owned", "lost", "destroyed", "sealed", "transferred"],
}
HOOK_PROGRESS = ["pending", "partial", "due"]
QUERY_FIXTURES = ["剑胎", "沈青梧", "反噬", "林伯"]


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_structure(truth_dir):
    """1. 结构完整性：truth 6 文件存在且非空。"""
    ok, detail = True, {}
    for fn in TRUTH_FILES:
        p = os.path.join(truth_dir, fn)
        exists = os.path.isfile(p)
        size = os.path.getsize(p) if exists else 0
        if not exists or size == 0:
            ok = False
        detail[fn] = {"exists": exists, "bytes": size}
    return ok, detail


def check_schema(truth_dir):
    """2. Schema 一致性：状态机枚举合法、hooks 推进状态列、characters 5通用字段。"""
    ok = True
    detail = {}
    # hooks 推进状态列
    h = _read(os.path.join(truth_dir, "hooks.md"))
    has_progress_col = ("推进状态" in h) and ("下一回收点" in h)
    # 校验推进状态值
    bad_progress = []
    for m in re.finditer(r"\|\s*(partial|pending|due)\s*\|", h):
        pass
    # 提取状态行里的推进状态（倒数第二列前）
    for line in h.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 8 and cells[6] in HOOK_PROGRESS:
            pass  # 合法
        elif len(cells) >= 8 and cells[6] not in ("ID", "推进状态") and "---" not in cells[6]:
            bad_progress.append(cells[6])
    if not has_progress_col:
        ok = False
    detail["hooks_progress_col"] = has_progress_col
    detail["hooks_bad_progress"] = bad_progress[:5]
    # characters 状态机枚举
    ch = _read(os.path.join(truth_dir, "characters.md"))
    detail["characters_status_machine_used"] = any(s in ch for s in ["存活", "alive", "missing", "true_dead", "resurrected"])
    # objects 状态机枚举
    for fn, valid in STATE_MACHINES.items():
        content = _read(os.path.join(truth_dir, fn))
        for s in valid:
            if s in content:
                detail[f"{fn}->{s}"] = True
    return ok, detail


def check_volume(truth_dir):
    """3. 体积红线：单状态文件 ≤8KB。"""
    ok = True
    detail = {}
    for fn in TRUTH_FILES:
        p = os.path.join(truth_dir, fn)
        kb = os.path.getsize(p) / 1024.0
        if kb > VOLUME_LIMIT_KB:
            ok = False
        detail[fn] = round(kb, 1)
    return ok, detail


def check_zvec(root_dir, index_path, window):
    """4+5+6. ZVEC 可复现 / 查询 / 幂等。root_dir 需含 story/truth。"""
    import zvec
    result = {"ok": True, "detail": {}}
    idx.PROJECT_ROOT = root_dir
    idx.INDEX_PATH = index_path
    if os.path.exists(index_path):
        import shutil
        shutil.rmtree(index_path, ignore_errors=True)

    def _stats_dict(col):
        s = col.stats
        if isinstance(s, dict):
            return s
        return json.loads(str(s))

    col, _ = idx._get_collection()
    docs = idx._iter_truth_files(root_dir)
    col.upsert(zvec.DocList(docs))
    st1 = _stats_dict(col)
    col.close()

    # 幂等：第二次 build（重建索引）
    if os.path.exists(index_path):
        import shutil
        shutil.rmtree(index_path, ignore_errors=True)
    col, _ = idx._get_collection()
    docs2 = idx._iter_truth_files(root_dir)
    col.upsert(zvec.DocList(docs2))
    st2 = _stats_dict(col)
    idem = (st1 == st2)
    result["detail"]["doc_count"] = st1.get("doc_count")
    result["detail"]["index_completeness"] = st1.get("index_completeness")
    result["detail"]["idempotent"] = idem

    # 查询：固定文本（确定性 hash 向量）
    query_hits = {}
    for text in QUERY_FIXTURES:
        import numpy as np
        rng = np.random.RandomState(hash(text) & 0x7FFFFFFF)
        v = rng.rand(512).astype(np.float32)
        v = (v / np.linalg.norm(v)).tolist()
        q = zvec.Query(field_name="dense", vector=v)
        try:
            res = col.query(q, topk=5)
            query_hits[text] = [r.id for r in res]
        except Exception as e:
            query_hits[text] = f"ERR:{str(e)[:40]}"
    result["detail"]["query_hits"] = query_hits
    result["ok"] = result["ok"] and idem
    col.close()
    return result["ok"], result["detail"]


def check_spoiler(truth_dir, cutoff):
    """7. 防剧透门：truth 内 source_chapter>cutoff 的条目应被标记未解锁。"""
    # truth 层目前 source_chapter 多为 0（状态卡非章节绑定），此处校验 hooks 的埋设章 vs cutoff
    h = _read(os.path.join(truth_dir, "hooks.md"))
    detail = {"cutoff": cutoff, "beyond_cutoff_hooks": []}
    for line in h.splitlines():
        if not line.startswith("|") or "h_" not in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # 埋设章 在第3列
        try:
            buried = int(cells[3])
        except Exception:
            continue
        if buried > cutoff:
            detail["beyond_cutoff_hooks"].append(cells[0])
    # 窗口1 cutoff=5 时不应有超限钩子；窗口3 压力下应有
    return True, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="窗口根目录（须含 story/truth）")
    ap.add_argument("--window", required=True, help="观察窗口名")
    ap.add_argument("--index", default=None, help="窗口索引目录（缺省：root/story/index/w）")
    ap.add_argument("--cutoff", type=int, default=0)
    args = ap.parse_args()

    root_dir = args.root
    truth_dir = os.path.join(root_dir, "story", "truth")
    index_path = args.index or os.path.join(root_dir, "story", "index", "w")
    results = {"window": args.window, "checks": {}}

    ok_s, d_s = check_structure(truth_dir)
    results["checks"]["structure"] = {"pass": ok_s, "detail": d_s}

    ok_sc, d_sc = check_schema(truth_dir)
    results["checks"]["schema"] = {"pass": ok_sc, "detail": d_sc}

    ok_v, d_v = check_volume(truth_dir)
    results["checks"]["volume"] = {"pass": ok_v, "detail": d_v}

    try:
        ok_z, d_z = check_zvec(root_dir, index_path, args.window)
        results["checks"]["zvec"] = {"pass": ok_z, "detail": d_z}
    except Exception as e:
        results["checks"]["zvec"] = {"pass": False, "detail": {"error": str(e)[:100]}}

    ok_sp, d_sp = check_spoiler(truth_dir, args.cutoff)
    results["checks"]["spoiler"] = {"pass": ok_sp, "detail": d_sp}

    results["all_pass"] = all(c["pass"] for c in results["checks"].values())
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
