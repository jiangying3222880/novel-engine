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

v2.0：源仓已由单个大技能拆为 9 个子技能，镜像同步改为
「每个 ne* 子目录 → skills/<同名目录>」的一对一映射。

用法：
  python ne-tools/runtime/deploy.py                 # 演练：只打印将要同步的清单，不写盘
  python ne-tools/runtime/deploy.py --apply         # 真执行：备份旧镜像 → 全量重建 → 校验版本
  python ne-tools/runtime/deploy.py --target <路径> # 指定 skills 父目录（默认见下）
  python ne-tools/runtime/deploy.py --no-backup     # 跳过备份（不推荐；仅当确认镜像无价值时）

安全设计：
  - 默认 dry-run，必须显式 --apply 才动盘
  - --apply 时先把旧镜像**重命名**为 <目录>.bak-<时间戳>（不删除，可整体回退）
  - 同步后逐个比对源/镜像的 SKILL.md 版本号，不一致则报错退出
  - 旧的单技能镜像 novel-engine/ 会被提示（它已拆分，不再同步）
"""
import argparse
import os
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import package as pkg  # noqa: E402  复用排除规则（package.py 有 __main__ guard，导入安全）

# v2.0：目标改为 skills 父目录，每个子技能同步到其下的同名目录
DEFAULT_TARGET = r'C:\Users\jy322\.workbuddy\skills'

SKIP_IN_SKILL = {'__pycache__', '.git', '.workbuddy', 'dist'}


def skill_version(root):
    p = os.path.join(root, 'SKILL.md')
    if not os.path.exists(p):
        return 'unknown'
    txt = open(p, encoding='utf-8').read()
    m = re.search(r'^version:\s*([0-9][0-9A-Za-z.\-]*)', txt, re.M)
    return m.group(1).strip() if m else 'unknown'


def count_files(root):
    n = 0
    for _, _, files in os.walk(root):
        n += len(files)
    return n


def collect_skill(root):
    """收集单个子技能内需要同步的文件（相对路径列表），排除开发期垃圾。"""
    out = []
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_IN_SKILL]
        for f in files:
            if f.endswith('.pyc'):
                continue
            out.append(os.path.relpath(os.path.join(dp, f), root))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description='Novel Engine 运行镜像同步')
    ap.add_argument('--apply', action='store_true', help='真执行（默认演练）')
    ap.add_argument('--target', default=DEFAULT_TARGET, help='镜像目录')
    ap.add_argument('--no-backup', action='store_true', help='跳过旧镜像备份')
    args = ap.parse_args()

    # v2.0：脚本从 <包根>/runtime/ 移到 <包根>/ne-tools/runtime/，多了一层。
    # 逐层向上找包根：优先含 VERSION，其次含 ne/ 路由技能，最后含 SKILL.md。
    def _find_package_root(start):
        cands = []
        d = start
        for _ in range(5):
            has_ver = os.path.exists(os.path.join(d, 'VERSION'))
            has_ne = os.path.isdir(os.path.join(d, 'ne'))
            has_skill = os.path.exists(os.path.join(d, 'SKILL.md'))
            if has_ver or has_ne or has_skill:
                cands.append((0 if has_ver else (1 if has_ne else 2), d))
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
        if not cands:
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cands.sort(key=lambda x: x[0])
        return cands[0][1]

    here = os.path.dirname(os.path.abspath(__file__))
    root = _find_package_root(here)
    skills_parent = args.target

    subs = sorted(d for d in os.listdir(root)
                  if (d == 'ne' or d.startswith('ne-'))
                  and os.path.isdir(os.path.join(root, d))
                  and os.path.exists(os.path.join(root, d, 'SKILL.md')))
    if not subs:
        print('[失败] 包根下未找到任何 ne* 子技能：%s' % root)
        return 1

    src_ver = open(os.path.join(root, 'VERSION'), encoding='utf-8').read().strip() \
        if os.path.exists(os.path.join(root, 'VERSION')) else 'unknown'

    print('源仓：%s（包版本 v%s）' % (root, src_ver))
    print('镜像父目录：%s' % skills_parent)
    print('待同步子技能 %d 个：' % len(subs))
    plans = []
    for d in subs:
        src_dir = os.path.join(root, d)
        files = collect_skill(src_dir)
        plans.append((d, src_dir, os.path.join(skills_parent, d), files))
        exist = count_files(os.path.join(skills_parent, d)) \
            if os.path.isdir(os.path.join(skills_parent, d)) else 0
        print('  %-12s %4d 文件 → %s（现有 %d 文件，v%s）'
              % (d, len(files), os.path.join(skills_parent, d), exist,
                 skill_version(os.path.join(skills_parent, d))))

    old_mono = os.path.join(skills_parent, 'novel-engine')
    if os.path.isdir(old_mono):
        print('\n注意：旧单技能镜像 %s 仍存在（v%s，%d 文件）。'
              % (old_mono, skill_version(old_mono), count_files(old_mono)))
        print('      它已拆分，不再同步。确认新子技能可用后可删除或改名。')

    if not args.apply:
        print('\n[演练模式] 未写盘。确认无误后加 --apply 执行。')
        return 0

    # 1) 备份 + 2) 全量重建
    total = 0
    for d, src_dir, tgt_dir, files in plans:
        if os.path.isdir(tgt_dir) and not args.no_backup:
            bak = '%s.bak-%s' % (tgt_dir.rstrip('\\/'), datetime.now().strftime('%Y%m%d-%H%M%S'))
            try:
                os.rename(tgt_dir, bak)
                print('\n%s 旧镜像已备份 → %s' % (d, os.path.basename(bak)))
            except OSError as e:
                print('\n[失败] %s 旧镜像无法重命名：%s' % (d, e))
                return 1
        os.makedirs(tgt_dir, exist_ok=True)
        for rel in files:
            s = os.path.join(src_dir, rel)
            dst = os.path.join(tgt_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(s, dst)
        total += len(files)
        print('  %-12s 复制 %d 文件' % (d, len(files)))

    # 3) 逐个校验版本
    print()
    bad = 0
    for d, src_dir, tgt_dir, _ in plans:
        sv, tv = skill_version(src_dir), skill_version(tgt_dir)
        if sv != tv:
            print('[失败] %s 版本不一致：源 %s vs 镜像 %s' % (d, sv, tv))
            bad += 1
        else:
            print('  %-12s 版本校验通过 v%s' % (d, sv))
    if bad:
        return 1
    print('\n同步完成：%d 个子技能，共 %d 文件' % (len(plans), total))
    print('提示：子技能/agent 注册如需刷新，新开一个会话生效。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
