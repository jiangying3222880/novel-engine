#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 · 正文观测 / 诊断脚本（P0 借鉴 · 防"假自检"）

定位：给阶段③自检提供**量化依据**，把"写得好不好"从拍脑袋变成可对照的指标。
原则（对齐技能理念）：**观测不是禁令**。本脚本只输出指标与 AI 高频词命中，
提示供人工/自检判断，**不拦截、不禁止、不黑名单**——内容层永远只引导。

用法：
  python runtime/check_text.py <正文文件或目录>          # 打印诊断
  python runtime/check_text.py <正文文件或目录> --json   # 输出 JSON（供自检引用）

输出指标：
  total_chars / paragraphs / avg_para_chars
  sentences / avg_sentence_chars / short_sentence_ratio(≤15字句占比，防"短句拉满"漂移)
  ai_lexicon_hits：常见 AI 高频词命中（计数，仅提示）
"""
import os
import re
import sys
import json
import argparse

# 常见 AI 高频词（观测用，非禁止清单——命中只提示，由人判断是否真 AI 味）
AI_LEXICON = [
    "仿佛", "似乎", "好像", "微微", "淡淡", "轻轻", "缓缓", "不由", "顿时",
    "然而", "却", "竟", "忽然", "突然", "心底", "眼中", "心头", "默默",
    "静静", "深深", "狠狠", "死死", "定定", "喃喃", "低语", "叹息", "凝视",
    "沉默", "终究", "终究是", "罢了", "呢喃", "一怔", "一震", "瞳孔", "嘴角",
    "勾勒", "弥漫", "充斥", "笼罩", "蔓延", "闪烁", "浮现", "闪过", "掠过",
]

SENTENCE_BOUNDARY = "。！？；…!?;"


def _read_text(path):
    if os.path.isdir(path):
        parts = []
        for fn in sorted(os.listdir(path)):
            if fn.endswith(".md"):
                try:
                    with open(os.path.join(path, fn), encoding="utf-8-sig") as f:
                        parts.append(f.read())
                except Exception:
                    continue
        return "\n".join(parts)
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def analyze(text):
    # 去 YAML 头
    text = re.sub(r"^---\s*.*?---\s*", "", text, flags=re.S)
    # 去 markdown 标题/引用/表格（只算正文）
    body_lines = [ln for ln in text.splitlines()
                  if ln.strip() and not ln.lstrip().startswith(("#", ">", "|", "-", "```", "*"))]
    body = "\n".join(body_lines)
    total_chars = len(re.sub(r"\s+", "", body))
    paragraphs = [p for p in re.split(r"\n{1,}", body) if p.strip()]
    avg_para_chars = round(total_chars / len(paragraphs), 1) if paragraphs else 0

    # 分句（按句末标点）
    sentences = [s for s in re.split(r"[。！？；!?;]", body) if s.strip()]
    avg_sentence_chars = round(
        (len("".join(re.findall(r"[^。！？；!?;\s]", body))) / len(sentences)), 1) if sentences else 0
    short_sentences = [s for s in sentences if len(re.sub(r"\s+", "", s)) <= 15]
    short_ratio = round(len(short_sentences) / len(sentences), 3) if sentences else 0

    # AI 高频词命中
    hits = {}
    for w in AI_LEXICON:
        c = body.count(w)
        if c > 0:
            hits[w] = c
    hits = dict(sorted(hits.items(), key=lambda x: -x[1]))

    return {
        "total_chars": total_chars,
        "paragraphs": len(paragraphs),
        "avg_para_chars": avg_para_chars,
        "sentences": len(sentences),
        "avg_sentence_chars": avg_sentence_chars,
        "short_sentence_ratio": short_ratio,
        "ai_lexicon_hits": hits,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="正文文件或目录")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()
    if not os.path.exists(args.path):
        print(f"路径不存在：{args.path}")
        sys.exit(1)
    res = analyze(_read_text(args.path))
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    print("== 正文观测 ==")
    print(f"  字数：{res['total_chars']} | 段落：{res['paragraphs']}（均 {res['avg_para_chars']} 字/段）")
    print(f"  句数：{res['sentences']}（均 {res['avg_sentence_chars']} 字/句）| 短句占比(≤15字)：{res['short_sentence_ratio']:.1%}")
    print("  AI 高频词命中（仅观测，非禁令）：")
    if res["ai_lexicon_hits"]:
        for w, c in list(res["ai_lexicon_hits"].items())[:15]:
            print(f"    {w}: {c}")
    else:
        print("    （无）")


if __name__ == "__main__":
    main()
