#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 流程门禁（verify.py）
=====================================
把"自动完成"从 Agent 自觉升级为程序强制。关键动作（初始化 / 落库 / 总览生成）
之后必须运行本脚本：PASS → 允许继续下一步；FAIL → 流程禁止继续，先修复再走。

用法：
  python runtime/verify.py --root <项目根> [--scope init|narrative|evidence|execution|all]

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
  [落点]   相邻3章落点类型（开/合/转）去重（防收尾套路化；v1.9 细纲路径 大纲/ → 故事/元数据/，兼容旧路径）
  [细纲门] S1 细纲硬性结构检查（v1.9 · scope=outline：任务字数非空/冲突链四节点/声线标注来源/角色状态最小摘要）
  [证据]   evidence_ids 格式校验 + 正文引用存在性（evidence 范围；v1.9 载体含 检验报告_*.md）
  [执行]   config.modules 字段合法性 + 最新流程日志含 execution_mode 声明行（execution 范围，v1.8）
  [残留]   正文首段工具残留检查（v1.9 · F-09：续写指令/工具声明/元注释漏入正文）

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
    ap.add_argument('--scope', default='all', choices=['init', 'narrative', 'all', 'evidence', 'execution', 'outline'])
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
        meta_dir_2 = os.path.join(root, '故事', '元数据')
        chap_seq = []
        # v1.9 产物链：细纲落盘位置从 大纲/ 迁移到 故事/元数据/（兼容旧路径）
        for base_dir in (meta_dir_2, outline_dir):
            if not os.path.isdir(base_dir):
                continue
            for fn in sorted(os.listdir(base_dir)):
                m = re.match(r'^细纲_第(\d{4})章\.md$', fn)
                if m:
                    txt = open(os.path.join(base_dir, fn), encoding='utf-8').read()
                    lm = re.search(r'落点类型[:：]\s*(开|合|转)', txt)
                    chap_seq.append((m.group(1), lm.group(1) if lm else None))
        for i in range(len(chap_seq) - 2):
            a, b, c = chap_seq[i][1], chap_seq[i + 1][1], chap_seq[i + 2][1]
            if a and b and c and a == b == c:
                landing_bad.append(f"{chap_seq[i][0]}-{chap_seq[i + 2][0]}连续3章同类落点({a})")
        check('落点类型去重', not landing_bad, '; '.join(landing_bad) if landing_bad else '')

    # 7b 细纲门硬性结构检查（v1.9 · scope=outline 或 scope=all）
    # 细纲门第一道 = 程序可校验项（非语义判断）；软性删节推理由 S3 检验 Agent 做，程序不判
    if args.scope in ('outline', 'all'):
        meta_dir_2 = os.path.join(root, '故事', '元数据')
        outline_gate_bad = []
        if os.path.isdir(meta_dir_2):
            for fn in sorted(os.listdir(meta_dir_2)):
                m = re.match(r'^细纲_第(\d{4})章\.md$', fn)
                if not m:
                    continue
                txt = open(os.path.join(meta_dir_2, fn), encoding='utf-8').read()
                # 3.1 硬性结构检查 4 项
                # ① 任务字数（每节数字非空）
                has_task_words = bool(re.search(r'任务字数[:：]?\s*\d', txt))
                # ② 冲突链四节点（想要/阻拦/弄砸/代价）
                conflict_kws = ['想要', '阻拦', '弄砸', '代价']
                has_conflict = all(kw in txt for kw in conflict_kws)
                # ③ 声线要求标注来源（characters.md# 透传）
                has_voice_src = bool(re.search(r'来源[:：]?\s*(characters|角色卡|设定)', txt))
                # ④ 角色状态最小摘要存在
                has_state_summary = bool(re.search(r'角色状态最小摘要', txt))
                missing = []
                if not has_task_words:
                    missing.append('任务字数缺数字')
                if not has_conflict:
                    missing.append('冲突链四节点不完整')
                if not has_voice_src:
                    missing.append('声线未标注来源')
                if not has_state_summary:
                    missing.append('角色状态最小摘要缺失')
                if missing:
                    outline_gate_bad.append(f'{fn}: ' + ','.join(missing))
        check('细纲门硬性结构', not outline_gate_bad,
              '; '.join(outline_gate_bad) if outline_gate_bad else '')

    # 8 evidence_ids 校验（scope=evidence 或 scope=all）
    if args.scope in ('evidence', 'all'):
        meta_dir = os.path.join(root, '故事/元数据')
        body_dir = os.path.join(root, '正文')
        if os.path.isdir(meta_dir):
            import glob as _glob
            # v1.9：evidence 载体从 chapter_*.md 扩展为 chapter_*.md + 检验报告_*.md
            meta_files = (sorted(_glob.glob(os.path.join(meta_dir, 'chapter_*.md')))
                          + sorted(_glob.glob(os.path.join(meta_dir, '检验报告_*.md'))))
            evidence_issues = []
            for mf_path in meta_files:
                mf_name = os.path.basename(mf_path)
                mf_txt = open(mf_path, encoding='utf-8').read()

                # 提取 review_status
                rs_m = re.search(r'review_status:\s*([^\s]+)', mf_txt)
                review_status = rs_m.group(1).strip() if rs_m else ''

                # 提取 chapter 号用于找正文文件
                ch_m = re.search(r'chapter[_\s]*id[:：]\s*[^\d]*(\d{1,4})', mf_txt, re.IGNORECASE)
                if not ch_m:
                    continue
                ch_num = ch_m.group(1).zfill(4)

                # 提取正文文件路径（从 chapter_files 或实际扫描）
                body_files = []
                if os.path.isdir(body_dir):
                    body_files = _glob.glob(os.path.join(body_dir, f'第{ch_num}章 *.md'))

                # 读取正文内容（用于 excerpt 存在性校验）
                body_text = ''
                if body_files:
                    for bf in body_files:
                        body_text += open(bf, encoding='utf-8').read()

                # 如果 review_status 非空（说明跑了自检），必须有 evidence_ids
                if review_status:
                    if 'evidence_ids' not in mf_txt:
                        evidence_issues.append(f'{mf_name}: review_status={review_status} 但无 evidence_ids')
                        continue

                    # 提取 evidence_ids 块
                    ids_m = re.search(r'evidence_ids:\s*\n((?:\s+- .+\n)*)', mf_txt)
                    if not ids_m:
                        evidence_issues.append(f'{mf_name}: evidence_ids 存在但格式错误（无条目）')
                        continue

                    ids_block = ids_m.group(1)
                    entries = re.findall(r'^\s+-\s+source:\s*(.+?)\s+excerpt:\s*(.+?)\s*$',
                                          ids_block, re.MULTILINE)
                    if not entries:
                        evidence_issues.append(f'{mf_name}: evidence_ids 无有效条目（缺 source/excerpt 字段）')
                        continue

                    # 逐条检查 source 和 excerpt 格式
                    for entry_src, entry_excerpt in entries:
                        src = entry_src.strip()
                        excerpt = entry_excerpt.strip()
                        if not src:
                            evidence_issues.append(f'{mf_name}: evidence_ids 条目缺少 source 字段')
                        if not excerpt:
                            evidence_issues.append(f'{mf_name}: evidence_ids 条目缺少 excerpt 字段')
                        # excerpt 至少 5 字符（防空引用）
                        if excerpt and len(excerpt) < 5:
                            evidence_issues.append(f'{mf_name}: evidence_ids excerpt 过短（<5字）：{excerpt[:20]}')
                        # 如果正文存在，校验 excerpt 是否在正文中（允许模糊匹配）
                        if body_text and excerpt:
                            # 用截取前30字做模糊匹配（避免特殊字符差异）
                            match_key = excerpt[:30] if len(excerpt) >= 30 else excerpt
                            if match_key not in body_text:
                                # 再试截取前15字
                                short_key = excerpt[:15]
                                if short_key not in body_text:
                                    evidence_issues.append(
                                        f'{mf_name}: excerpt 未在正文中找到（source={src}）：{excerpt[:40]}')

            if evidence_issues:
                check('evidence_ids校验', False, '; '.join(evidence_issues))
            else:
                # 如果没有任何元数据文件含 evidence_ids 也算通过（有写才算查）
                checked = len(meta_files)
                check('evidence_ids校验', True,
                      f'已检查 {checked} 个元数据文件，无问题' if checked > 0
                      else '无元数据文件，跳过')

    # 9 执行模式与模块配置校验（v1.8 · scope=execution 或 scope=all）
    if args.scope in ('execution', 'all'):
        # 9a config.modules 字段存在且合法（模块 SSOT）
        cfg_path = os.path.join(root, 'novel-config.json')
        mod_ok, mod_detail = True, ''
        if not os.path.isfile(cfg_path):
            mod_ok, mod_detail = False, '缺 novel-config.json'
        else:
            try:
                cfg_data = json.load(open(cfg_path, encoding='utf-8'))
                mods = cfg_data.get('modules')
                if not isinstance(mods, dict):
                    mod_ok, mod_detail = False, 'modules 字段缺失或非对象'
                else:
                    need_keys = ['short_story', 'chat_outsource', 'pool_teardown',
                                 'obsidian_overview', 'zvec']
                    missing = [k for k in need_keys if k not in mods]
                    if missing:
                        mod_ok, mod_detail = False, 'modules 缺键: ' + ','.join(missing)
                    else:
                        bad = [k for k, v in mods.items() if not isinstance(v, bool)]
                        if bad:
                            mod_ok, mod_detail = False, 'modules 值非布尔: ' + ','.join(bad)
            except Exception as e:
                mod_ok, mod_detail = False, f'config 解析失败: {e}'
        check('模块配置(modules)', mod_ok, mod_detail)

        # 9b 最新流程日志含 execution_mode 声明行（降级必须留痕）
        log_dir = os.path.join(root, '故事', '日志')
        em_ok, em_detail = True, ''
        if not os.path.isdir(log_dir):
            em_ok, em_detail = False, '缺 故事/日志/ 目录'
        else:
            logs = sorted([f for f in os.listdir(log_dir) if f.endswith('.md')])
            if not logs:
                em_ok, em_detail = False, '故事/日志/ 为空（无流程日志）'
            else:
                latest_log = logs[-1]
                log_txt = open(os.path.join(log_dir, latest_log), encoding='utf-8').read()
                if 'execution_mode' not in log_txt:
                    em_ok, em_detail = False, f'最新日志({latest_log})缺 execution_mode 声明行（降级未留痕）'
        check('执行模式声明(execution_mode)', em_ok, em_detail)

    # 10 正文工具残留检查（v1.9 · F-09：AI 工具痕迹漏入正文）
    # 番茄实测案例：高潮点后新章开头整行"按照您的要求，对xx进行续写"——读者直接弃书。
    # 检查正文第一段是否以工具残留开头（续写指令/工具声明/元注释）。
    if args.scope in ('all', 'execution'):
        body_dir = os.path.join(root, '正文')
        residue_bad = []
        if os.path.isdir(body_dir):
            residue_pat = re.compile(
                r'^\s*(按照您的要求|根据您的要求|遵照要求|按您的要求|继续(续写|写作|写)|'
                r'以下是(本章|正文|内容)|好的?，?(我|下面|现在)(来|开始)?(写|继续)|'
                r'\[?(本章|本段|正文)?(草稿|初稿|正文|内容)\]?[:：]\s*$)'
            )
            for fn in sorted(os.listdir(body_dir)):
                if not re.match(r'^第\d{4}章', fn) or not fn.endswith('.md'):
                    continue
                txt = open(os.path.join(body_dir, fn), encoding='utf-8').read()
                first_para = txt.strip().split('\n\n', 1)[0]
                # 跳过 YAML frontmatter（正文文件应无 YAML，但防御性跳过）
                if first_para.startswith('---'):
                    first_para = txt.strip().split('\n---\n', 1)[-1].strip().split('\n\n', 1)[0]
                if residue_pat.search(first_para):
                    residue_bad.append(f'{fn}: 首段疑似工具残留「{first_para[:40]}」')
        check('正文无工具残留', not residue_bad,
              '; '.join(residue_bad) if residue_bad else '')

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
