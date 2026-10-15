#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
package.py — Novel Engine 发行打包（v1.9.1.2 新增）
==================================================
把技能目录打成发行 ZIP，自动排除开发期文件。治"README 整目录复制"把
_skill_analysis/（内部缺陷登记）、测试基线、.git 一起发出去的问题。

用法：
  python runtime/package.py                 # 输出 dist/novel-engine-v<版本>-<日期>.zip
  python runtime/package.py --out <路径>    # 指定输出
  python runtime/package.py --list          # 只打印将被打包/排除的清单，不写盘

排除规则（与 README 安装节、缺陷登记表 D-19"不打包"假设同口径）：
  目录：.git/  .workbuddy/  __pycache__/  dist/  _skill_analysis/  测试_基线*/  story/index/
  文件：*.pyc  *.bundle  pr-body.md  审查报告*.md
"""
import argparse, os, re, sys, zipfile
from datetime import date

EXCLUDE_DIRS = {'.git', '.workbuddy', '__pycache__', 'dist'}
EXCLUDE_DIR_PATTERNS = [re.compile(r'^_skill_analysis'), re.compile(r'^测试_基线'),
                        re.compile(r'^_selftest')]
EXCLUDE_DIR_PATHS = ('story/index',)
EXCLUDE_FILE_PATTERNS = [
    re.compile(r'^pr-body\.md$'),
    re.compile(r'^审查报告.*\.md$'),
    re.compile(r'.*\.pyc$'),
    re.compile(r'.*\.bundle$'),
]


def excluded_dir(rel_dir):
    """rel_dir：相对技能根的目录路径（正斜杠归一）。"""
    rel_norm = rel_dir.replace('\\', '/').rstrip('/')
    parts = rel_norm.split('/')
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    for pd in EXCLUDE_DIR_PATHS:
        if rel_norm == pd or rel_norm.startswith(pd + '/'):
            return True
    return any(pat.match(p) for pat in EXCLUDE_DIR_PATTERNS for p in parts)


def excluded_file(fn):
    return any(pat.match(fn) for pat in EXCLUDE_FILE_PATTERNS)


def skill_version(root):
    txt = open(os.path.join(root, 'SKILL.md'), encoding='utf-8').read()
    m = re.search(r'^version:\s*([0-9][0-9A-Za-z.\-]*)', txt, re.M)
    return m.group(1).strip() if m else 'unknown'


def collect(root):
    kept, skipped = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel == '.':
            rel = ''
        # 剪枝：命中的子目录不再深入
        dirnames[:] = [d for d in dirnames
                       if not excluded_dir(os.path.join(rel, d) if rel else d)]
        for fn in sorted(filenames):
            rel_path = os.path.join(rel, fn) if rel else fn
            if excluded_file(fn):
                skipped.append(rel_path)
            else:
                kept.append(rel_path)
    return sorted(kept), sorted(skipped)


def main():
    ap = argparse.ArgumentParser(description='Novel Engine 发行打包')
    ap.add_argument('--out', default='', help='输出 ZIP 路径（默认 dist/ 下按版本+日期命名）')
    ap.add_argument('--list', action='store_true', help='只打印清单，不写盘')
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kept, skipped = collect(root)
    ver = skill_version(root)

    print('将打包 %d 个文件；排除 %d 个开发期文件' % (len(kept), len(skipped)))
    if args.list:
        for p in skipped:
            print('  [排除] %s' % p)
        return 0
    if skipped:
        print('（排除明细可用 --list 查看）')

    out = args.out or os.path.join(root, 'dist', 'novel-engine-v%s-%s.zip'
                                   % (ver, date.today().strftime('%Y%m%d')))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel in kept:
            zf.write(os.path.join(root, rel), os.path.join('novel-engine', rel))
    size = os.path.getsize(out)
    print('已生成：%s（%.1f KB，%d 文件）' % (out, size / 1024.0, len(kept)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
