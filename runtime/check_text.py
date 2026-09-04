#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.5 · 正文观测 / 门禁脚本（P0 借鉴 · 防"假自检"）

定位：给阶段③自检提供量化依据，并把"写够字数 + 不扎堆 AI 词"变成写作纪律。

原则（对齐技能"引导不是禁止"）：
  - 默认（观测）：只输出指标与 AI 高频词命中，不拦截。
  - --target N：字数门禁，正文 <85%N 或 >115%N 即 FAIL（正负15%验收，用户口径）。
  - --strict：高频词三级门禁（人类也会用这些词 -> 不搞零容忍）：
      1 次 = 绿（提示 + 换法，不拦）
      2 次 = 黄（必须换掉 1 个，附换法）
      >=3 次 = 红 FAIL（打印全部命中句 + 逐条换法）
    - 密度归一：正文 <2000 字 -> 阈值减半（防"写短反而易过"）
    - 近邻冗余：同词在 <=2 段内出现 2 次 -> 提示局部重复（AI 特征是扎堆）

用法：
  python runtime/check_text.py <正文文件或目录>                            # 观测
  python runtime/check_text.py <正文文件或目录> --target 3000              # 字数门禁
  python runtime/check_text.py <正文文件或目录> --target 3000 --strict      # 字数+高频词门禁
  python runtime/check_text.py <正文文件或目录> --target 3000 --strict --json

观测辅助（观察级，只提示不拦截，供阶段③人工核对）：
  --hook        检查文首 300 字是否命中回归式标记（"从什么时候开始"等）
  --consist     按出现顺序导出时序副词及其句子，人工核对先后是否自洽
  --digits      导出章节内所有数字（含中文数字）及上下文，人工核对金额/数量统一
  --facts <台账> 将正文与 facts.md 台账的金额/正文写法比对，提示不一致
  示例：python runtime/check_text.py <正文> --target 3000 --strict --hook --digits --facts ../../真相/facts.md

退出码：0=通过  1=路径错误  2=门禁 FAIL（字数或高频词）
"""
import os, re, sys, json, argparse

# 常见 AI 高频词（观测用，非禁止清单）
AI_LEXICON = [
    "仿佛", "似乎", "好像", "微微", "淡淡", "轻轻", "缓缓", "不由", "顿时",
    "然而", "却", "竟", "忽然", "突然", "心底", "眼中", "心头", "默默",
    "静静", "深深", "狠狠", "死死", "定定", "喃喃", "低语", "叹息", "凝视",
    "沉默", "终究", "终究是", "罢了", "呢喃", "一怔", "一震", "瞳孔", "嘴角",
    "勾勒", "弥漫", "充斥", "笼罩", "蔓延", "闪烁", "浮现", "闪过", "掠过",
]

# 写作纪律高频词门禁清单 + 功能换法（对应 references/anti-ai-swaps.md）
STRICT_LEXICON = {
    "忽然": ["时间锚点（三点一刻，门响了）", "动作打断（手机在兜里震）", "感官触发（一声汽笛炸开）", "直接删（事件自带突兀）"],
    "缓缓": ["动作拆解（他抬手，像被慢放）", "物理细节（指节发白）", "删"],
    "淡淡": ["对白内容示态度", "微表情", "删"],
    "轻轻": ["物理细节（指腹蹭过/几乎没声）", "删"],
    "静静": ["环境细节（窗外只剩路灯）", "删（让画面自己静）"],
    "掠过": ["具体部位+动作（眼尾扫过/衣摆带风）", "删"],
    "心头": ["直接内心独白（去掉'心头'壳）"],
    "只得": ["动作决定（他抓起包就走）", "删"],
    "默默": ["用沉默的行动表现", "删"],
    "些许": ["量化（三分/半秒）", "删"],
}

# 开篇回归式标记（观察级：--hook 检测文首是否有回顾式写法）
HOOK_REVIEW_MARKERS = [
    "从什么时候开始", "说起来", "不知从哪里说起", "这事得从", "回想起来",
    "时间过得", "不知从何时起", "说来话长",
]

# 时序副词（观察级：--consist 按出现顺序导出，人工核对先后自洽）
TIMELINE_ADVERBS = [
    "先", "后", "接着", "随即", "然后", "再后来", "后来", "最终", "终于",
    "第二天", "次日", "当晚", "当天", "晚上", "早上", "中午", "下午", "深夜",
]

# 中文数字（--digits 提取）
CN_NUM_RE = r"[零一二两三四五六七八九十百千万]"

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

    # AI 高频词命中（观测）
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
        "body": body,
        "paragraphs_list": paragraphs,
    }


def strict_scan(res):
    """返回 (fail, messages)。三级频率制 + 密度归一 + 近邻冗余。"""
    paras = res["paragraphs_list"]
    total = res["total_chars"]
    thresh = 3 if total >= 2000 else 2          # 密度归一：<2000 字阈值减半
    hits = {}
    for wi, para in enumerate(paras):
        for w in STRICT_LEXICON:
            start = 0
            while True:
                idx = para.find(w, start)
                if idx < 0:
                    break
                seg_start = para.rfind("。", 0, idx) + 1
                seg_end = para.find("。", idx + len(w))
                if seg_end < 0:
                    seg_end = len(para)
                sentence = para[seg_start:seg_end].strip()
                hits.setdefault(w, []).append((wi, sentence))
                start = idx + len(w)

    messages = []
    fail = False
    for w in sorted(hits):
        occ = hits[w]
        cnt = len(occ)
        tier = 'red' if cnt >= thresh else ('yellow' if cnt == 2 else 'green')
        if tier == 'red':
            fail = True
        msg = f"  [{tier.upper()}] {w} x{cnt}（阈值>= {thresh}）"
        if tier == 'yellow':
            msg += " 换掉至少1个，换法见 anti-ai-swaps.md"
        elif tier == 'red':
            msg += " FAIL — 命中句：" + " / ".join(f"§{i+1}:{s}" for i, s in occ)
            msg += " ｜ 换法：" + "；".join(STRICT_LEXICON[w][:2])
        # 近邻冗余（<=2 段内同词 2 次）
        prox = []
        for i in range(len(occ) - 1):
            if occ[i + 1][0] - occ[i][0] <= 2:
                prox.append(f"§{occ[i][0]+1}-§{occ[i+1][0]+1}")
        if prox:
            msg += " ｜ 近邻重复: " + "，".join(prox)
        messages.append(msg)
    return fail, messages


def _sentence_around(text, start, end, word):
    """返回包含 word 的最小句段（按句末标点切）。"""
    seg_start = text.rfind("。", 0, start) + 1
    seg_end = text.find("。", end)
    if seg_end < 0:
        seg_end = len(text)
    return text[seg_start:seg_end].strip()


def hook_scan(res):
    """观察级：检测文首 300 字是否疑似回顾式（--hook）。"""
    body = res["body"]
    head = body[:300]
    marks = [m for m in HOOK_REVIEW_MARKERS if m in head]
    if not marks:
        return None
    return ("[hook] 开篇疑似回顾式，命中回顾标记：" + "、".join(marks) +
            "\n      回溯写法耗前 300 字情绪，建议改冷开场/悬念倒叙/危机切入（见 开篇钩子设计.md）。若确为有意回溯可忽略。")


def timeline_scan(res):
    """观察级：按出现顺序导出时序副词句，人工核对先后是否自洽（--consist）。"""
    paras = res["paragraphs_list"]
    rows = []
    for pi, para in enumerate(paras):
        for adv in TIMELINE_ADVERBS:
            start = 0
            while True:
                idx = para.find(adv, start)
                if idx < 0:
                    break
                seg_s = para.rfind("。", 0, idx) + 1
                seg_e = para.find("。", idx + len(adv))
                if seg_e < 0:
                    seg_e = len(para)
                rows.append((pi + 1, adv, para[seg_s:seg_e].strip()))
                start = idx + len(adv)
    if not rows:
        return None
    lines = ["[consist] 时间线顺序核查（按出现顺序，人工核对先后是否自洽，尤其注意'先/后'能否对上）："]
    for pi, adv, sent in rows:
        lines.append(f"  §{pi:>2}｜{adv}：{sent[:40]}")
    return "\n".join(lines)


def digits_scan(res):
    """观察级：导出章节内所有数字（含中文数字）及上下文（--digits）。"""
    body = res["body"]
    pat = re.compile(r"\d+(?:\.\d+)?|" + CN_NUM_RE + "+")
    rows = []
    for m in pat.finditer(body):
        ctx = _sentence_around(body, m.start(), m.end(), m.group(0))
        rows.append((m.group(0), ctx))
    if not rows:
        return None
    lines = ["[digits] 章节内数字清单（人工核对金额/数量前后是否统一，含中文数字）："]
    for num, ctx in rows:
        lines.append(f"  {num:<6}｜{ctx[:45]}")
    return "\n".join(lines)


def facts_scan(res, ledger_path):
    """观察级：将正文与 facts.md 台账比对（--facts）。

    只处理含「正文写法」列的账目表（当前为「金额账目」），其余表（位置/时间/数量）
    无该列则跳过，避免误报。命中：值中的阿拉伯数字，或「正文写法」去空白子串匹配出现于正文。
    """
    if not ledger_path or not os.path.exists(ledger_path):
        return "[facts] 未提供台账路径或台账不存在，跳过（观察级，不影响门禁）。"
    with open(ledger_path, encoding="utf-8-sig") as f:
        ledger = f.read()
    body_plain = re.sub(r"\s+", "", res["body"])
    facts = []
    has_forms_col = False
    for line in ledger.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        flat = " ".join(cells)
        if "含义" in flat:                      # 表头行：按是否含「正文写法」决定是否比对
            has_forms_col = "正文写法" in flat
            continue
        if not has_forms_col:
            continue
        if not cells or not cells[0] or re.fullmatch(r"-+", cells[0]):
            continue                            # 分隔行
        if len(cells) < 3:
            continue
        facts.append((cells[0], cells[1], cells[2]))
    if not facts:
        return "[facts] 台账无可比对条目（未找到带「正文写法」列的账目表）。"
    lines = ["[facts] 台账基准 → 正文可能不符（观察级，人工判断）:"]
    any_hit = False
    for label, val, forms in facts:
        hit = False
        for n in re.findall(r"[0-9]+(?:\.[0-9]+)?", val):
            if n and n in body_plain:
                hit = True
                break
        if not hit and forms:
            for f in re.sub(r"[／/]", "/", forms).split("/"):
                f = re.sub(r"\s+", "", f)
                if f and f in body_plain:
                    hit = True
                    break
        if not hit:
            lines.append(f"  ✗ 「{label}」（值：{val}，正文写法：{forms}）在正文未找到")
            any_hit = True
    if not any_hit:
        return "[facts] 台账基准事实均能在正文中找到（一致性通过）。"
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="正文文件或目录")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--target", type=int, default=None, help="每章目标字数（正负15% 验收）")
    ap.add_argument("--strict", action="store_true", help="高频词三级门禁（写作完成定义）")
    ap.add_argument("--hook", action="store_true", help="观察开篇是否回顾式（观察级）")
    ap.add_argument("--consist", action="store_true", help="导出时间线副词顺序（观察级）")
    ap.add_argument("--digits", action="store_true", help="导出章节内数字清单（观察级）")
    ap.add_argument("--facts", metavar="台账路径", default=None, help="比对正文与 facts.md（观察级）")
    args = ap.parse_args()
    if not os.path.exists(args.path):
        print(f"路径不存在：{args.path}")
        sys.exit(1)

    res = analyze(_read_text(args.path))
    fail = False
    msgs = []
    strict_fail, strict_msgs = False, []

    # 字数门禁（正负15%）
    if args.target:
        lo, hi = int(args.target * 0.85), int(args.target * 1.15)
        ok = lo <= res["total_chars"] <= hi
        if not ok:
            fail = True
            msgs.append(f"[FAIL] 字数 {res['total_chars']} 不在 [{lo},{hi}]（目标 {args.target} 正负15%）｜距上限 {res['total_chars']-hi} / 距下限 {lo-res['total_chars']}")
        else:
            msgs.append(f"[PASS] 字数 {res['total_chars']} 在 [{lo},{hi}]（目标 {args.target} 正负15%）｜距上限 {hi-res['total_chars']} / 距下限 {res['total_chars']-lo}")

    # 高频词门禁
    if args.strict:
        strict_fail, strict_msgs = strict_scan(res)
        if strict_fail:
            fail = True

    if args.json:
        out = {k: v for k, v in res.items() if k not in ("body", "paragraphs_list")}
        out["wordcount_gate"] = msgs
        out["strict_gate"] = strict_msgs
        out["gate_pass"] = not fail
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return

    print("== 正文观测 ==")
    print(f"  字数：{res['total_chars']} | 段落：{res['paragraphs']}（均 {res['avg_para_chars']} 字/段）")
    print(f"  句数：{res['sentences']}（均 {res['avg_sentence_chars']} 字/句）| 短句占比(<=15字)：{res['short_sentence_ratio']:.1%}")
    print("  AI 高频词命中（仅观测，非禁令）：")
    if res["ai_lexicon_hits"]:
        for w, c in list(res["ai_lexicon_hits"].items())[:15]:
            print(f"    {w}: {c}")
    else:
        print("    （无）")

    # 观察级辅助检查（只提示，不纳入门禁）
    if args.hook or args.consist or args.digits or args.facts:
        print("== 观测辅助（观察级 · 仅供人工判断，不拦截） ==")
        if args.hook:
            r = hook_scan(res)
            print(r if r else "  [hook] 开篇未见回顾标记（PASS）")
        if args.consist:
            r = timeline_scan(res)
            if r:
                print(r)
        if args.digits:
            r = digits_scan(res)
            if r:
                print(r)
        if args.facts:
            print(facts_scan(res, args.facts))

    if args.target or args.strict:
        print("== 门禁（写作完成定义） ==")
        for m in msgs:
            print(m)
        if args.strict:
            print("  高频词门禁（三级频率制，1绿/2黄/>=3红）：")
            if strict_msgs:
                for m in strict_msgs:
                    print(m)
            else:
                print("    未命中（PASS）")

    print("结论: " + ("FAIL — 未达写作完成标准，改写后再过。" if fail else "PASS — 可进入阶段③自检。"))
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    main()