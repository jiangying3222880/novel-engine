#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · ZVEC 检索脚本（功能八 · 修复版）
混合检索（dense + FTS，RRF 融合）+ 防剧透双查询 + 知情权过滤。

修复（对照审查报告）：
  BUG-3: 两路结果用 RRF（Ranked Reciprocal Fusion，k=60）重排融合，
         替代原"dense top20 + fts top20 无序拼接"。
  BUG-4: 索引路径从 runtime/config.yaml 读取（不再硬编码）。

用法：
  python runtime/query.py --text "林深现在在哪" --cutoff 5
  python runtime/query.py --text "伏笔" --cutoff 5 --visibility public
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import index
from index import _embed, DENSE_DIM, _load_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_CONFIG = _load_config(PROJECT_ROOT)
INDEX_PATH = os.path.join(PROJECT_ROOT, *_CONFIG["collection_path"].split("/"))

RRF_K = 60  # RRF 平滑参数


def _open_collection():
    import zvec
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError("索引不存在，先运行 python runtime/index.py build")
    return zvec.open(INDEX_PATH)


def _query_dense(text, topk):
    """dense 向量查询（jieba TF-IDF dense，语义召回）。"""
    import zvec
    return zvec.Query(field_name="dense", vector=_embed(text)), topk


def _query_fts(text, topk):
    """BM25 全文查询（zvec 0.7.0 用 Query + fts 参数）。"""
    import zvec
    return zvec.Query(field_name="text", fts=zvec.Fts(match_string=text)), topk


def _rrf_merge(result_sets, k=RRF_K):
    """RRF 融合（BUG-3 修复）：score = Σ 1/(k + rank)，跨两路排名融合。
    result_sets: list of [doc, ...]（每路按相关度排序）。返回 [(rid, score), ...] 降序。"""
    scores = {}
    for ranked in result_sets:
        for rank, r in enumerate(ranked):
            rid = getattr(r, "id", str(r))
            scores[rid] = scores.get(rid, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])


def _doc_by_id(collection, results):
    """把 RRF 排序的 (rid, score) 映射回 doc 对象（按 id 从结果池取）。"""
    pool = {}
    for ranked in results:
        for r in ranked:
            pool[getattr(r, "id", str(r))] = r
    return pool


def run(text, cutoff, visibility):
    collection = _open_collection()
    try:
        # 两路查询：dense + FTS，各取 top20
        result_sets = []
        for q, topk in [_query_dense(text, 20), _query_fts(text, 20)]:
            try:
                result_sets.append(list(collection.query(q, topk=topk)))
            except Exception:
                continue
        pool = _doc_by_id(collection, result_sets)
        ranked = _rrf_merge(result_sets)

        # 主查询：已解锁范围（source_chapter <= cutoff）按知情权过滤
        rows = []
        for rid, _score in ranked:
            r = pool.get(rid)
            if r is None:
                continue
            fields = getattr(r, "fields", {}) or {}
            sc = fields.get("source_chapter", 0)
            vis = fields.get("visibility", "public")
            if sc <= cutoff and (visibility == "all" or vis == visibility or vis == "public"):
                rows.append(f"[{sc}] {fields.get('entity_cn','')} {fields.get('text','')[:60]}")
        print("== 已解锁结果（RRF 融合排序） ==")
        for row in rows[:10]:
            print(row)

        # 副查询：未解锁范围 → 只给占位
        locked_hit = False
        for rid, _score in ranked:
            r = pool.get(rid)
            if r is None:
                continue
            fields = getattr(r, "fields", {}) or {}
            sc = fields.get("source_chapter", 0)
            if sc > cutoff:
                locked_hit = True
                print(f"[未解锁：第{sc}章 / {fields.get('entity_cn','')}]")
        if not locked_hit:
            print("（未解锁范围无命中）")
    finally:
        collection.close()


def main():
    global PROJECT_ROOT, INDEX_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--cutoff", type=int, default=0, help="防剧透基准章，>cutoff 只给占位")
    parser.add_argument("--visibility", default="all", help="all/public/角色名")
    parser.add_argument("--root", default=None, help="项目根目录（缺省：当前工作目录）")
    args = parser.parse_args()
    PROJECT_ROOT = os.path.abspath(args.root or os.getcwd())
    INDEX_PATH = os.path.join(PROJECT_ROOT, *_CONFIG["collection_path"].split("/"))
    run(args.text, args.cutoff, args.visibility)


if __name__ == "__main__":
    main()
