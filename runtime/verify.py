#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 流程门禁（verify.py）
=====================================
把"自动完成"从 Agent 自觉升级为程序强制。关键动作（初始化 / 落库 / 总览生成）
之后必须运行本脚本：PASS → 允许继续下一步；FAIL → 流程禁止继续，先修复再走。

用法：
  python runtime/verify.py --root <项目根> [--scope init|narrative|evidence|execution|outline|settle|all]

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
  [落库一致] index↔change_report↔正文互核（v1.9.1 · settle 范围：archived 必须有三件套；有正文但 index=outline_only 即 FAIL）
  [timeline] timeline.md 登记章数 ≥ index 已落库章数（v1.9.1 · settle：防时间线滞后）
  [hooks唯一] hooks.md ID 重复 = FAIL（v1.9.1 · settle：防伏笔 ID 冲突）
  [hooks登记] change_report 宣称"待登记"的伏笔必须在 hooks.md 找到（v1.9.1 · settle：防只写报告不登记）
  [逗号密度] 正文逗号密度 >12% = FAIL（v1.9.1 · all：防碎句退化逐章放大）
  [检验报告] 兼容 故事/元数据/ 与 故事/reports/ 双路径（v1.9.1 · settle）
  [退化趋势] scope=trend：逐章逗号/破折号/短句指标 vs 前5章基线偏离>50%、连续5章爬升 = WARN（v1.9.1 · 预警逐章放大，不等超阈值）
  [正文质量#17-#33] #17章内重复FAIL / #18跨章整句重复WARN / #19半角标点 / #24占位符FAIL / #25崩溃句FAIL /
      #26章末净化(引用块/细纲钩子句/元数据/markdown残留) / #30口癖密度(破折号≥5每千字或"的方向是">5=FAIL,破折号3-5或"了一下">15=WARN) /
      #33章末雷同(末1句逐字≥35字FAIL/20-35WARN + 18组收尾意象在≥3章末出现=WARN)
  [残章/产物] #20残章字数(archived<target×0.7 FAIL,0.7-0.85 WARN;非archived半成品<0.5 WARN) / #21章级产物齐套 /
      #27 change_report充实度(<100字WARN) / #29 init关键文件非空(作者身份+世界观)
  [状态/批跑] #23角色物品状态(物品/角色ID重复、表格内死而复生=FAIL;多人持有/同名重复/同ID多行/死者晚章正文出现=WARN) /
      #28伏笔债务(超过计划回收章+5仍active/pending=FAIL,临近=WARN;无计划章按类型化年龄 chekhov30/50、mystery等60/100;partial/due排除) /
      #32批跑断链(正文跳号、前章有正文未archived即续写后章=FAIL;细纲跳号/超前正文>3章=WARN)

结果三态：PASS / WARN（预警，不改变退出码）/ FAIL（退出码 1）。

退出码：0=全部通过（可有 WARN）  1=存在 FAIL 项
"""
import argparse, json, os, re, sys
from statistics import median
from collections import Counter

# v1.9.1 #33 收尾套路词表（按"组"统计：末2句命中本组任一短语、且本组在 ≥3 章结尾出现即 WARN）。
# 设计：夕阳/背影只是举例，故按网文高频"模板化收尾"穷举成组；优先多字固定短语、不用裸单字（降低正常描写误伤）；
# 仅跨章反复（≥3）才提示，单次出现不预警；纯"同句型不同词"机器误报高，交 S3 收尾复核，本表不判。
TAIL_CLICHE_GROUPS = {
    '夕阳黄昏': r'夕阳|落日|余晖|残阳|斜阳|黄昏时分|日暮',
    '背影拉长': r'背影|身影.{0,8}(拉|拖).{0,2}长|影子.{0,4}(拉|拖).{0,2}长|渐行渐远',
    '叹气': r'长叹|长长?地?叹了?口?气|吁了?口气|叹了口气|暗自叹息|一声叹息',
    '夜色星月': r'夜色|夜幕|月色|月光|星光(闪烁|点点)?|夜深了?|入夜|夜空',
    '握拳发誓': r'握紧(了)?拳|拳头.{0,3}(握紧|攥紧)|攥紧(了)?拳|(目光|眼神).{0,4}坚定|暗暗?发誓|下定(了)?决心|咬(紧)?了?咬牙',
    '远去尽头': r'渐渐远去|逐渐远去|远去的?背影|消失在.{0,6}(尽头|夜色|黑暗)|路的尽头|走向远方',
    '寒意发凉': r'背后一凉|脊背发凉|背脊发凉|一股寒意|不寒而栗|冷汗(直冒|直流)?|汗毛倒竖|毛骨悚然|头皮发麻',
    '心跳屏息': r'心跳(漏了?一拍|加速|一紧|提到了?嗓子眼)|屏住(了)?呼吸|呼吸一滞|倒吸(一口|了口)?凉气|心口一紧|心脏(猛地)?一缩',
    '眼神目光': r'眼底闪过|眼神(一冷|一沉|一变|一凛|深邃|复杂)|眯起(了)?双眼?|目光(一沉|变冷|闪烁|复杂|深邃)|深邃的?目光|意味深长',
    '嘴角冷笑': r'嘴角(勾起|上扬|微微一弯|噙着)|勾起一抹(弧度|冷笑|笑意|笑)|冷笑(一声|道|着)|似笑非笑|唇角(勾起|上扬)',
    '寂静凝固': r'一片(寂静|死寂|沉默|沉寂)|死一般的?(寂静|沉寂|沉默|安静)|空气(仿佛|瞬间)?(凝固|凝滞)|陷入(了)?(沉默|沉寂)|鸦雀无声|静得(可怕|能听见|出奇)|落针可闻',
    '风收尾': r'晚风(吹来|拂过|习习)?|寒风(呼啸|凛冽)?|一阵(凉|冷|狂)?风(吹|刮|卷)|风(吹|卷)起|凉风(袭来|一吹)|风声呼啸',
    '雨收尾': r'下起(了)?(大|小|毛)?雨|大雨(滂沱|倾盆|如注)|雨水(混着|打在|顺着)|细雨(绵绵|纷飞)?|雨点(落下|敲打)|雨越下越大',
    '黑暗吞噬': r'被黑暗吞噬|无边(无际)?的?黑暗|陷入(无边|无尽|一片)?黑暗|夜色如墨|黑暗中(一双|那双|仿佛有).{0,4}眼睛|吞噬(在|进)',
    '叙事越界预告': r'他不知道的是|她不知道的是|此刻的?(他|她).{0,8}还不知道|命运的?齿轮(开始|悄然)?转动|故事(才|刚刚)?开始|真正的?(考验|风暴|危机|较量).{0,6}(才|刚刚)?(开始|来临)|一场(更大的?)?(风暴|危机|阴谋|浩劫).{0,6}(正在|即将).{0,4}(酝酿|逼近|来临|等待)|暴风雨前的?宁静|(他|她)(还|尚)未?意识到(危险|这一切)',
    '设问悬念': r'难道(说|这|他|她|真的|就|是)|这究竟是|他到底是(谁|什么|怎么)|这一切(是巧合|意味着|到底)|为什么会这样|是福是祸|是敌是友|等待(他|她)的?(将)?会是什么',
    '灯火摇曳': r'灯火(阑珊|通明|摇曳)|烛火(摇曳|跳动|熄灭|明灭)|灯光(闪烁|熄灭|昏黄)|一盏(孤)?灯(摇曳)?|火光(跳动|摇曳|明灭)',
    '夜深时逝': r'夜(越来越|渐|渐渐)深|时间一分一秒(地)?(过去|流逝)|不知不觉(间)?(天|已经).{0,6}(亮|黑|深夜|黎明)|天色(渐晚|渐暗|已晚|不早)|转眼(已是|到了)|这一夜(格外|特别)',
}

BANNED = '[['  # 真相文件禁用字符


def walk_md(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith('.md'):
                yield os.path.join(dirpath, f)


def extract_body(txt):
    """去 YAML frontmatter / markdown 标记（标题/引用/表格/列表/代码），返回纯正文。

    供密度、重复、口癖、收尾等统计共用，保证各检查项口径一致。
    """
    txt = re.sub(r'^---\s*.*?---\s*', '', txt, flags=re.S)
    lines = [ln for ln in txt.splitlines()
             if ln.strip() and not ln.lstrip().startswith(('#', '>', '|', '-', '```', '*'))]
    return '\n'.join(lines)


def iter_chapter_bodies(root):
    """遍历 正文/第XXXX章*.md，按章号升序 yield (章号4位, 文件名, 原文, 纯正文)。"""
    body_dir = os.path.join(root, '正文')
    if not os.path.isdir(body_dir):
        return
    for fn in sorted(os.listdir(body_dir)):
        m = re.match(r'^第(\d{4})章.*\.md$', fn)
        if not m:
            continue
        raw = open(os.path.join(body_dir, fn), encoding='utf-8').read()
        yield m.group(1), fn, raw, extract_body(raw)


def chapter_metrics(body):
    """单章量化指标：字数/逗号密度%/破折号每千字/短句占比（<=15字句）。"""
    total = len(re.sub(r'\s+', '', body))
    if total == 0:
        return {'chars': 0, 'comma_pct': 0.0, 'dash_per_k': 0.0, 'short_ratio': 0.0}
    sentences = [s for s in re.split(r'[。！？；!?;]', body) if s.strip()]
    short = sum(1 for s in sentences if len(re.sub(r'\s+', '', s)) <= 15)
    return {
        'chars': total,
        'comma_pct': body.count('，') * 100.0 / total,
        'dash_per_k': body.count('——') * 1000.0 / total,
        'short_ratio': (short / len(sentences)) if sentences else 0.0,
    }


def normalized(text):
    return re.sub(r'\s+', '', text)


def parse_index_status(root):
    """综合 index.md 解析每章状态 → (archived:set, smap:{ch:status})。
    兼容集中式（唐末 第01卷-第01章…archived）与分散式（星尘 | 0001 |…已落库）。"""
    archived, smap = set(), {}
    idx = os.path.join(root, '故事', '元数据', 'index.md')
    if not os.path.isfile(idx):
        return archived, smap
    for line in open(idx, encoding='utf-8').read().splitlines():
        if not line.strip().startswith('|'):
            continue
        if re.search(r'\barchived\b', line) or '已落库' in line:
            status = 'archived'
        elif 'outline_only' in line:
            status = 'outline_only'
        elif re.search(r'\bdrafting\b', line):
            status = 'drafting'
        elif re.search(r'\breview\b', line) or '检验中' in line:
            status = 'review'
        else:
            continue
        nums = re.findall(r'\d{4}', line)
        if not nums:
            continue
        ch = nums[-1] if ('第' in line and '卷' in line) else nums[0]
        smap[ch] = status
        if status == 'archived':
            archived.add(ch)
    return archived, smap


def chapter_artifacts(root, ch):
    """某章各产物存在性；change_report 兼容 change_report_第X章.md 与旧版 第X章.md 流程日志。"""
    meta = os.path.join(root, '故事', '元数据')
    logs = os.path.join(root, '故事', '日志')
    reports = os.path.join(root, '故事', 'reports')
    outline_dir = os.path.join(root, '大纲')
    body_dir = os.path.join(root, '正文')
    body = os.path.isdir(body_dir) and any(
        f.startswith(f'第{ch}章') and f.endswith('.md') for f in os.listdir(body_dir))
    return {
        'body': bool(body),
        'outline': os.path.isfile(os.path.join(outline_dir, f'细纲_第{ch}章.md')),
        'chapter_meta': os.path.isfile(os.path.join(meta, f'chapter_{ch}.md')),
        'change_report': os.path.isfile(os.path.join(logs, f'change_report_第{ch}章.md'))
                          or os.path.isfile(os.path.join(logs, f'第{ch}章.md')),
        'review': os.path.isfile(os.path.join(meta, f'检验报告_第{ch}章.md'))
                   or os.path.isfile(os.path.join(reports, f'检验报告_第{ch}章.md')),
    }


def project_uses_chapter_meta(root):
    """分散式项目：元数据目录存在任一 chapter_XXXX.md（集中式仅 index.md，不要求章元数据）。"""
    meta = os.path.join(root, '故事', '元数据')
    return os.path.isdir(meta) and any(re.match(r'^chapter_\d{4}\.md$', f) for f in os.listdir(meta))


def project_has_reviews(root):
    """项目是否走 v1.9 S3 产物链（存在任一检验报告）。"""
    for d in (os.path.join(root, '故事', '元数据'), os.path.join(root, '故事', 'reports')):
        if os.path.isdir(d) and any(f.startswith('检验报告_第') for f in os.listdir(d)):
            return True
    return False


def internal_duplicates(body, min_len=40, step=1):
    """章内 ≥min_len 字非重叠重复片段，返回去重片段（最多 2 条，每处重复只报1条）。步长1全采样。"""
    t = normalized(body)
    seen, hits, hit_zones = {}, [], []
    for i in range(0, len(t) - min_len + 1, step):
        seg = t[i:i + min_len]
        if seg in seen:
            if i - seen[seg] >= min_len and not any(abs(i - z) < min_len for z in hit_zones):
                hits.append(seg)
                hit_zones.append(i)
                if len(hits) >= 2:
                    break
        else:
            seen[seg] = i
    return hits


def tail_window(raw, n_sents=2, max_chars=60):
    """结尾窗：去 YAML/markdown 标记后取最后 n_sents 个完整句（按句末标点切），归一化取末 max_chars 字。
    只盯收束句，不纳入结尾前的整段正文（避免与 #18 跨章正文重复重叠、避免过渡句误报）。"""
    txt = re.sub(r'^---\s*.*?---\s*', '', raw, flags=re.S)
    lines = [l for l in txt.splitlines()
             if l.strip() and not l.lstrip().startswith(('#', '>', '|', '-', '```', '*'))]
    body = '\n'.join(lines)
    sents = [s for s in re.split(r'(?<=[。！？])', body) if normalized(s)]
    tail = ''.join(sents[-n_sents:]) if sents else body
    return normalized(tail)[-max_chars:]


def table_rows(text, header_kws):
    """返回表头含全部 header_kws 的那张 markdown 表的数据行（每行是去空格的 cells 列表）。
    只解析第一张命中的表（characters 有基线/当前状态两表时，调用方先切段再传入）。"""
    rows, mode = [], None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith('|'):
            if all(k in s for k in header_kws):
                mode = 'sep'
                continue
            if mode == 'sep' and re.fullmatch(r'\|?[\s:\-|]+\|?', s):
                mode = 'data'
                continue
            if mode == 'data':
                cells = [c.strip() for c in s.strip('|').split('|')]
                if cells and any(cells):
                    rows.append(cells)
        elif mode == 'data' and s:
            break
    return rows


def chap_num(cell):
    """从埋设章/计划回收章单元格提取章号（int），无则 None。
    乱格式实测："0085 前后""约 0280""第 0001 章起""卷1后期（约0050）""卷3末/卷4初""全程""待卷3出场（约0085）"。
    关键：'卷1/卷3'里的 1 位数字是卷号不是章号，必须优先取'约0XXX'或括号内/裸 2-4 位章号；
    纯数字单元格（星尘 "1"/"7"）才接受 1 位。"""
    cell = (cell or '').strip()
    if re.fullmatch(r'0*(\d{1,4})', cell):
        return int(re.fullmatch(r'0*(\d{1,4})', cell).group(1))
    m = re.search(r'约\s*0*(\d{2,4})', cell)                 # 约0050 / 约 0280
    if m:
        return int(m.group(1))
    m = re.search(r'[（(][^）)]*?0*(\d{2,4})', cell)          # 括号内章号
    if m:
        return int(m.group(1))
    m = re.search(r'(?<!\d)0*(\d{2,4})(?!\d)', cell)         # 裸 2-4 位（0085前后 / 0001-0085）
    if m:
        return int(m.group(1))
    if '卷' in cell:                                          # 仅剩"卷X"1 位数字 = 卷号
        return None
    m = re.search(r'0*(\d{1,4})', cell)
    return int(m.group(1)) if m else None


def holder_multi(holder_cell):
    """当前持有者列是否出现 ≥2 个具体人名（按 / 、 ， 和 拆分，排除组织/地点/载具词）。
    共用物资（姜枫/周平/狗子）会命中，仅作 WARN 提示人工区分"共有"还是"归属冲突"。
    先剥括号说明——"张谨（孔目官）""姜枫（胸口，h_004…）"括号内顿号/逗号不得误判为多人。"""
    h = re.sub(r'[（(].*?[)）]', '', holder_cell or '')
    org = re.compile(r'[号队军营堡船城库寨坊舱帐台所部组馆庄]')
    parts = [p.strip() for p in re.split(r'[/、，,和]', h) if p.strip()]
    nameish = [p for p in parts
               if 2 <= len(p) <= 8 and re.fullmatch(r'[一-鿿（）()A-Za-z·\.]+', p) and not org.search(p)]
    return len(nameish) >= 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--scope', default='all', choices=['init', 'narrative', 'all', 'evidence', 'execution', 'outline', 'settle', 'trend'])
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f'[错误] 项目根不存在: {root}')
        sys.exit(1)

    results = []

    def check(name, status, detail=''):
        # status: True/'pass'=PASS, False/'fail'=FAIL, 'warn'=WARN（预警，不计退出码）
        if status is True:
            status = 'pass'
        elif status is False:
            status = 'fail'
        results.append((name, status, detail))

    def warn(name, detail=''):
        results.append((name, 'warn', detail))

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

    # 10 正文工具/框架残留检查（v1.9 · F-09：AI 工具痕迹漏入正文）
    # 番茄实测案例：高潮点后新章开头整行"按照您的要求，对xx进行续写"——读者直接弃书。
    # 框架显形案例：写作期夹带"这是细纲第X节""我用一下X技巧"——破坏框架隐形原则（writing-guide §0.1）。
    # 检查正文首段是否以工具残留开头，以及全文是否夹带框架自指语言。
    if args.scope in ('all', 'execution'):
        body_dir = os.path.join(root, '正文')
        residue_bad = []
        if os.path.isdir(body_dir):
            residue_pat = re.compile(
                r'^\s*(按照您的要求|根据您的要求|遵照要求|按您的要求|继续(续写|写作|写)|'
                r'以下是(本章|正文|内容)|好的?，?(我|下面|现在)(来|开始)?(写|继续)|'
                r'\[?(本章|本段|正文)?(草稿|初稿|正文|内容)\]?[:：]\s*$)'
            )
            # 框架自指语言（writing-guide §0.1 框架隐形）：写作期不应出现"我在按细纲/用技巧/检查因果循环"类元语言
            framework_pat = re.compile(
                r'(这是(细纲|骨架|冲突链|信息释放)(的|第|中)?|'
                r'按(照|着)?(细纲|骨架|剧本|规划|安排)(来|写|展开)|'
                r'(我|这里)(用(了|一下)?|套(用|了)?|参考(了|一下)?)(细纲|技巧|手法|技法|套路|写法)|'
                r'(检查|核对|对照)(细纲|骨架|因果循环|内核|状态|声线)|'
                r'(本章|本节|这段)(的)?(设计|安排|目的|意图)(是|为|在于)|'
                r'(满足|符合)(了)?(C-00\d|内核三联|驱动标注|骨架)要求)'
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
                # 框架自指检查全文（首段已查过工具残留，此处查框架元语言）
                fw_matches = list(framework_pat.finditer(txt))
                if fw_matches:
                    snippet_idx = fw_matches[0].start()
                    snippet = txt[max(0, snippet_idx - 10): snippet_idx + 30].replace('\n', ' ')
                    residue_bad.append(f'{fn}: 框架自指语言 ×{len(fw_matches)}「{snippet}」')
        check('正文无工具/框架残留', not residue_bad,
              '; '.join(residue_bad) if residue_bad else '')

    # 11 落库一致性：index↔change_report↔正文互核（v1.9.1 · settle/all）
    # 根因修复：唐末第3章"有正文但 index=outline_only + 缺 change_report"、第30章报告自夸30章全落库——机器未核
    if args.scope in ('settle', 'all'):
        idx_path = os.path.join(root, '故事', '元数据', 'index.md')
        log_dir = os.path.join(root, '故事', '日志')
        body_dir = os.path.join(root, '正文')
        settle_bad = []
        archived_chapters = set()
        outline_only_chapters = set()
        if os.path.isfile(idx_path):
            idx_txt = open(idx_path, encoding='utf-8').read()
            # 兼容两种 index 格式：
            #   星尘方舟：| 0001 | 标题 | 已落库 | 字数 | 关键事件 | ... |
            #   唐末：    | 第01卷-第01章 | 标题 | **archived** ✓(...) | 0001 |
            for line in idx_txt.splitlines():
                if not line.strip().startswith('|'):
                    continue
                status = None
                if re.search(r'\barchived\b', line):
                    status = 'archived'
                elif 'outline_only' in line:
                    status = 'outline_only'
                elif re.search(r'\bdrafting\b', line):
                    status = 'drafting'
                elif re.search(r'\breview\b', line) or '检验中' in line:
                    status = 'review'
                elif '已落库' in line:
                    status = 'archived'
                if not status:
                    continue
                nums = re.findall(r'\d{4}', line)
                if not nums:
                    continue
                # 章号取行内 4 位数字：唐末格式(卷-章前缀)取末位，星尘格式取首位
                ch = nums[-1] if ('第' in line and '卷' in line) else nums[0]
                if status == 'archived':
                    archived_chapters.add(ch)
                elif status == 'outline_only':
                    outline_only_chapters.add(ch)
        # ① archived 必须三件套：change_report + 正文
        for ch in sorted(archived_chapters):
            missing = []
            # 兼容两种日志命名：change_report_第XXXX章.md（唐末/v1.9）与 第XXXX章.md（星尘/旧版）
            cr1 = os.path.join(log_dir, f'change_report_第{ch}章.md')
            cr2 = os.path.join(log_dir, f'第{ch}章.md')
            if not os.path.isfile(cr1) and not os.path.isfile(cr2):
                missing.append('缺 change_report/流程日志')
            if os.path.isdir(body_dir):
                has_body = any(f.startswith(f'第{ch}章') and f.endswith('.md') for f in os.listdir(body_dir))
                if not has_body:
                    missing.append('缺正文')
            if missing:
                settle_bad.append(f'第{ch}章(archived但' + ','.join(missing) + ')')
        # ② 有正文但 index 标 outline_only = 漏落库
        if os.path.isdir(body_dir):
            for fn in sorted(os.listdir(body_dir)):
                m = re.match(r'^第(\d{4})章', fn)
                if m and m.group(1) in outline_only_chapters:
                    settle_bad.append(f'第{m.group(1)}章有正文但index仍=outline_only(漏落库)')
        check('落库一致性(index↔报告↔正文)', not settle_bad,
              '; '.join(settle_bad) if settle_bad else f'已核 {len(archived_chapters)} 章 archived')

    # 12 timeline 覆盖：登记章数 ≥ index 已落库章数（v1.9.1 · settle/all）
    if args.scope in ('settle', 'all'):
        tl_path = os.path.join(root, '故事', '真相', 'timeline.md')
        tl_bad = []
        if os.path.isfile(tl_path):
            tl_txt = open(tl_path, encoding='utf-8').read()
            # 兼容 4 位（唐末：| 0001 |）与 1-2 位（星尘：| 1 | / | 19 |）章号
            tl_chapters = set()
            for m in re.finditer(r'^\|\s*(\d{1,4})\s*\|', tl_txt, re.MULTILINE):
                tl_chapters.add(m.group(1).zfill(4))
            idx_path2 = os.path.join(root, '故事', '元数据', 'index.md')
            archived_count = 0
            if os.path.isfile(idx_path2):
                idx_txt2 = open(idx_path2, encoding='utf-8').read()
                # 按行统计 archived（一行可能同时含 archived + 已落库 两个词，不能按词数）
                archived_count = 0
                for _line in idx_txt2.splitlines():
                    if _line.strip().startswith('|') and (re.search(r'\barchived\b', _line) or '已落库' in _line):
                        archived_count += 1
            if archived_count > 0 and len(tl_chapters) < archived_count:
                tl_bad.append(f'timeline 只登记 {len(tl_chapters)} 章 < index 已落库 {archived_count} 章(滞后)')
        else:
            tl_bad.append('缺 timeline.md')
        check('timeline覆盖', not tl_bad, '; '.join(tl_bad) if tl_bad else 'OK')

    # 13 hooks ID 唯一性（v1.9.1 · settle/all）
    if args.scope in ('settle', 'all'):
        hooks_path = os.path.join(root, '故事', '真相', 'hooks.md')
        dup_bad = []
        if os.path.isfile(hooks_path):
            hk_txt = open(hooks_path, encoding='utf-8').read()
            # 只数表格行（以 | h_XXX | 开头），排除备注/说明文字误报
            ids = re.findall(r'^\|\s*h_(\d{3})\s*\|', hk_txt, re.MULTILINE)
            from collections import Counter
            cnt = Counter(ids)
            dups = {k: v for k, v in cnt.items() if v > 1}
            if dups:
                dup_bad.append('重复ID: ' + ', '.join(f'h_{k}×{v}' for k, v in sorted(dups.items())))
        check('hooks唯一性', not dup_bad, '; '.join(dup_bad) if dup_bad else 'OK')

    # 14 hooks 登记核对：change_report 宣称"待登记"的伏笔必须在 hooks.md 找到（v1.9.1 · settle/all）
    if args.scope in ('settle', 'all'):
        log_dir2 = os.path.join(root, '故事', '日志')
        hooks_path2 = os.path.join(root, '故事', '真相', 'hooks.md')
        reg_bad = []
        if os.path.isdir(log_dir2) and os.path.isfile(hooks_path2):
            hk_txt2 = open(hooks_path2, encoding='utf-8').read()
            for fn in sorted(os.listdir(log_dir2)):
                if not re.match(r'^change_report_第\d{4}章\.md$', fn):
                    continue
                cr_txt = open(os.path.join(log_dir2, fn), encoding='utf-8').read()
                # 找"已写入 hooks.md 待登记"声明中的 ID
                for m in re.finditer(r'(?:已写入 hooks\.md 待登记|待登记)[^。\n]*?(h_\d{3})', cr_txt):
                    hid = m.group(1)
                    if hid not in hk_txt2:
                        reg_bad.append(f'{fn}: {hid} 宣称待登记但 hooks.md 无此行')
        check('hooks登记核对', not reg_bad, '; '.join(reg_bad) if reg_bad else 'OK')

    # 15 逗号密度：>12% = FAIL（v1.9.1 · all/settle；防碎句退化逐章放大）
    # 实测基线：正常5-7%，退化到15章9.9%、17章14.4%、19章23.3%。阈值12%留出正常写作余量
    if args.scope in ('all', 'settle'):
        body_dir2 = os.path.join(root, '正文')
        comma_bad = []
        if os.path.isdir(body_dir2):
            for fn in sorted(os.listdir(body_dir2)):
                if not re.match(r'^第\d{4}章', fn) or not fn.endswith('.md'):
                    continue
                txt = open(os.path.join(body_dir2, fn), encoding='utf-8').read()
                # 去 YAML / markdown 标记，只算正文
                txt_body = re.sub(r'^---\s*.*?---\s*', '', txt, flags=re.S)
                lines = [ln for ln in txt_body.splitlines()
                         if ln.strip() and not ln.lstrip().startswith(('#', '>', '|', '-', '```'))]
                body = ''.join(lines)
                total = len(re.sub(r'\s+', '', body))
                if total < 500:  # 短篇/半成品不判（第20章 2008字可判，<500 跳过防止误伤）
                    continue
                commas = body.count('，')
                pct = commas * 100.0 / total
                if pct > 12.0:
                    comma_bad.append(f'{fn}: 逗号密度 {pct:.1f}% (>12%)')
        check('逗号密度', not comma_bad, '; '.join(comma_bad) if comma_bad else 'OK')

    # 16 检验报告位置兼容（v1.9.1 · settle/all）：元数据/ 与 reports/ 双路径
    if args.scope in ('settle', 'all'):
        meta_dir3 = os.path.join(root, '故事', '元数据')
        reports_dir = os.path.join(root, '故事', 'reports')
        found_in = []
        for d in (meta_dir3, reports_dir):
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if re.match(r'^检验报告_第\d{4}章\.md$', fn):
                        found_in.append(os.path.relpath(os.path.join(d, fn), root))
        if not found_in and os.path.isdir(meta_dir3):
            # 无任何检验报告 = 旧版项目未走 v1.9 产物链（唐末现状），提示但不 FAIL（避免旧项目全红）
            check('检验报告位置', True, '未找到检验报告（旧项目无 S3 产物链，提示）')
        else:
            check('检验报告位置', True, f'找到 {len(found_in)} 份（' + '; '.join(sorted(set(os.path.dirname(p) for p in found_in))) + ')')

    # ===== v1.9.1 正文质量补盲（#17/#18/#19/#24/#25/#26/#33 · all/settle，一次遍历）=====
    if args.scope in ('all', 'settle'):
        internal_bad, cross_hits, half_comma = [], [], []
        half_dot_warn, placeholder_bad, crash_bad, tail_purify_bad, md_star_warn = [], [], [], [], []
        dash_bad, fx_bad, dash_warn, le_warn = [], [], [], []   # #30 口癖（破折号FAIL/的方向是FAIL；破折号偏多/了一下 WARN）
        cross_seen = {}                       # ≥25字整句指纹 → 首见章（#18）
        tail40, tail25, tail_fail, tail_warn, fail_pairs = {}, {}, [], [], set()
        cliche_chapters = {k: set() for k in TAIL_CLICHE_GROUPS}
        placeholder_pats = [
            (r'(?:流民|路人|群众|群演|配角|角色|人物)[甲乙丙丁]', '流民甲/乙式占位'),
            (r'(?:角色|人物)\s*[A-ZＡ-Ｚ]', '角色A式占位'),
            (r'【[^】]*(?:角色|人物|名字|名称|占位|XXX|xxx)[^】]*】', '【】占位'),
            (r'[XxＸ]{3,}', 'XXX占位'),
            (r'待\s*定|TBD|TODO|此处占位|占位符', '待定占位'),
        ]
        for ch, fn, raw, body in iter_chapter_bodies(root):
            # 30 口癖密度（破折号≥5/千字或"的方向是">5次=FAIL；破折号3-5/千字、"了一下">15次=WARN）
            mt30 = chapter_metrics(body)
            if mt30['dash_per_k'] >= 5:
                dash_bad.append(f'{fn}: 破折号{mt30["dash_per_k"]:.1f}/千字(≥5)')
            elif mt30['dash_per_k'] >= 3:
                dash_warn.append(f'{fn}: 破折号{mt30["dash_per_k"]:.1f}/千字(偏多)')
            nfx = body.count('的方向是')
            if nfx > 5:
                fx_bad.append(f'{fn}:“的方向是”{nfx}次(>5)')
            nle = body.count('了一下')
            if nle > 15:
                le_warn.append(f'{fn}:“了一下”{nle}次(>15)')
            # 17 章内重复（≥40字非重叠 = FAIL）
            for seg in internal_duplicates(body):
                internal_bad.append(f'{fn}: 章内重复「{seg[:20]}…」')
            # 18 跨章重复（≥25字整句跨章相同 = WARN；句子为自然边界不依赖采样网格；刻意回环交 S3）
            for sent in re.split(r'[。！？\n]', body):
                s = normalized(sent)
                if len(s) < 25:
                    continue
                if s in cross_seen:
                    if cross_seen[s] != ch:
                        cross_hits.append(f'「{s[:24]}…」第{cross_seen[s]}章≈第{ch}章')
                else:
                    cross_seen[s] = ch
            # 19 半角标点（半角逗号≥5 FAIL；中文后半角句号≥5 WARN）
            if body.count(',') >= 5:
                half_comma.append(f'{fn}: 半角逗号 {body.count(",")} 个')
            n_dot = len(re.findall(r'[一-鿿]\.', body))
            if n_dot >= 5:
                half_dot_warn.append(f'{fn}: 中文后半角句号 {n_dot} 处')
            # 24 占位符未替换（FAIL）
            for pat, label in placeholder_pats:
                mph = re.search(pat, body)
                if mph:
                    placeholder_bad.append(f'{fn}: {label}「{mph.group(0)[:16]}」')
                    break
            # 25 生成崩溃句（FAIL）：①3-4字词组无分隔紧邻三连（2字词放过"没事没事"式口语）；②单句破折号≥3；③短句(≤40字)词组≥3次且破折号≥2（机械嵌套）
            # 有意复沓不误判：对话中"小禾……小禾……"用省略号、无破折号，三条均不命中
            crash = None
            m25a = re.search(r'([一-鿿]{3,4})\1{2,}', body)
            if m25a:
                crash = f'词组紧邻复读「{m25a.group(0)[:24]}」'
            else:
                for sent in re.split(r'[。！？\n]', body):
                    s = sent.strip()
                    if s.count('——') >= 3:
                        crash = f'单句破折号≥3「{s[:28]}」'
                        break
                    if len(normalized(s)) <= 40 and s.count('——') >= 2:
                        for w, c in Counter(re.findall(r'[一-鿿]{2,4}', s)).items():
                            if c >= 3:
                                crash = f'破折号嵌套词组复读「{s[:28]}」'
                                break
                        if crash:
                            break
            if crash:
                crash_bad.append(f'{fn}: {crash}')
            # 26 章末净化（FAIL）：末3非空行不得含引用块/细纲钩子句/生产元数据
            raw_lines = [ln for ln in re.sub(r'^---\s*.*?---\s*', '', raw, flags=re.S).splitlines() if ln.strip()]
            for ln in raw_lines[-3:]:
                hit26 = None
                if ln.lstrip().startswith('>'):
                    hit26 = '引用块(>)漏入正文'
                elif re.search(r'——\s*钩子\s*[：:]', ln) or re.search(r'钩子\s*[：:]\s*\S', ln):
                    hit26 = '章末细纲钩子句'
                elif re.search(r'承前章末|精确还原|章末钩子精确', ln):
                    hit26 = '生产元数据漏入'
                if hit26:
                    shown = ln.strip()
                    shown = shown if len(shown) <= 46 else shown[:12] + '…' + shown[-32:]
                    tail_purify_bad.append(f'{fn}: {hit26}「{shown}」')
                    break
            # markdown 加粗符 ** 未闭合（半截残留，如"——**云纹的"漏了收尾 **）
            if body.count('**') % 2 == 1:
                tail_purify_bad.append(f'{fn}: markdown加粗符**未闭合(半截残留)')
            elif body.count('**') >= 2:
                md_star_warn.append(f'{fn}: 正文含markdown加粗×{body.count("**") // 2}(网文平台会显示字面星号)')
            # 33 章末雷同：逐字只比最后1句（收束句零容忍；倒数第2句起的正文重复归 #18）；意象套路扫末2句
            tw = tail_window(raw, n_sents=1, max_chars=60)               # 末句，逐字比对
            last2 = tail_window(raw, n_sents=2, max_chars=60)            # 末2句，意象判定
            for grp, pat in TAIL_CLICHE_GROUPS.items():
                if re.search(pat, last2):
                    cliche_chapters[grp].add(ch)
            for i in range(0, len(tw) - 35 + 1, 10):
                seg = tw[i:i + 35]
                if seg in tail40 and tail40[seg] != ch:
                    pair = tuple(sorted((tail40[seg], ch)))
                    fail_pairs.add(pair)
                    tail_fail.append(f'结尾「{seg[:18]}…」第{tail40[seg]}章≈第{ch}章')
                else:
                    tail40.setdefault(seg, ch)
            for i in range(0, len(tw) - 20 + 1, 8):
                seg = tw[i:i + 20]
                if seg in tail25 and tail25[seg] != ch:
                    pair = tuple(sorted((tail25[seg], ch)))
                    if pair not in fail_pairs:
                        tail_warn.append(f'结尾「{seg[:16]}…」第{tail25[seg]}章≈第{ch}章')
                else:
                    tail25.setdefault(seg, ch)
        for grp, chs in cliche_chapters.items():
            if len(chs) >= 3:
                tail_warn.append(f'收尾意象「{grp}」出现于第{",".join(sorted(chs)[:8])}章(≥3章雷同)')
        tail_fail, tail_warn = list(dict.fromkeys(tail_fail)), list(dict.fromkeys(tail_warn))
        cross_hits = list(dict.fromkeys(cross_hits))
        check('章内重复(#17)', not internal_bad, '; '.join(internal_bad[:6]))
        check('跨章重复(#18)', 'warn' if cross_hits else 'pass',
              ('; '.join(cross_hits[:6]) + (f' 共{len(cross_hits)}处' if cross_hits else '')) if cross_hits else 'OK')
        check('半角逗号(#19)', not half_comma, '; '.join(half_comma[:6]))
        if half_dot_warn:
            warn('半角句号(#19)', '; '.join(half_dot_warn[:5]))
        check('占位符未替换(#24)', not placeholder_bad, '; '.join(placeholder_bad[:6]))
        check('生成崩溃句(#25)', not crash_bad, '; '.join(crash_bad[:6]))
        check('正文净化(#26)', not tail_purify_bad, '; '.join(tail_purify_bad[:8]))
        if md_star_warn:
            warn('正文markdown加粗(#26)', '; '.join(md_star_warn[:6]))
        check('章末雷同(#33)', 'fail' if tail_fail else ('warn' if tail_warn else 'pass'),
              '; '.join((tail_fail + tail_warn)[:8]) if (tail_fail or tail_warn) else 'OK')
        check('口癖密度(#30)', not (dash_bad or fx_bad), '; '.join((dash_bad + fx_bad)[:6]))
        if dash_warn or le_warn:
            warn('口癖密度(#30)', '; '.join((dash_warn + le_warn)[:6]))

    # ===== v1.9.1 落库产物补盲（#20 残章 / #21 产物齐套 / #27 报告敷衍 · settle/all）=====
    if args.scope in ('settle', 'all'):
        archived_v, smap_v = parse_index_status(root)
        target_v = cfg.get('target_word_count', 3000)
        residual_fail, residual_warn, ch_union = [], [], set(archived_v) | set(smap_v)
        for ch, fn, raw, body in iter_chapter_bodies(root):
            ch_union.add(ch)
            n = chapter_metrics(body)['chars']
            if n < 500:
                continue
            if ch in archived_v and n < target_v * 0.7:
                residual_fail.append(f'第{ch}章已落库但仅{n}字(<{int(target_v * 0.7)})=严重残章')
            elif ch in archived_v and n < target_v * 0.85:
                residual_warn.append(f'第{ch}章已落库{n}字(临界{int(target_v * 0.85)},统计口径容差)')
            elif ch not in archived_v and n < target_v * 0.5:
                residual_warn.append(f'第{ch}章仅{n}字(<{int(target_v * 0.5)})疑似半成品')
        check('残章字数(#20)', 'fail' if residual_fail else ('warn' if residual_warn else 'pass'),
              '; '.join(residual_fail + residual_warn)[:400] or 'OK')
        outline_dir_v = os.path.join(root, '大纲')
        if os.path.isdir(outline_dir_v):
            for f in os.listdir(outline_dir_v):
                mo = re.match(r'^细纲_第(\d{4})章\.md$', f)
                if mo:
                    ch_union.add(mo.group(1))
        uses_meta, has_rev = project_uses_chapter_meta(root), project_has_reviews(root)
        prod_bad, prod_warn = [], []
        for ch in sorted(ch_union):
            art = chapter_artifacts(root, ch)
            if art['body'] and not art['outline']:
                prod_bad.append(f'第{ch}章有正文但缺细纲')
            if uses_meta and ch in archived_v and not art['chapter_meta']:
                prod_bad.append(f'第{ch}章(archived)缺chapter元数据')
            if has_rev and ch in archived_v and not art['review']:
                prod_warn.append(f'第{ch}章(archived)缺检验报告')
        check('章级产物齐套(#21)', 'fail' if prod_bad else ('warn' if prod_warn else 'pass'),
              '; '.join(prod_bad + prod_warn)[:400] or 'OK')
        cr_dir = os.path.join(root, '故事', '日志')
        cr_warn = []
        if os.path.isdir(cr_dir):
            for fn in sorted(os.listdir(cr_dir)):
                if not re.match(r'^change_report_第\d{4}章\.md$', fn):
                    continue
                core = normalized(extract_body(open(os.path.join(cr_dir, fn), encoding='utf-8').read()))
                core = re.sub(r'\[[ xX✓√]\]', '', core)
                if len(core) < 100:
                    cr_warn.append(f'{fn}: 实质内容仅{len(core)}字(<100)疑似敷衍')
        check('change_report充实度(#27)', 'warn' if cr_warn else 'pass', '; '.join(cr_warn[:6]) or 'OK')

    # ===== v1.9.1 状态一致性 / 伏笔债务 / 批跑断链（#23 / #28 / #32 · settle/all）=====
    if args.scope in ('settle', 'all'):
        truth = os.path.join(root, '故事', '真相')
        archived_c, _ = parse_index_status(root)
        body_chs = sorted(int(c) for c, _, _, _ in iter_chapter_bodies(root))
        # 伏笔债务按"故事实际推进到的章"算（正文进度），不是落库进度
        cur_ch = max([int(c) for c in archived_c] + body_chs) if (archived_c or body_chs) else 0

        # ---------- #23 角色 / 物品状态表格级一致性 ----------
        c23_fail, c23_warn = [], []
        obj_path = os.path.join(truth, 'objects.md')
        if os.path.isfile(obj_path):
            orows = table_rows(open(obj_path, encoding='utf-8').read(), ['物品ID', '当前持有者'])
            obj_ids, obj_names = Counter(), {}
            for r in orows:
                if len(r) < 4 or not re.match(r'obj_?\d+', r[0]):
                    continue
                oid, nm = r[0], r[1]
                holder = re.sub(r'[（(].*?[)）]', '', r[3]).strip()   # 剥括号说明再归一持有者
                obj_ids[oid] += 1
                obj_names.setdefault(nm, []).append(holder)
                if holder_multi(holder):
                    c23_warn.append(f'物品「{nm}」持有者列多人「{holder}」(确认共有还是归属冲突)')
            for oid, c in obj_ids.items():
                if c > 1:
                    c23_fail.append(f'物品ID {oid} 重复登记 {c} 行')
            for nm, hs in obj_names.items():
                if len(hs) > 1:
                    if len(set(hs)) > 1:
                        c23_warn.append(f'同名物品「{nm}」{len(hs)}行且持有者不一致({"/".join(sorted(set(hs)))})')
                    else:
                        c23_warn.append(f'同名物品「{nm}」重复登记{len(hs)}行(持有者均为{hs[0]})')
        char_path = os.path.join(truth, 'characters.md')
        deads = {}   # 姓名 → 死亡章
        if os.path.isfile(char_path):
            cseg = open(char_path, encoding='utf-8').read().split('当前状态', 1)[-1]  # 只看当前状态表，跳过基线摘要表
            id_rows = {}
            for r in table_rows(cseg, ['mortal']):
                if len(r) < 8 or not re.match(r'[a-zA-Z]', r[0]):
                    continue
                cid, nm, st = r[0], r[1], r[2]
                id_rows.setdefault(cid, []).append((st, chap_num(r[7]), nm))
                if 'true_dead' in st and nm:
                    deads[nm] = chap_num(r[7])
            for cid, lst in id_rows.items():
                if len(lst) > 1:
                    sts = [x[0] for x in lst]
                    if any('true_dead' in s for s in sts) and \
                       any(re.search(r'alive|resurrected|false_dead|missing', s) for s in sts):
                        c23_fail.append(f'角色 {cid} 当前状态表同时 true_dead 与存活状态(死而复生/状态冲突)')
                    else:
                        c23_warn.append(f'角色ID {cid} 当前状态表重复{len(lst)}行(新旧状态未合并)')
        if deads:   # 死者在更晚章【正文】出现（WARN：念名单/回忆/闪回是正常的，复活行动才是穿帮；按死者聚合，人工确认）
            mention = {}
            for ch, fn, raw, body in iter_chapter_bodies(root):
                rch = int(ch)
                for nm, dch in deads.items():
                    if dch is not None and rch > dch and nm in body:
                        mention.setdefault(nm, []).append(rch)
            for nm, chs in mention.items():
                chs_str = ','.join(f'{c:04d}' for c in chs) if len(chs) <= 6 \
                    else f'{chs[0]:04d}…{chs[-1]:04d}(共{len(chs)}章)'
                c23_warn.append(f'死者「{nm}」(殁于第{deads[nm]:04d}章)在第{chs_str}正文出现(确认回忆/闪回,非复活行动)')
        check('角色/物品状态一致(#23)', not c23_fail, '; '.join(c23_fail[:6]))
        if c23_warn:
            warn('角色/物品状态一致(#23)', '; '.join(c23_warn[:8]))

        # ---------- #28 伏笔债务（计划回收章优先；无计划才按类型化年龄；partial/due 排除）----------
        c28_fail, c28_warn = [], []
        hooks_p = os.path.join(truth, 'hooks.md')
        if os.path.isfile(hooks_p):
            for r in table_rows(open(hooks_p, encoding='utf-8').read(), ['埋设章', '推进状态']):
                # cells: ID0 类型1 内容2 埋设章3 计划回收章4 实际回收章5 推进状态6 下一回收点7 状态8 可见性9
                if len(r) < 9 or not re.match(r'h_?\d+', r[0]):
                    continue
                hid, typ, bury_c, plan_c, prog, status = r[0], r[1], r[3], r[4], r[6], r[8]
                if 'active' not in status or re.search(r'partial|due', prog):
                    continue
                bury, plan = chap_num(bury_c), chap_num(plan_c)
                if bury is None or bury > cur_ch:
                    continue   # 埋设章未知 / 属未来规划伏笔
                age = cur_ch - bury
                if plan is not None:
                    if cur_ch > plan + 5:
                        c28_fail.append(f'{hid}({typ})计划第{plan}章回收,已到{cur_ch}章仍active/pending(伏笔违约)')
                    elif cur_ch >= plan - 3:
                        c28_warn.append(f'{hid}({typ})临近计划回收第{plan}章(当前{cur_ch})仍未推进')
                else:
                    t = typ.lower()
                    w_age, f_age = (30, 50) if 'chekhov' in t else \
                                   (60, 100) if re.search(r'mystery|identity|emotion', t) else (40, 80)
                    if age > f_age:
                        c28_fail.append(f'{hid}({typ})无计划回收章,active已{age}章(>{f_age})长期悬空')
                    elif age > w_age:
                        c28_warn.append(f'{hid}({typ})无计划回收章,active已{age}章(>{w_age})')
        check('伏笔债务(#28)', not c28_fail, '; '.join(c28_fail[:6]))
        if c28_warn:
            warn('伏笔债务(#28)', '; '.join(c28_warn[:6]))

        # ---------- #32 批跑章号连续 + 落库断链（错误不向下游传播的机器闸）----------
        c32_fail, c32_warn = [], []
        outline_chs = set()
        for d in (os.path.join(root, '故事', '元数据'), os.path.join(root, '大纲')):
            if os.path.isdir(d):
                for f in os.listdir(d):
                    mo = re.match(r'^细纲_第(\d{4})章\.md$', f)
                    if mo:
                        outline_chs.add(int(mo.group(1)))
        if body_chs:
            for expect in range(body_chs[0], body_chs[-1] + 1):
                if expect not in body_chs:
                    c32_fail.append(f'正文缺第{expect:04d}章(跳号)')
            unarch = [c for c in body_chs if f'{c:04d}' not in archived_c]
            if unarch and body_chs[-1] > unarch[0]:
                c32_fail.append(f'第{unarch[0]:04d}章有正文但未落库即连续批写到第{body_chs[-1]:04d}章(批跑落库断链)')
        if outline_chs:
            olo, ohi = min(outline_chs), max(outline_chs)
            for expect in range(olo, ohi + 1):
                if expect not in outline_chs:
                    c32_warn.append(f'细纲缺第{expect:04d}章(跳号)')
            if body_chs and ohi > body_chs[-1] + 3:
                c32_warn.append(f'细纲排到第{ohi:04d}章,超前正文第{body_chs[-1]:04d}章>3章(一章一闭环,勿批量预生成)')
        check('批跑章号连续/落库断链(#32)', not c32_fail, '; '.join(c32_fail[:6]))
        if c32_warn:
            warn('批跑章号连续/落库断链(#32)', '; '.join(c32_warn[:6]))

    # 29 init 关键文件非空（仅 init：作者身份 + 世界观，防空目录即开写）
    if args.scope == 'init':
        init_bad = []
        def real_md_chars(d):
            tot = 0
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith('.md') and f != '.gitkeep':
                        tot += len(normalized(open(os.path.join(d, f), encoding='utf-8').read()))
            return tot
        if real_md_chars(os.path.join(root, '配置', '身份')) < 50:
            init_bad.append('缺作者身份实质文件（配置/身份/*.md）')
        world_chars = 0
        for w in ('故事/真相/world.md', '设定/世界观.md'):
            p = os.path.join(root, w)
            if os.path.isfile(p):
                world_chars += len(normalized(open(p, encoding='utf-8').read()))
        if world_chars < 50:
            init_bad.append('缺世界观实质内容（故事/真相/world.md 或 设定/世界观.md）')
        check('init关键文件非空(#29)', not init_bad, '; '.join(init_bad))

    # 31 退化趋势 + 基线（v1.9.1 · scope=trend 或 all；WARN 预警，不改变退出码）
    # 治"逐章自我放大"：固定阈值抓不住早期爬坡（第10章 6.9% 未超标但在恶化），
    # 用"前5章基线 + 连续3章上升"在超阈值前预警。
    if args.scope in ('trend', 'all'):
        series = []
        for ch, fn, raw, body in iter_chapter_bodies(root):
            mt = chapter_metrics(body)
            if mt['chars'] < 500:
                continue  # 半成品不纳入趋势
            series.append((ch, mt))
        if len(series) >= 3:
            metric_defs = [('逗号密度%', 'comma_pct'), ('破折号/千字', 'dash_per_k'), ('短句占比', 'short_ratio')]
            base_n = min(5, len(series))
            baseline = {k: median([m[k] for _, m in series[:base_n]]) for _, k in metric_defs}
            trend_msgs = []
            # a) 单章指标较基线偏离 >50%
            for ch, mt in series:
                for label, k in metric_defs:
                    b = baseline[k]
                    if b > 1e-9 and mt[k] > b * 1.5:
                        trend_msgs.append(f'第{ch}章 {label}={mt[k]:.2f} 高于基线{b:.2f}')
            # b) 连续 ≥5 章非降且末值较首值增幅 ≥30%（窗口拉长，过滤早期 3 章正常起伏）
            for label, k in metric_defs:
                vals = [(ch, mt[k]) for ch, mt in series]
                hit = None
                for i in range(len(vals) - 4):
                    window = vals[i:i + 5]
                    ws = [v for _, v in window]
                    if all(ws[j] <= ws[j + 1] for j in range(4)) and ws[0] > 0 and ws[-1] >= ws[0] * 1.3:
                        hit = (window[0][0], window[-1][0], ws[0], ws[-1])
                        break
                if hit:
                    trend_msgs.append(f'{label} 第{hit[0]}→{hit[1]}章连续5章爬升({hit[2]:.2f}→{hit[3]:.2f})，疑似逐章放大')
            table = ['章号 | 逗号% | 破折号/千 | 短句%']
            for ch, mt in series:
                table.append(f'{ch} | {mt["comma_pct"]:.1f} | {mt["dash_per_k"]:.1f} | {mt["short_ratio"]:.2f}')
            detail = '退化曲线:\n    ' + '\n    '.join(table) + (
                '\n    预警: ' + '；'.join(trend_msgs) if trend_msgs else '\n    预警: 无（指标平稳）')
            check('退化趋势', 'warn' if trend_msgs else 'pass', detail)
        else:
            check('退化趋势', 'pass', f'有效章仅 {len(series)} 章（<3），无法判趋势')

    # 汇总
    fails = [r for r in results if r[1] == 'fail']
    warns = [r for r in results if r[1] == 'warn']
    print(f'=== Novel Engine 流程门禁 ({args.scope}) ===')
    for name, status, detail in results:
        mark = {'pass': 'PASS', 'warn': 'WARN', 'fail': 'FAIL'}[status]
        print(f'  [{mark}] {name}' + (f'  — {detail}' if detail else ''))
    print(f'--- PASS {len(results) - len(fails) - len(warns)} / WARN {len(warns)} / FAIL {len(fails)}，共 {len(results)} 项 ---')
    if fails:
        print('结论: FAIL — 流程禁止继续，修复后再跑。')
        sys.exit(1)
    if warns:
        print('结论: PASS（含 WARN 预警，建议人工确认后继续）。')
        sys.exit(0)
    print('结论: PASS — 可继续下一步。')
    sys.exit(0)


if __name__ == '__main__':
    main()
