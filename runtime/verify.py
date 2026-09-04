#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 流程门禁（verify.py）
=====================================
把"自动完成"从 Agent 自觉升级为程序强制。关键动作（初始化 / 落库 / 总览生成）
之后必须运行本脚本：PASS → 允许继续下一步；FAIL → 流程禁止继续，先修复再走。

用法：
  python runtime/verify.py --root <项目根> [--scope init|narrative|all]

检查项：
  [结构]   项目目录骨架（真相/元数据/正文/叙事总览…）
  [MOC]    根叙事总览.md 存在（init 即强制，防初始化漏建）
  [防污染] 真相文件禁止双链（机器可读）
  [骨架]   叙事总览 6 子页 + 根 MOC
  [双链]   展示层链接目标可解析（未写章节悬空=警告非失败）
  [导航]   快速导航双链必须精确文件名（防语义名 [[角色总览]] 悬空）
  [角色卡] 角色总览双链必须已有角色卡文件（防未出场角色转双链）
  [命名]   章节链接必须 4 位章号（第000X章）
  [配置]   novel-config.json 合法性（target_word_count/命名模板）
  [落点]   相邻3章落点类型（开/合/转）去重（防收尾套路化）

退出码：0=全部通过  1=存在失败项
"""
import argparse, json, os, re, sys

BANNED = '[['  # 真相文件禁用字符


def walk_md(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith('.md'):
                yield os.path.join(dirpath, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--scope', default='all', choices=['init', 'narrative', 'all'])
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f'[错误] 项目根不存在: {root}')
        sys.exit(1)

    results = []

    def check(name, ok, detail=''):
        results.append((name, ok, detail))

    # 1 目录结构
    if args.scope in ('init', 'all'):
        dirs = ['故事/真相', '故事/元数据', '故事/日志', '故事/索引',
                '正文', '大纲', '设定', '配置/身份', '素材池', '叙事总览']
        missing = [d for d in dirs if not os.path.isdir(os.path.join(root, d))]
        check('目录结构', not missing, '缺失: ' + ','.join(missing) if missing else '')
        # 1b 根 MOC 存在性（init 也强制：曾因初始化漏建，仅 narrative/all 才报 → 改为 init 即查）
        moc_ok = os.path.isfile(os.path.join(root, '叙事总览.md'))
        check('根MOC存在', moc_ok, '缺 叙事总览.md（根MOC入口）' if not moc_ok else '')

    # 2 数据层防污染（机器可读：truth + meta 均禁双链）
    polluted = []
    for data_dir in ['故事/真相', '故事/元数据']:
        d = os.path.join(root, data_dir)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith('.md'):
                    p = os.path.join(d, f)
                    if BANNED in open(p, encoding='utf-8').read():
                        polluted.append(os.path.join(data_dir, f))
    check('数据层防污染', not polluted, '含双链: ' + ','.join(polluted) if polluted else '')

    # 3-5 叙事总览层
    if args.scope in ('narrative', 'all'):
        nar = os.path.join(root, '叙事总览')
        skeletons = ['00_作品总览', '01_角色总览', '02_世界观总览',
                     '03_伏笔追踪总览', '04_章节地图', '05_关系网']
        miss = [s for s in skeletons if not os.path.isfile(os.path.join(nar, s + '.md'))]
        moc_ok = os.path.isfile(os.path.join(root, '叙事总览.md'))
        detail = ''
        if miss:
            detail += '缺子页: ' + ','.join(miss)
        if not moc_ok:
            detail += ('; ' if detail else '') + '缺根MOC'
        check('总览骨架', not miss and moc_ok, detail)

        # 4 双链可解析性（Obsidian 按文件名全库匹配，需在整个项目树中找目标）
        links = {}
        for p in walk_md(nar):
            for m in re.finditer(r'\[\[([^\]|#]+)', open(p, encoding='utf-8').read()):
                name = m.group(1).strip()
                if name:
                    links.setdefault(name, []).append(os.path.relpath(p, root))
        # 全库文件名集合（不含扩展名），Obsidian 同名唯一解析
        all_basenames = set()
        for p in walk_md(root):
            all_basenames.add(os.path.splitext(os.path.basename(p))[0])
        missing_links = []
        for name in sorted(links):
            if name not in all_basenames:
                missing_links.append(name)
        warns = [n for n in missing_links if re.match(r'^第\d{4}章$', n)]   # 未写章节悬空
        hard = [n for n in missing_links if n not in warns]
        detail = ''
        if hard:
            detail = '缺失目标: ' + ','.join(hard)
        elif warns:
            detail = '仅未写章节悬空(允许): ' + ','.join(warns)
        check('双链可解析', not hard, detail)

        # 4b 导航双链精确文件名（防 [[角色总览]] 语义名 vs [[01_角色总览]] 实际文件名不一致）
        nav_bad = []
        nav_file = os.path.join(nar, '00_作品总览.md')
        if os.path.isfile(nav_file):
            nav_txt = open(nav_file, encoding='utf-8').read()
            if '## 快速导航' in nav_txt:
                nav_sec = nav_txt.split('## 快速导航', 1)[1]
                for m in re.finditer(r'\[\[([^\]|#]+)', nav_sec):
                    nm = m.group(1).strip()
                    if nm and not os.path.isfile(os.path.join(nar, nm + '.md')):
                        nav_bad.append(nm)
        check('导航双链精确', not nav_bad, '语义名缺失: ' + ','.join(nav_bad) if nav_bad else '')

        # 4c 角色卡可解析（防未出场角色在 01_角色总览 写双链导致悬空）
        card_bad = []
        role_file = os.path.join(nar, '01_角色总览.md')
        card_dir = os.path.join(nar, '角色卡')
        if os.path.isfile(role_file):
            role_txt = open(role_file, encoding='utf-8').read()
            for m in re.finditer(r'\[\[([^\]|#]+)', role_txt):
                nm = m.group(1).strip()
                if not nm:
                    continue
                if re.match(r'^0\d_', nm):  # 子页导航 → 指向叙事总览目录
                    if not os.path.isfile(os.path.join(nar, nm + '.md')):
                        card_bad.append(nm + '(子页缺)')
                else:  # 角色名 → 必须已有角色卡（落库联动生成后才可双链）
                    if not os.path.isfile(os.path.join(card_dir, nm + '.md')):
                        card_bad.append(nm + '(角色卡缺)')
        check('角色卡可解析', not card_bad, '缺失: ' + ','.join(card_bad) if card_bad else '')

        # 5 章节链接命名规范（4位章号）
        bad_chap = []
        for p in walk_md(nar):
            for m in re.finditer(r'\[\[(第\d+章[^\]|#]*)', open(p, encoding='utf-8').read()):
                t = m.group(1).strip()
                if not re.match(r'^第\d{4}章', t):
                    bad_chap.append(t)
        check('章节链接4位章号', not bad_chap, '非4位: ' + ','.join(bad_chap) if bad_chap else '')

    # 6 config 合法性
    cfg_path = os.path.join(root, 'novel-config.json')
    if os.path.isfile(cfg_path):
        try:
            cfg = json.load(open(cfg_path, encoding='utf-8-sig'))  # 容忍 Windows BOM
            ok = (isinstance(cfg.get('target_word_count'), int)
                  and cfg.get('target_word_count') > 0
                  and 'body_filename_template' in cfg)
            check('config合法性', ok, '缺 target_word_count 或 body_filename_template' if not ok else '')
        except Exception as e:
            check('config合法性', False, f'JSON 解析失败: {e}')
    else:
        check('config合法性', False, 'novel-config.json 不存在')

    # 7 落点类型去重（防连载收尾套路化：相邻3章同类落点 FAIL；落库后跑 --scope all 生效）
    landing_bad = []
    if args.scope in ('all',):
        outline_dir = os.path.join(root, '大纲')
        chap_seq = []
        if os.path.isdir(outline_dir):
            for fn in sorted(os.listdir(outline_dir)):
                m = re.match(r'^细纲_第(\d{4})章\.md$', fn)
                if m:
                    txt = open(os.path.join(outline_dir, fn), encoding='utf-8').read()
                    lm = re.search(r'落点类型[:：]\s*(开|合|转)', txt)
                    chap_seq.append((m.group(1), lm.group(1) if lm else None))
        for i in range(len(chap_seq) - 2):
            a, b, c = chap_seq[i][1], chap_seq[i + 1][1], chap_seq[i + 2][1]
            if a and b and c and a == b == c:
                landing_bad.append(f"{chap_seq[i][0]}-{chap_seq[i + 2][0]}连续3章同类落点({a})")
        check('落点类型去重', not landing_bad, '; '.join(landing_bad) if landing_bad else '')
    # 汇总
    fails = [r for r in results if not r[1]]
    print(f'=== Novel Engine 流程门禁 ({args.scope}) ===')
    for name, ok, detail in results:
        mark = 'PASS' if ok else 'FAIL'
        print(f'  [{mark}] {name}' + (f'  — {detail}' if detail else ''))
    print(f'--- 通过 {len(results) - len(fails)}/{len(results)} ---')
    if fails:
        print('结论: FAIL — 流程禁止继续，修复后再跑。')
        sys.exit(1)
    print('结论: PASS — 可继续下一步。')
    sys.exit(0)


if __name__ == '__main__':
    main()
