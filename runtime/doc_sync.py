#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_sync.py — 技能说明文档同步器
================================
解决"修改技能文件后说明文档（_README.md）容易过期"的问题。

约定：每个含 .md 文件或有子目录的目录，维护一个 `_README.md`：
  - 顶部"人工说明区"：由作者维护的语义描述（定位/用法/上下游关系），doc_sync 不触碰。
  - 底部"自动清单区"：由本脚本维护的文件清单（文件名/大小/首行标题/更新时间）。

用法：
  python runtime/doc_sync.py scan            # 列出全部目录的同步状态（缺 _README / 过期 / 正常）
  python runtime/doc_sync.py check           # 门禁：有缺失或过期则 exit 1（供 verify.py 集成）
  python runtime/doc_sync.py update          # 批量创建/刷新各目录 _README 的自动清单区
  python runtime/doc_sync.py update --root X # 指定技能根目录（默认=本文件上级）
"""
import os
import re
import sys
import io
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)  # runtime/ 的上级 = 技能根

MARK_START = "<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->"
MARK_END = "<!-- AUTO-LIST-END -->"
# deps = 离线 vendored 第三方依赖（jieba/pypinyin/pyyaml），非技能说明文档，跳过扫描
SKIP_DIRS = {".git", "__pycache__", ".workbuddy", "node_modules", "deps"}


def walk_dirs(root):
    """返回所有含 md 或有子目录的目录（相对路径列表，'.' 代表根）。"""
    result = []
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if ".git" in dp:
            continue
        rel = os.path.relpath(dp, root)
        has_md = any(f.endswith(".md") and not f.startswith("_") for f in files)
        has_sub = bool(dirs)
        if has_md or has_sub:
            result.append((rel, files, dirs))
    return result


def read(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


def write(p, text):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def first_heading(text):
    """取 md 第一个 # 或 ## 标题作用途，截断 34 字。"""
    m = re.search(r"^#{1,3}\s+(.+)$", text, re.M)
    if not m:
        return ""
    t = m.group(1).strip().replace("|", "／")
    return t[:34]


def human_size(n):
    return "%.1fK" % (n / 1024)


def gen_autolist(root, rel):
    """生成自动清单区文本（不含 MARK 标记）。"""
    dp = os.path.join(root, rel) if rel != "." else root
    entries = []
    files = sorted(f for f in os.listdir(dp)
                   if f.endswith(".md") and not f.startswith("_"))
    for f in files:
        p = os.path.join(dp, f)
        try:
            size = os.path.getsize(p)
            c = read(p)
            purpose = first_heading(c)
            mtime = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
        except Exception:
            size, purpose, mtime = 0, "", "-"
        entries.append((f, human_size(size), purpose, mtime))
    lines = ["## 文件清单（自动生成）", "", "| 文件 | 大小 | 用途（首行标题） | 更新 |",
             "|------|------|-------------------|------|"]
    for f, sz, pur, mt in entries:
        lines.append("| %s | %s | %s | %s |" % (f, sz, pur or "-", mt))
    subdirs = sorted(d for d in os.listdir(dp)
                     if os.path.isdir(os.path.join(dp, d)) and d not in SKIP_DIRS)
    if subdirs:
        lines.append("")
        lines.append("### 子目录")
        lines.append("")
        for d in subdirs:
            sub_readme = os.path.exists(os.path.join(dp, d, "_README.md"))
            lines.append("- `%s/` %s" % (d, "（有说明）" if sub_readme else "（缺说明，运行 doc_sync update 生成）"))
    return "\n".join(lines)


def split_autolist(text):
    """把 _README 拆成 (人工区, 自动区)。自动区可能不存在。"""
    if MARK_START in text and MARK_END in text:
        head = text.split(MARK_START)[0]
        return head, True
    return text, False


def status_of(root, rel, files):
    """返回 ('missing'|'ok'|'stale', 详情)。"""
    rp = os.path.join(root, rel, "_README.md") if rel != "." else os.path.join(root, "_README.md")
    if not os.path.exists(rp):
        return "missing", ""
    text = read(rp)
    # 自动区是否存在且与最新一致
    autolist = gen_autolist(root, rel)
    if MARK_START in text and MARK_END in text:
        cur = text.split(MARK_START)[1].split(MARK_END)[0].strip()
        if cur == autolist.strip():
            return "ok", ""
        return "stale", "自动清单与目录不一致"
    # 有 _README 但无自动区
    return "stale", "缺少自动清单区（运行 doc_sync update）"


def do_scan_or_check(root, check=False):
    bad = 0
    for rel, files, dirs in walk_dirs(root):
        st, msg = status_of(root, rel, files)
        if st == "ok":
            continue
        bad += 1
        label = "[缺说明]" if st == "missing" else "[已过期]"
        print("%s %s  (%s)" % (label, rel if rel != "." else "[根]", msg))
    if not bad:
        print("全部目录说明文档已同步 ✓")
    return 1 if (bad and check) else 0


def do_update(root):
    made, refreshed = 0, 0
    for rel, files, dirs in walk_dirs(root):
        rp = os.path.join(root, rel, "_README.md") if rel != "." else os.path.join(root, "_README.md")
        autolist = gen_autolist(root, rel)
        block = "\n\n%s\n%s\n%s\n" % (MARK_START, autolist, MARK_END)
        if os.path.exists(rp):
            text = read(rp)
            if MARK_START in text and MARK_END in text:
                head = text.split(MARK_START)[0].rstrip()
                new_text = head + block
            else:
                new_text = text.rstrip() + block
            if new_text != text:
                write(rp, new_text)
                refreshed += 1
                print("刷新: %s/_README.md" % rel)
        else:
            name = os.path.basename(rel) if rel != "." else "技能根"
            head = "# %s 说明\n\n> ⚠️ 本说明由 doc_sync.py 自动生成。请在下方补充本目录的语义说明（定位/用法/上下游），自动文件清单见文末。\n\n<!-- 人工说明区（doc_sync 保留此区，不会覆盖） -->\n（待补充）" % name
            write(rp, head + block)
            made += 1
            print("生成: %s/_README.md" % rel)
    print("完成：新建 %d 个，刷新 %d 个" % (made, refreshed))


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "scan"
    root = DEFAULT_ROOT
    if "--root" in args:
        i = args.index("--root")
        root = os.path.abspath(args[i + 1])
    if cmd == "update":
        do_update(root)
    elif cmd == "check":
        sys.exit(do_scan_or_check(root, check=True))
    else:
        do_scan_or_check(root, check=False)


if __name__ == "__main__":
    main()
