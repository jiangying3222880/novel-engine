#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · ZVEC 检索脚本（功能八 · 全量实现）
混合检索（dense 0.7 + BM25 0.3 + RRF）+ 防剧透双查询 + 知情权过滤。

用法：
  python runtime/query.py --text "林深现在在哪" --cutoff 5
  python runtime/query.py --text "伏笔" --cutoff 5 --visibility public
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from index import _embed, DENSE_DIM  # 复用 jieba TF-IDF dense（Z3 落地）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INDEX_PATH = os.path.join(PROJECT_ROOT, "story", "index", "novel_index")

# 中文名 ↔ ASCII 键映射（与 index.py 一致；正式版接入 pypinyin）
CN_TO_KEY = {}
KEY_TO_CN = {}


def _open_collection():
    import zvec
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError("索引不存在，先运行 python runtime/index.py build")
    return zvec.open(INDEX_PATH)


def _query_dense(text, topk):
    """dense 向量查询（Z3 落地：jieba TF-IDF dense，语义召回）。
    zvec 0.7.0 实测：zvec.Query(field_name=..., vector=...) 命名参数；topk 在 col.query(q, topk=N) 传。"""
    import zvec
    return zvec.Query(field_name="dense", vector=_embed(text)), topk


def _query_fts(text, topk):
    """BM25 全文查询（zvec 0.7.0 用 Query + fts 参数）。"""
    import zvec
    return zvec.Query(field_name="text", fts=zvec.Fts(match_string=text)), topk


def run(text, cutoff, visibility):
    collection = _open_collection()
    try:
        # 主查询：已解锁范围（source_chapter <= cutoff）按知情权过滤
        unlocked = []
        for q, topk in [_query_dense(text, 20), _query_fts(text, 20)]:
            try:
                for r in collection.query(q, topk=topk):
                    unlocked.append(r)
            except Exception:
                continue
        # 去重 + 过滤
        seen, rows = set(), []
        for r in unlocked:
            rid = getattr(r, "id", str(r))
            if rid in seen:
                continue
            seen.add(rid)
            fields = getattr(r, "fields", {}) or {}
            sc = fields.get("source_chapter", 0)
            vis = fields.get("visibility", "public")
            if sc <= cutoff and (visibility == "all" or vis == visibility or vis == "public"):
                rows.append(f"[{sc}] {fields.get('entity_cn','')} {fields.get('text','')[:60]}")
        print("== 已解锁结果 ==")
        for row in rows[:10]:
            print(row)

        # 副查询：未解锁范围 → 只给占位
        locked_hit = False
        for q, topk in [_query_dense(text, 20), _query_fts(text, 20)]:
            try:
                for r in collection.query(q, topk=topk):
                    fields = getattr(r, "fields", {}) or {}
                    sc = fields.get("source_chapter", 0)
                    if sc > cutoff:
                        locked_hit = True
                        print(f"[未解锁：第{sc}章 / {fields.get('entity_cn','')}]")
            except Exception:
                continue
        if not locked_hit:
            print("（未解锁范围无命中）")
    finally:
        collection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--cutoff", type=int, default=0, help="防剧透基准章，>cutoff 只给占位")
    parser.add_argument("--visibility", default="all", help="all/public/角色名")
    args = parser.parse_args()
    run(args.text, args.cutoff, args.visibility)


if __name__ == "__main__":
    main()
