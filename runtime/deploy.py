#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deploy.py — Novel Engine 运行镜像同步（v2.0 闸 3）
==================================================
治"改了源仓，运行镜像还是旧版"的问题。

背景（2026-10-15 实测）：
  D 盘源仓 514 文件 / v1.9.1.3
  C 盘镜像 1185 文件 / v1.4.0     ← 整目录手工复制的陈旧脏快照

根因：手工复制会把 _skill_analysis/、测试基线、__pycache__、.git 一起复制过去，
且只覆盖不清理，越攒越多。本脚本复用 package.py 的排除规则，先备份再全量重建，
同步后校验版本号一致。

用法：
  python runtime/deploy.py                 # 演练：只打印将要同步/排除的清单，不写盘
  python runtime/deploy.py --apply         # 真执行：备份旧镜像 → 全量重建 → 校验版本
  python runtime/deploy.py --target <路径> # 指定镜像目录（默认见下）
  python runtime/deploy.py --no-backup     # 跳过备份（不推荐；仅当确认镜像无价值时）

安全设计：
  - 默认 dry-run，必须显式 --apply 才动盘
  - --apply 时先把旧镜像**重命名**为 <目录>.bak-<时间戳>（不删除，可整体回退）
  - 同步后比对源/镜像的 SKILL.md 版本号，不一致则报错退出
"""
import argparse
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import package as pkg  # noqa: E402  复用排除规则（package.py 有 __main__ guard，导入安全）

DEFAULT_TARGET = r'C:\Users\jy322\.workbuddy\skills\novel-engine'


def skill_version(root):
    txt = open(os.path.join(root, 'SKILL.md'), encoding='utf-8').read()
    m = re.search(r'^version:\s*([0-9][0-9A-Za-z.\-]*)', txt, re.M)
    return m.group(1).strip() if m else 'unknown'


def count_files(root):
    n = 0
    for _, _, files in os.walk(root):
        n += len(files)
    return n


def main():
    ap = argparse.ArgumentParser(description='Novel Engine 运行镜像同步')
    ap.add_argument('--apply', action='store_true', help='真执行（默认演练）')
    ap.add_argument('--target', default=DEFAULT_TARGET, help='镜像目录')
    ap.add_argument('--no-backup', action='store_true', help='跳过旧镜像备份')
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kept, skipped = pkg.collect(root)
    src_ver = skill_version(root)
    target = args.target

    print('源仓：%s（v%s，共 %d 文件，本次同步 %d）' % (root, src_ver, count_files(root), len(kept)))
    print('镜像：%s' % target)
    if os.path.isdir(target):
        print('现有镜像：%d 文件，v%s' % (count_files(target), skill_version(target)))
    else:
        print('现有镜像：不存在（将新建）')
    print('排除 %d 个开发期文件（_skill_analysis/ 测试基线/ _selftest/ dist/ .git/ __pycache__ 等）' % len(skipped))

    if not args.apply:
        print('\n[演练模式] 未写盘。确认无误后加 --apply 执行。')
        return 0

    # 1) 备份旧镜像（重命名而非删除，可整体回退）
    if os.path.isdir(target) and not args.no_backup:
        bak = '%s.bak-%s' % (target.rstrip('\\/'), datetime.now().strftime('%Y%m%d-%H%M%S'))
        try:
            os.rename(target, bak)
            print('\n旧镜像已备份 → %s' % bak)
            print('（确认新镜像可用后，可自行删除该备份目录）')
        except OSError as e:
            print('\n[失败] 旧镜像无法重命名：%s' % e)
            print('可能正被占用。关闭占用进程后重试，或先手动移走该目录。')
            return 1

    # 2) 全量重建
    os.makedirs(target, exist_ok=True)
    copied = 0
    for rel in kept:
        src = os.path.join(root, rel)
        dst = os.path.join(target, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    # 3) 校验版本一致
    tgt_ver = skill_version(target)
    tgt_n = count_files(target)
    print('\n同步完成：复制 %d 个文件 → 镜像共 %d 文件' % (copied, tgt_n))
    if tgt_ver != src_ver:
        print('[失败] 版本不一致：源 %s vs 镜像 %s' % (src_ver, tgt_ver))
        return 1
    print('版本校验通过：源 v%s = 镜像 v%s' % (src_ver, tgt_ver))
    print('\n提示：子技能/agent 注册如需刷新，新开一个会话生效。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
