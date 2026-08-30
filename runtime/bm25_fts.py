#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · BM25 + FTS 全文检索（默认启用 · 零依赖）

定位：ZVEC（zvec SDK 混合检索）是可选增强；本项目初始化**默认启用 BM25+FTS**，
仅依赖 jieba（分词，已有），不依赖 zvec。即使 ZVEC 未安装/建库失败，检索不中断。

与 ZVEC 的差别：
  BM25+FTS ：词法匹配（分词→BM25 打分）。擅长精确词命中（专名/术语：沈青梧/剑胎/血月）。
             同义改写查不到；索引小；零依赖。
  ZVEC     ：混合检索（BM25 + dense 语义向量 + RRF 融合）。同义/语义近似可召回；
             需要安装 zvec SDK；索引大。
  两者都做：防剧透 cutoff + 知情权过滤（visibility）。

用法：
  python runtime/bm25_fts.py build --root <项目根>            # 建索引（默认 story/index/bm25/）
  python runtime/bm25_fts.py query --root <项目根> --text "沈青梧 剑胎" --cutoff 5 [--visibility public] [--topk 10]
"""
import os
import sys
import re
import json
import math
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

K1 = 1.5
B = 0.75


def _tokenize(text):
    """jieba 分词（词长>=2）；无 jieba 时兜底字符 bigram。"""
    try:
        import jieba
        jieba.setLogLevel(60)
        return [t for t in jieba.lcut(text) if len(t) >= 2]
    except Exception:
        return [text[i:i + 2] for i in range(0, max(len(text) - 1, 0))]


class BM25Index:
    def __init__(self):
        self.docs = {}   # id -> doc dict
        self.df = {}     # term -> doc 数
        self.N = 0
        self.avgdl = 0.0

    def add(self, doc):
        """doc: {id, text, doc_type, entity_cn, source_chapter, visibility, status}"""
        terms = _tokenize(doc["text"])
        freq = {}
        for t in terms:
            freq[t] = freq.get(t, 0) + 1
        dl = sum(freq.values())
        self.docs[doc["id"]] = {
            "text": doc["text"][:200],
            "terms": freq, "length": dl,
            "doc_type": doc.get("doc_type", ""),
            "entity_cn": doc.get("entity_cn", ""),
            "source_chapter": doc.get("source_chapter", 0),
            "visibility": doc.get("visibility", "public"),
            "status": doc.get("status", ""),
        }
        for t in freq:
            self.df[t] = self.df.get(t, 0) + 1

    def finalize(self):
        self.N = len(self.docs)
        total = sum(d["length"] for d in self.docs.values())
        self.avgdl = total / self.N if self.N else 0.0

    def _idf(self, t):
        n = self.df.get(t, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def _score(self, qterms, doc):
        s = 0.0
        for t in set(qterms):
            f = doc["terms"].get(t, 0)
            if not f:
                continue
            denom = f + K1 * (1 - B + B * doc["length"] / self.avgdl)
            s += self._idf(t) * (f * (K1 + 1)) / denom
        return s

    def query(self, text, cutoff=None, visibility=None, topk=10):
        """返回 [(score, doc), ...]，已按 source_chapter<=cutoff 与 visibility 过滤。"""
        qterms = _tokenize(text)
        if not qterms:
            return []
        scored = []
        for did, doc in self.docs.items():
            if cutoff is not None and doc["source_chapter"] > cutoff:
                continue
            if visibility and visibility != "public" and doc["visibility"] not in ("public", visibility):
                continue
            s = self._score(qterms, doc)
            if s > 0:
                scored.append((s, did, doc))
        scored.sort(key=lambda x: -x[0])
        return scored[:topk]

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "avgdl": self.avgdl, "N": self.N,
            "df": self.df,
            "docs": {k: {kk: vv for kk, vv in v.items() if kk != "terms"}
                     for k, v in self.docs.items()},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        self.avgdl, self.N, self.df = p["avgdl"], p["N"], p["df"]
        self.docs = {}
        for k, v in p["docs"].items():
            terms = _tokenize(v["text"])
            freq = {}
            for t in terms:
                freq[t] = freq.get(t, 0) + 1
            self.docs[k] = dict(v)
            self.docs[k]["terms"] = freq
            self.docs[k]["length"] = sum(freq.values())


# ---------- 数据源扫描 ----------
def _iter_truth_docs(root):
    """复用 index._iter_truth_files 的实体扫描（保证 entity_id 规则一致）。"""
    import index as idx
    try:
        return idx._iter_truth_files(root)
    except Exception:
        return []


def _iter_meta_docs(root):
    """story/meta/chapter_*.md → 每条一条 meta 文档。"""
    meta_dir = os.path.join(root, "story", "meta")
    docs = []
    if not os.path.isdir(meta_dir):
        return docs
    for fn in sorted(os.listdir(meta_dir)):
        if not (fn.endswith(".md") and fn.startswith("chapter_")):
            continue
        path = os.path.join(meta_dir, fn)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue
        m = re.search(r"chapter_id[:：]\s*(\d+)", text)
        ch = int(m.group(1)) if m else 0
        docs.append({
            "id": f"meta.{fn}", "text": text[:600], "doc_type": "meta",
            "entity_cn": fn, "source_chapter": ch, "visibility": "public", "status": "",
        })
    return docs


def _iter_正文_docs(root):
    """正文/ 分块（500-1000 字/块），按章。"""
    import index as idx
    body_dir = os.path.join(root, "正文")
    docs = []
    if not os.path.isdir(body_dir):
        return docs
    for fn in sorted(os.listdir(body_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(body_dir, fn)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue
        m = re.search(r"[第]?(\d+)[章节]", fn)
        ch = int(m.group(1)) if m else 0
        for i, chunk in enumerate(idx._chunk_text(text)):
            docs.append({
                "id": f"body.{fn}.{i}", "text": chunk, "doc_type": "正文",
                "entity_cn": fn, "source_chapter": ch, "visibility": "public", "status": "",
            })
    return docs


def _truth_to_dict(d):
    """把 index._iter_truth_files 的 zvec.Doc 转成统一 dict。"""
    return {
        "id": d.id,
        "text": d.fields.get("text", ""),
        "doc_type": d.fields.get("doc_type", ""),
        "entity_cn": d.fields.get("entity_cn", ""),
        "source_chapter": d.fields.get("source_chapter", 0),
        "visibility": d.fields.get("visibility", "public"),
        "status": d.fields.get("status", ""),
    }


def build(root, out=None):
    index = BM25Index()
    docs = [_truth_to_dict(d) for d in _iter_truth_docs(root)]
    docs += _iter_meta_docs(root) + _iter_正文_docs(root)
    for doc in docs:
        index.add(doc)
    index.finalize()
    if out is None:
        out = os.path.join(root, "story", "index", "bm25", "index.json")
    index.save(out)
    return index


def main():
    ap = argparse.ArgumentParser(description="BM25+FTS 全文检索（默认启用，零依赖）")
    ap.add_argument("cmd", choices=["build", "query"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--cutoff", type=int, default=None)
    ap.add_argument("--visibility", default=None)
    ap.add_argument("--topk", type=int, default=10)
    args = ap.parse_args()

    idx_path = os.path.join(args.root, "story", "index", "bm25", "index.json")
    if args.cmd == "build":
        idx = build(args.root, idx_path)
        print(f"BM25 索引已建：{idx.N} 条文档，{len(idx.df)} 个词项 → {idx_path}")
        return
    if args.cmd == "query":
        if not os.path.exists(idx_path):
            print(f"索引不存在（{idx_path}），先运行 build")
            return
        idx = BM25Index()
        idx.load(idx_path)
        hits = idx.query(args.text, cutoff=args.cutoff, visibility=args.visibility, topk=args.topk)
        print(f"查询「{args.text}」cutoff={args.cutoff} → {len(hits)} 条")
        for s, did, d in hits:
            print(f"  [{s:.3f}] {did} | {d['doc_type']} | {d['entity_cn'][:20]} | src_ch{d['source_chapter']} | {d['text'][:40]}...")


if __name__ == "__main__":
    main()
