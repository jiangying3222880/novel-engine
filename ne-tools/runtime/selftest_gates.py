#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_gates.py — 流程门禁回归自测（v1.9.1.3 新增 · D-31）
============================================================
在临时目录构造最小项目夹具，逐场景运行 verify.py 并断言预期结果，
把"门禁行为"变成可复现回归（治 D-31：此前 0 误报依赖仓库外两本事故书，第三方无法独立复现）。

用法：
  python runtime/selftest_gates.py            # 跑全部场景
  python runtime/selftest_gates.py -v         # 额外打印每场景的 verify 关键输出行
  python runtime/selftest_gates.py --keep     # 保留临时夹具目录供人工检查（默认脚本自行清理自己创建的临时目录）

退出码：0 = 全部断言通过；1 = 有断言失败（门禁行为回归，禁止发版）。
维护约定：新增/修改 verify.py 检查项时，**先在本脚本登记预期行为，再改代码**（预期先行）。
场景与缺陷登记表对应：S1=D-28 / S2=D-29 / S3=D-30 / S4=D-01 / S5=D-04 / S6=D-05 / S7=D-06 / S8=D-07。
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VERIFY = SCRIPT_DIR / 'verify.py'
WORLD_TICK = SCRIPT_DIR / 'world_tick.py'
SKILL_ROOT = SCRIPT_DIR.parent

# ---------- 夹具构造 ----------

FILLER = [  # 无逗号长句池（避免章内 ≥40 字连续重复：相邻句不重复、单句 <40 字）
    '空屋里的回声替他数着拍子直到天光从窗缝里退出去为止。',
    '他把抹布搭在肩上继续擦那张没人坐的桌子。',
    '楼下修车摊的气钻声一阵一阵钻进墙里来。',
    '挂钟的秒针走得比他的手快不出多少。',
    '水壶在灶上小声响着像是随时要开口说话。',
    '窗台上的那盆蒜苗又抽出来一指长的新叶。',
    '他把账本翻回第一页从头再数了一遍数目。',
    '门缝底下的风把一张旧传单吹得直打转。',
    '楼道里的灯坏了半个月一直没有人来修。',
    '他把凉透的半杯水端起来又原样放了回去。',
]

DENSE_WHO = ['老周', '阿灿', '陈姨', '小满', '老康', '细妹', '老蒋', '阿禾', '老佟', '春生']
DENSE_WORDS = ['路远', '灯暗', '粮紧', '船慢', '风大', '浪高', '账乱', '人心散', '租重', '价贱', '夜长', '活重']

ENDINGS = [  # 章末句：各章不同、无套路意象、<35 字
    '他把空杯扣在桌上，出门去了。',
    '她拉上卷帘门，闩得很响。',
    '他把号码拨了一半又按灭了。',
    '她把两本账合在一起，压上砖。',
    '他把工牌翻过来，背面朝上。',
]


def dense_sentence(i):
    """构造一句 8 逗号密句（i 为全局序号，保证各句互不相同，避免章内 ≥40 字重复）。"""
    who = DENSE_WHO[i % len(DENSE_WHO)]
    ws = [DENSE_WORDS[(i * 3 + k) % len(DENSE_WORDS)] for k in range(8)]
    return f'{who}说，{ws[0]}，{ws[1]}，{ws[2]}，{ws[3]}，{ws[4]}，{ws[5]}，{ws[6]}，{ws[7]}，都赶在一块儿了。'


def ramp_body(i):
    """第 i 章（1..5）正文：逗号密度随章号单调上升（约 3%→9.4%），总长 ≥500 字。
    用于 S8 趋势闸：不用破折号（避开 #30 硬阈），不用 ≥12% 逗号（避开 #15）。"""
    n_dense = 2 * i
    parts = []
    for k in range(n_dense):
        parts.append(dense_sentence(i * 2 + k))          # 各章各句全局唯一
        parts.append(FILLER[(i * 5 + k * 3) % len(FILLER)])
    for k in range(20):
        parts.append(FILLER[(i * 7 + k * 3) % len(FILLER)])
    parts.append(ENDINGS[i - 1])
    return '\n'.join(parts) + '\n'


def tiny_body():
    return ('客厅的灯只开了一半，茶杯在桌上凉透了。他坐在沙发尽头，手里捏着一张对折的收据，'
            '指腹把纸边磨出了毛。门开了，没有人说话。他先看见那双鞋，然后才看见人。\n')


REPORT_SLOTS_HEADS = ['章节出口', 'OOC', '遮名', '质感', '因果', '目标焦点', '章际', '设定宪法']


def report_unfilled(ch='0001'):
    """8 个必需小节齐全但全部残留模板占位符＿（D-30 应报 未实质填写）。"""
    lines = [f'# 检验报告：第 {ch} 章（selftest S3）', '', '## 0. 结论', '', '- 本章判定：通过', '']
    for kw in REPORT_SLOTS_HEADS:
        lines += [f'## 检验-{kw}', '', f'- {kw}：＿', '']
    lines += ['## 6. 证据清单（evidence_ids）', '',
              '- source: 正文 excerpt: 客厅的灯只开了一半，茶杯在桌上凉', '']
    return '\n'.join(lines) + '\n'


def report_filled(ch='0001'):
    """8 个必需小节齐全且已实质填写（D-30 不应报 未实质填写 / 缺小节）。"""
    lines = [f'# 检验报告：第 {ch} 章（selftest S3 filled）', '', '## 0. 结论', '', '- 本章判定：通过', '']
    for kw in REPORT_SLOTS_HEADS:
        lines += [f'## 检验-{kw}', '', f'- {kw}：成立（他先看见那双鞋，然后才看见人——信息差兑现）。', '']
    lines += ['## 6. 证据清单（evidence_ids）', '',
              '- source: 正文 excerpt: 他先看见那双鞋，然后才看见人', '']
    return '\n'.join(lines) + '\n'


def report_no_evidence(ch='0001'):
    return (f'# 检验报告：第 {ch} 章（selftest）\n\n## 0. 结论\n\n- 本章判定：通过\n')


def report_dual_format(ch='0001'):
    return (f'# 检验报告：第 {ch} 章（selftest D-29）\n\n'
            '## 6. 证据清单（evidence_ids）\n\n'
            '- source: 正文 excerpt: 客厅的灯只开了一半，茶杯在桌上凉\n'
            '- source: 上章末\n'
            '  excerpt: 这一句只存在于上一章，本章正文里必然找不到\n')


CONFIG = ('{\n  "title": "selftest",\n  "target_word_count": 3000,\n'
          '  "body_filename_template": "第{ch}章 {title}.md",\n  "body_dir": "正文",\n  "modules": {}\n}\n')

TRUTH_FILES = ['characters', 'world', 'hooks', 'relationships', 'objects', 'timeline']

# world.md 夹具：含 v2.1.3 的【当前状态】区块（无它 → 世界时钟检查无处可判）
WORLD_TPL = ('# world\n\n'
             '## 当前状态（每章更新）\n\n'
             '### 时间\n'
             '- 故事起点：第一章\n'
             '- 当前进度：第 {ch} 章 / 自测占位\n\n'
             '### 地点\n- 主场景：占位\n\n'
             '### 环境\n- 天气：晴\n')

# 作者身份档案夹具（v2.1.4 #29c）
AUTHOR_BASE = ('# 作者身份档案（项目级 · selftest）\n\n'
               '一句话卖点：自测占位卖点，用于门禁回归夹具。\n'
               '目标读者：自测占位读者群，年龄跨度与题材偏好均为占位。\n'
               '写作边界：自测占位边界，不写与本章冲突链无关的内容。\n'
               '叙述人称：第三人称限知，跟随主角。\n'
               '句法倾向：短句为主，动词先行，心理靠外部动作呈现。\n')

AUTHOR_VOICE_GOOD = AUTHOR_BASE + (
    '样本段: |\n'
    '  电梯到七楼，门开了又合上。他站着没动，指节抵在不锈钢壁上，凉。\n'
    '  走廊尽头的灯管坏了两格，一明一灭，把她的影子拉到墙上又收回来。\n'
    '  他想起早上出门时她说过的话，随即又把它按回去。想这些没用。\n'
    '  办公室的门半掩着，里面有人在笑，笑声隔着一层石膏板，像从水底传上来。\n'
    '  他把手从壁上挪开，往那边走。鞋跟敲地砖的声音规律得让他自己都觉得假。\n')

AUTHOR_VOICE_TEMPLATE = AUTHOR_BASE + (
    '样本段: |\n'
    '  （粘贴 200-400 字本项目成稿，作为声音基准。\n'
    '   取样三条硬口径，粘错了本区等于没填：\n'
    '   1. 主体必须是叙述/描写/动作段 —— 引号内台词占比 ≤ 1/3。\n'
    '   2. 挑常态段，不要挑高潮段 —— 高潮段句式会变形，拿它当基准会让全书一直紧绷。\n')

AUTHOR_VOICE_DIALOG = AUTHOR_BASE + (
    '样本段: |\n'
    '  "你把咖啡洒了。"她把文件往桌角一推。\n'
    '  "对不起，"他说，"我马上擦。"\n'
    '  "擦？"她笑了一声，"你知道这份文件要几份吗？"\n'
    '  "我知道。"他抽出纸巾，"三份，楼下印。"\n'
    '  "两份已经废了。"她站起来，"你今天第几次了？"\n'
    '  "第三次。"他说。\n')

# 声线漂移夹具（v2.1.6 #29d）：AUTHOR_VOICE_GOOD 基线 = 17 字/句，阈值 = >25.5 且差 ≥5。
# 两段正文**字数相当、内容无关**，唯一差别是句长——这不是文学样本，是量尺。
SHORT_SENTENCE_BODY = '\n'.join([
    '他推开门。屋里没人。灯还亮着。',
    '桌上有杯水。水是凉的。杯壁挂着一层雾。',
    '窗外的雨停了。楼下有人在喊。喊了三声。',
    '他把包放下。坐了一会儿。没有动静。',
    '墙上挂着一张照片。照片里是两个人。他都认识。',
    '电话响了。他没接。响到第六声停了。',
    '他起身。走到窗边。玻璃上有道裂纹。',
    '街上很静。路灯坏了两盏。地上有一滩水。',
    '他想起上午的事。随即又把它按回去。想这些没用。',
    '门开了。她站在门口。肩上有一点湿。',
    '他没说话。她也没说。两个人就这样站着。',
    '过了几秒。她把手上的袋子放下。袋子里有声响。',
    '他终于开口。问她吃没吃饭。她说吃了。',
    '他没再问。转身去厨房。水开了他就关了火。',
    '屋里只剩下水声。窗外又开始下雨。',
] * 4) + '\n'      # ×4 只为凑够 500 字触发判定（短章不判）

LONG_SENTENCE_BODY = '\n'.join([
    '他推开门之后发现屋子里空无一人，只有那盏灯还亮着，光线落在地板上，把桌腿的影子拉得很长很长。',
    '桌上放着一杯已经凉透了的水，杯壁上挂着一层薄薄的水雾，看起来已经在这里放了相当长的一段时间。',
    '窗外的雨已经停了，楼下不知道谁在喊着什么，喊了三声之后就没有了动静，只剩下湿漉漉的街道。',
    '他把背包从肩上卸下来放在椅子上，然后坐了一会儿，屋子里安静得能听见冰箱在墙角发出的低鸣。',
    '墙上挂着一张照片，照片里是两个并肩站着的人，他都认识，只是已经很久没有和他们联系过了。',
    '电话在这个时候响了起来，他没有伸手去接，铃声在安静的房间里一直响到第六声才彻底停下来。',
    '他从椅子上站起身，慢慢走到窗边，看见玻璃上有一道不知道什么时候留下的裂纹，从右上角延伸下来。',
    '街上一个行人也没有，路灯坏了两盏，剩下的那几盏把地上的一滩积水照得发亮，偶尔有车经过。',
    '他忽然想起上午发生的那件事，随即又把它按了回去，因为他很清楚现在想这些是没有任何用处的。',
    '门在这个时候被推开了，她站在门口，肩膀上有一点被雨水打湿的痕迹，头发贴在额角上。',
    '他没有说话，她也没有开口，两个人就这样隔着几步的距离站着，谁都没有先迈出那一步。',
    '过了几秒钟之后她才把手里提着的袋子放到地上，袋子里发出一阵轻微的声响，像是玻璃碰在一起。',
    '他终于开口了，问她有没有吃过饭，她说吃过了，声音很轻，像是隔着一层什么东西传过来的。',
    '他没有继续追问下去，而是转身走进了厨房，等水烧开的时候顺手把火关掉了，动作很熟练。',
    '屋子里最后只剩下水在壶里翻滚的声音，窗外的雨不知道什么时候又开始下了起来。',
] * 2) + '\n'

TICK_BLOCK = ('<!-- WORLD-TICK-START -->\n'
              '- clock: 0001 | 周一 早 → 周一 晚 | 半天\n'
              '- place: 主场景=占位地点\n'
              '- env: 天气=晴\n'
              '- loc: 占位地点 | intact | - | 无\n'
              '- event: 周一 晚 | 自测世界推进事件 | 自测影响\n'
              '<!-- WORLD-TICK-END -->\n')


class Proj:
    """最小项目夹具构建器。"""

    def __init__(self, base):
        self.root = Path(base)
        for d in ['正文', '大纲', '设定', '素材池', '叙事总览', '配置/身份',
                  '故事/真相', '故事/元数据', '故事/日志']:
            (self.root / d).mkdir(parents=True, exist_ok=True)
        (self.root / 'novel-config.json').write_text(CONFIG, encoding='utf-8')
        for t in TRUTH_FILES:
            (self.root / '故事/真相' / f'{t}.md').write_text(f'# {t}\n\n（selftest 占位）\n', encoding='utf-8')
        self._clock = '0000'
        self.set_world(WORLD_TPL.format(ch='0000'))

    def body(self, ch, text=None):
        (self.root / '正文' / f'第{ch}章 测试.md').write_text(text or tiny_body(), encoding='utf-8')
        # 夹具也要遵守契约：正文写到哪一章，世界时钟就跟到哪一章（等价于跑过 world_tick）
        if ch > self._clock:
            self._clock = ch
            self.set_world(WORLD_TPL.format(ch=ch))

    def set_world(self, text):
        (self.root / '故事/真相' / 'world.md').write_text(text, encoding='utf-8')

    def author_voice(self, text=None):
        """写 配置/身份/作者.md（v2.1.4 #29c 夹具）。"""
        t = AUTHOR_BASE if text is None else text
        (self.root / '配置' / '身份' / '作者.md').write_text(t, encoding='utf-8')

    def index(self, rows):
        lines = ['# 章节索引', '', '| 章号 | 标题 | 状态 |', '|------|------|------|']
        lines += [f'| {ch} | 测试 | {st} |' for ch, st in rows]
        (self.root / '故事/元数据' / 'index.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def outline(self, ch, text=None):
        (self.root / '大纲' / f'细纲_第{ch}章.md').write_text(
            text or f'# 细纲：第 {ch} 章\n\n- 冲突链：占位\n', encoding='utf-8')

    def chapter_meta(self, ch):
        (self.root / '故事/元数据' / f'chapter_{ch}.md').write_text(
            f'# chapter_{ch}\n\n- change_summary：selftest 占位。\n', encoding='utf-8')

    def report(self, ch, text):
        (self.root / '故事/元数据' / f'检验报告_第{ch}章.md').write_text(text, encoding='utf-8')

    def change_report(self, ch):
        (self.root / '故事/日志' / f'change_report_第{ch}章.md').write_text(
            f'# change_report 第{ch}章\n\n本章自测占位：角色无变化，伏笔无推进，时间线推进一天，'
            '关系无变化，物品无变化，世界观无变化。全部字段为回归夹具填充内容，不构成真实章节产物。\n' * 2,
            encoding='utf-8')

    def change_report_tick(self, ch, block=TICK_BLOCK):
        """往现有 change_report 追加 WORLD-TICK 区（模拟 S4 填了世界推进五行）。"""
        f = self.root / '故事/日志' / f'change_report_第{ch}章.md'
        f.write_text(f.read_text(encoding='utf-8') + '\n' + block, encoding='utf-8')

    def flag(self, name, content='0001\n'):
        (self.root / '故事/日志' / name).write_text(content, encoding='utf-8')

    def hooks(self, text):
        (self.root / '故事/真相' / 'hooks.md').write_text(text, encoding='utf-8')

    def shell_meta(self, ch):
        (self.root / '故事/元数据' / f'chapter_{ch}.md').write_text(f'# chapter_{ch}\n', encoding='utf-8')

    def full_chapter(self, ch, status='archived', body=None, report_text=None):
        self.body(ch, body)
        self.outline(ch)
        self.chapter_meta(ch)
        self.change_report(ch)
        if report_text is not None:
            self.report(ch, report_text)
        self.index([(ch, status)])


# ---------- 运行与断言 ----------

def run_verify(root, scope):
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    p = subprocess.run([sys.executable, str(VERIFY), '--root', str(root), '--scope', scope],
                       capture_output=True, env=env, cwd=str(SKILL_ROOT))
    out = p.stdout.decode('utf-8', errors='replace')
    return p.returncode, out


def run_world_tick(root, apply):
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    cmd = [sys.executable, str(WORLD_TICK), '--root', str(root)]
    if apply:
        cmd.append('--apply')
    p = subprocess.run(cmd, capture_output=True, env=env, cwd=str(SKILL_ROOT))
    return p.returncode, p.stdout.decode('utf-8', errors='replace')


def find_line(out, mark, name_substr):
    """找形如 '  [FAIL] <name> — detail' 且 name/detail 含 name_substr 的行。"""
    pat = re.compile(rf'^\s+\[{mark}\]\s+(.+)$', re.M)
    for m in pat.finditer(out):
        if name_substr in m.group(1):
            return m.group(0).strip()
    return None


class Asserts:
    def __init__(self):
        self.results = []   # (ok, 描述, 证据行)

    def expect(self, out, mark, name_substr, desc):
        line = find_line(out, mark, name_substr)
        self.results.append((line is not None, desc, line or f'（未找到 [{mark}] 含“{name_substr}”的行）'))

    def expect_absent(self, out, substr, desc):
        hit = next((l.strip() for l in out.splitlines() if substr in l and l.strip().startswith('[')), None)
        self.results.append((hit is None, desc, hit or f'（输出中无“{substr}”）'))


SCENARIOS = []


def scenario(fn):
    SCENARIOS.append(fn)
    return fn


@scenario
def s1_evidence_wiring(base, a, verbose):
    """D-28：#8 必须在 settle/batch 生效；缺证据 FAIL → legacy 旗 WARN → 补证 PASS。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_no_evidence())
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', 'evidence_ids校验', 'S1.1 settle 对缺 evidence 报告 FAIL')
    p.flag('legacy-no-evidence.flag')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', 'evidence_ids校验', 'S1.2 legacy-no-evidence.flag 命中转 WARN')
    a.expect_absent(out, '[FAIL] evidence_ids校验', 'S1.3 豁免后不再 FAIL')
    p.report('0001', report_filled())
    (p.root / '故事/日志/legacy-no-evidence.flag').unlink()
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', 'evidence_ids校验', 'S1.4 补 §6 证据后 PASS')


@scenario
def s2_dual_format_crossfile(base, a, verbose):
    """D-29：同行+分行双格式解析；跨文件（上章末）引用不得误报“未能在正文逐字定位”。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_dual_format())
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', 'evidence_ids校验', 'S2.1 双格式条目解析 PASS')
    a.expect_absent(out, '未能在正文逐字定位', 'S2.2 上章末跨文件引用不产生定位 WARN')


@scenario
def s3_slots_placeholder(base, a, verbose):
    """D-30：小节齐全但残留＿ → #27 WARN 未实质填写；实质填写后不再报。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_unfilled())
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', 'change_report充实度(#27)', 'S3.1 占位符未填写被 #27 报警')
    a.expect(out, 'WARN', '未实质填写', 'S3.2 报警注明未实质填写')
    p.report('0001', report_filled())
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', 'change_report充实度(#27)', 'S3.3 实质填写后 #27 PASS')
    a.expect_absent(out, '未实质填写', 'S3.4 填写后不再报未实质填写')


@scenario
def s4_report_missing(base, a, verbose):
    """D-01 回归：archived 缺检验报告 FAIL；legacy-no-review.flag 豁免转 WARN。"""
    p = Proj(base)
    p.body('0001')
    p.outline('0001')
    p.chapter_meta('0001')
    p.change_report('0001')
    p.index([('0001', 'archived')])
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', '检验报告完整性(#16)', 'S4.1 archived 缺报告 FAIL')
    p.flag('legacy-no-review.flag')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '检验报告完整性(#16)', 'S4.2 legacy-no-review.flag 豁免转 WARN')


@scenario
def s5_settle_consistency(base, a, verbose):
    """D-04 家族回归：archived 三件套齐全 PASS；缺 change_report FAIL。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_filled())
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', '落库一致性(index↔报告↔正文)', 'S5.1 三件套齐全 PASS')
    (p.root / '故事/日志/change_report_第0001章.md').unlink()
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', '落库一致性(index↔报告↔正文)', 'S5.2 archived 缺 change_report FAIL')


@scenario
def s6_hooks_duplicate(base, a, verbose):
    """D-05 回归：hooks ID 重复 = FAIL（唯一性口径）。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_filled())
    p.hooks('# hooks\n\n| 伏笔ID | 埋设章 | 推进状态 |\n|--------|--------|----------|\n'
            '| h_001 | 0001 | active |\n| h_001 | 0001 | active |\n')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', 'hooks唯一性', 'S6.1 hooks ID 重复 FAIL')


@scenario
def s7_shells_and_gap(base, a, verbose):
    """D-06 回归：未来章元数据空壳 ≥10 FAIL / 1-9 WARN；正文跳号 FAIL。"""
    p = Proj(base)
    p.body('0001')
    for i in range(5, 15):
        p.shell_meta(f'{i:04d}')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', '批跑章号连续/落库断链(#32)', 'S7.1 10 个未来空壳 FAIL(批量预生成)')
    for i in range(7, 15):
        (p.root / '故事/元数据' / f'chapter_{i:04d}.md').unlink()
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '批跑章号连续/落库断链(#32)', 'S7.2 2 个空壳降为 WARN')
    p.body('0003')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', '批跑章号连续/落库断链(#32)', 'S7.3 正文 0001→0003 跳号 FAIL')


@scenario
def s8_batch_trend(base, a, verbose):
    """D-07 回归：逗号密度 5 章单调爬升 → batch FAIL 停机 / trend WARN。"""
    p = Proj(base)
    for i in range(1, 6):
        p.body(f'{i:04d}', ramp_body(i))
    _, out = run_verify(p.root, 'batch')
    a.expect(out, 'FAIL', '退化趋势', 'S8.1 batch 对连续5章爬升 FAIL 停机')
    # 退化趋势的 detail 是多行（曲线表+停机信号），"连续5章爬升"落在后续行——按全文检索
    a.results.append(('连续5章爬升' in out and 'batch 停机' in out,
                      'S8.2 停机原因是 trend_b（连续爬升触发 batch 停机）',
                      '输出含 连续5章爬升=%s, batch 停机=%s' % ('连续5章爬升' in out, 'batch 停机' in out)))
    _, out = run_verify(p.root, 'trend')
    a.expect(out, 'WARN', '退化趋势', 'S8.3 trend scope 同曲线仅 WARN')


@scenario
def s9_world_clock(base, a, verbose):
    """v2.1.3 世界时钟：时钟停旧章 FAIL；同步则 PASS；缺当前进度行 FAIL；老格式只 WARN 不并列 PASS。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_filled())
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', '世界时钟', 'S9.1 世界时钟与最新落库章同步 → PASS')

    # 模拟「没跑 world_tick」：时钟退回 0000，正文/索引已在 0001
    p.set_world(WORLD_TPL.format(ch='0000'))
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', '世界时钟', 'S9.2 时钟停在 0000 章 < 最新 0001 章 → FAIL')

    # 有区块但缺「当前进度」行 = world_tick 无处写入
    p.set_world('# world\n\n## 当前状态（每章更新）\n\n### 时间\n- 故事起点：第一章\n')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'FAIL', '世界时钟', 'S9.3 缺「当前进度」行 → FAIL')

    # 老格式 world.md：只 WARN，且**不许同时并列一条 PASS**（两条自相矛盾 = 比没有检查更糟）
    p.set_world('# world\n\n- 现实：普通职场。\n')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '世界时钟', 'S9.4 老格式 world.md → WARN 提示未接入自动推进')
    a.expect_absent(out, '[PASS] 世界时钟', 'S9.5 老格式不并列输出 PASS（防自相矛盾结论）')


@scenario
def s10_world_tick_writer(base, a, verbose):
    """v2.1.3 写入器↔检查器配对：缺 WORLD-TICK 退出码 2；填了→推进→settle PASS；重复跑幂等。"""
    p = Proj(base)
    p.full_chapter('0001', report_text=report_filled())
    p.set_world(WORLD_TPL.format(ch='0000'))

    rc, out = run_world_tick(p.root, apply=False)
    a.results.append((rc == 2, 'S10.1 无 WORLD-TICK 区 → world_tick 退出码 2', f'rc={rc}'))

    p.change_report_tick('0001')
    rc, out = run_world_tick(p.root, apply=False)
    a.results.append((rc == 0 and 'dry-run' in out, 'S10.2 默认 dry-run 不写盘',
                      f'rc={rc}, 含dry-run={"dry-run" in out}'))
    a.results.append(('缺 WORLD-TICK' not in out, 'S10.3 有 WORLD-TICK 时不再报缺失',
                      out.strip().splitlines()[-1] if out.strip() else '(空输出)'))

    rc, out = run_world_tick(p.root, apply=True)
    a.results.append((rc == 0 and '已写盘' in out, 'S10.4 --apply 写盘成功', f'rc={rc}'))

    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', '世界时钟', 'S10.5 写入器推进后 检查器 PASS（两者必须配对）')

    # 幂等：第二次跑不应再 insert（timeline 按章号去重）
    rc, out2 = run_world_tick(p.root, apply=True)
    a.results.append(('第0001章行已存在' in out2, 'S10.6 重复跑幂等（timeline 按章号去重，不重复追加）',
                      [l.strip() for l in out2.splitlines() if 'timeline' in l][:1] or '(无 timeline 行)'))


@scenario
def s11_author_voice_sample(base, a, verbose):
    """v2.1.4 #29c 作者声音样本：缺失/模板原文/全是台词 → WARN；真实叙述段 → 不报。
    （这条闸治的是：把角色声线当成作者声线粘进来，或把模板原文当成已填。）"""
    p = Proj(base)
    _, out = run_verify(p.root, 'init')
    a.expect(out, 'WARN', '作者声音样本(#29c)', 'S11.1 未建 配置/身份/作者.md → WARN')

    p.author_voice(AUTHOR_VOICE_TEMPLATE)
    _, out = run_verify(p.root, 'init')
    a.expect(out, 'WARN', '作者声音样本(#29c)', 'S11.2 样本段仍是模板原文 → WARN')
    a.results.append(('模板原文' in out, 'S11.3 报警指明是模板原文（不是笼统的"缺失"）',
                      find_line(out, 'WARN', '作者声音样本') or '(无)'))

    p.author_voice(AUTHOR_VOICE_DIALOG)
    _, out = run_verify(p.root, 'init')
    a.expect(out, 'WARN', '作者声音样本(#29c)', 'S11.4 样本段台词占比 >1/3 → WARN（那是角色声线）')
    a.results.append(('台词占比' in out, 'S11.5 报警给出占比数字，指明粘错成角色声线',
                      find_line(out, 'WARN', '作者声音样本') or '(无)'))

    p.author_voice(AUTHOR_VOICE_GOOD)
    _, out = run_verify(p.root, 'init')
    a.expect_absent(out, '作者声音样本(#29c)', 'S11.6 真实叙述样本 → 不再报（WARN 只真命中才发声）')


@scenario
def s12_voice_drift(base, a, verbose):
    """v2.1.6 #29d 声线漂移：正文句长中位数 比 样本段基线 高出 50% → WARN。
    关键是正负向都要有——只测正向的话，恒定 PASS 的检查器根本发现不了是瞎的。"""
    p = Proj(base)
    p.author_voice(AUTHOR_VOICE_GOOD)          # 短句叙述段 → 基线约 6-8 字
    p.body('0001', SHORT_SENTENCE_BODY)        # 同风格短句正文 → 不该报
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'PASS', '声线漂移(#29d)', 'S12.1 正文句长贴近样本基线 → 不报')

    p.body('0002', LONG_SENTENCE_BODY)         # 长句连缀（AI 腔典型形态）→ 该报
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '声线漂移(#29d)', 'S12.2 正文句长 > 基线1.5倍 → WARN')
    a.results.append(('0002' in out, 'S12.3 报警指明是哪一章（不是笼统说"有漂移"）',
                      find_line(out, 'WARN', '声线漂移') or '(无)'))

    # 边界：短章不判（<500 字），否则半成品会被误伤。
    # 断言必须只看漂移那一行——out 里别处也会出现章号（落库一致性等），
    # 写 '0003' not in out 会把别的检查的章号当成漂移告警。
    p.body('0003', '短。')
    _, out = run_verify(p.root, 'settle')
    line = find_line(out, 'WARN', '声线漂移') or ''
    a.results.append(('0003' not in line, 'S12.4 短章(<500字)不参与漂移判定（防误伤半成品）',
                      line.strip() or '(无漂移告警行)'))

    # 无样本基线时：不重复报 #29c 的缺，但也不能假装"检查通过"。
    # （必须复用同一项目——另建 Proj 若共用 base 目录，0002 长章还在，会误判成"仍在报"）
    p.author_voice(AUTHOR_BASE)          # 只留档案头，抽掉样本段
    _, out = run_verify(p.root, 'settle')
    # 注意：无基线时本项**故意留一条 PASS+说明**，不是不出现——
    # 静默跳过 = 又一个"没有可报错的地方"。所以断言是"无 WARN 行"，不是"无此行"。
    wline = find_line(out, 'WARN', '声线漂移') or ''
    a.results.append((wline == '', 'S12.5 无样本基线 → 不报 WARN（缺样本归 #29c，不重复报）',
                      wline.strip() or '(无 WARN 行)'))
    pline = find_line(out, 'PASS', '声线漂移') or ''
    a.results.append(('跳过' in pline, 'S12.6 跳过时必须写明原因（不静默 PASS）',
                      pline.strip() or '(无)'))


# 细纲夹具（v2.1.8 S13）：三种「引号 + 道」的组合，区分误报与真报
OUTLINE_NO_DIALOGUE_TAOIST = (
    '# 细纲：第 0001 章\n\n'
    '| 事实层 | 老道士知道那个"有人代为回应"的现象意味着什么；铜钱碎是崩坏前兆 |\n'
    '- 老道士：知道那个"有人代为回应"的现象意味着什么；不知道林枫会不会回头\n'
)
OUTLINE_DIALOGUE_SAID = (
    '# 细纲：第 0001 章\n\n'
    '- 节四：他说"这句是完整台词不该出现在细纲"\n'
)
OUTLINE_DIALOGUE_TAOIST_SAID = (
    '# 细纲：第 0001 章\n\n'
    '- 节四：老道士说道"这句也是完整台词"\n'
)


@scenario
def s13_outline_dialogue_false_positive(base, a, verbose):
    """v2.1.8 细纲台词越界：真台词要抓，复合词里的「道」不许误报。

    真书实测（梦里叫主人）才暴露的误报：细纲写
        「老道士知道那个"有人代为回应"的现象」
    「老道士」的道 + 「知道」的道，两处都被当成说话动词 → 误报。
    夹具里不会有人叫「老道士」，所以夹具测试永远发现不了。
    """
    p = Proj(base)

    # 误报侧：含「老道士」「知道」的复合词，引号里不是台词 → 不该报
    p.outline('0001', OUTLINE_NO_DIALOGUE_TAOIST)
    _, out = run_verify(p.root, 'settle')
    wline = find_line(out, 'WARN', '细纲台词越界') or ''
    a.results.append((wline == '', 'S13.1 复合词含「道」（老道士/知道）→ 不误报',
                      wline.strip() or '(无 WARN 行)'))

    # 真报侧1：他说 + 台词
    p.outline('0001', OUTLINE_DIALOGUE_SAID)
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '细纲台词越界', 'S13.2 他说"…" 真台词 → 必须报')

    # 真报侧2：老道士说道 + 台词（"道士"要被右断言排除，但"说道"不是"道士"）
    p.outline('0001', OUTLINE_DIALOGUE_TAOIST_SAID)
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '细纲台词越界', 'S13.3 老道士说道"…" → 仍要报（不能因挡误报而失效）')


# 禁用词夹具（v2.1.9 S14）
# 分两行 + 代码块围栏两种写法，验证「块写在 ``` 里也能解析」以及「多行都要解析到」
AUTHOR_BAN_NONE = AUTHOR_VOICE_GOOD + '\n写作边界：自测占位边界，未启用禁用清单。\n'

AUTHOR_BAN_LIST = AUTHOR_VOICE_GOOD + (
    '禁用清单:\n'
    '  不由得  不禁  意味深长\n'
    '  淡淡的笑  苦笑\n')

# 围栏里的清单：验证 ``` 不当成"块结束"（否则清单写在代码块里会静默失效）
AUTHOR_BAN_FENCED = AUTHOR_VOICE_GOOD + (
    '禁用清单:\n'
    '```\n'
    '  轻笑一声  嘴角上扬\n'
    '```\n')

# 模板默认值的坑：`- 由本项目定` 若被当成真清单，会造出一个"永不命中的假清单"，
# 检查永远 PASS 且永远没意义 —— 必须被占位词过滤器清掉
AUTHOR_BAN_PLACEHOLDER = AUTHOR_VOICE_GOOD + (
    '禁用清单:\n'
    '  - 由本项目定\n')

BAN_CLEAN_BODY = '\n'.join([
    '他推开门。屋里没人。灯还亮着。',
    '桌上有杯水。水是凉的。杯壁挂着一层雾。',
    '他把包放下。坐了一会儿。没有动静。',
] * 5) + '\n'

BAN_DIRTY_BODY = '\n'.join([
    '他推开门。屋里没人。灯还亮着。',
    '他不由得想起上午的事，随即又把它按回去。',
    '她落下那句话，意味深长地看着他。',
    '想到这里他苦笑了一下，转身去把窗帘拉上。',
    '他不明白，也不想明白。窗外的雨又开始下了。',
] * 5) + '\n'


@scenario
def s14_banned_words(base, a, verbose):
    """v2.1.9 #29e 禁用词：清单是人写的，闸门是机器盯的。

    这道闸的存在理由很直白：此前「禁用清单」是作者档案里一张只给人看的表格，
    机器从不读它 —— "写了清单"和"没写清单"对产出零差别。**人写的规则机器不读 = 规则等于不存在。**
    所以这里必须测三件事：不启用清单要写明跳过（不许静默 PASS）、命中要指明词和章号、
    围栏和多行都不能让清单漏解析。
    """
    p = Proj(base)

    p.author_voice(AUTHOR_BAN_NONE)
    p.body('0001', BAN_CLEAN_BODY)
    _, out = run_verify(p.root, 'settle')
    wline = find_line(out, 'WARN', '禁用词') or ''
    a.results.append((wline == '', 'S14.1 未启用禁用清单 → 不报 WARN（写文档≠启用）',
                      wline.strip() or '(无 WARN 行)'))
    pline = find_line(out, 'PASS', '禁用词') or ''
    a.results.append(('未启用' in pline, 'S14.2 未启用时 PASS 必须写明跳过原因（不静默）',
                      pline.strip() or '(无)'))

    p.author_voice(AUTHOR_BAN_LIST)
    p.body('0001', BAN_DIRTY_BODY)
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '禁用词(#29e)', 'S14.3 正文含禁用词 → WARN')
    wline = find_line(out, 'WARN', '禁用词') or ''
    a.results.append(('0001' in wline, 'S14.4 报警指明章号（不是笼统说"有命中"）',
                      wline.strip() or '(无)'))
    a.results.append(('不由得' in wline and '×' in wline,
                      'S14.5 报警给出「词×次数」（让人判断改正文还是改清单）',
                      wline.strip() or '(无)'))
    # 第二行的词也要解析到 —— 只收第一行 = 又一处恒定漏报
    a.results.append(('苦笑' in wline, 'S14.6 清单写在第二行的词也被解析（多行不漏）',
                      wline.strip() or '(无)'))

    p.body('0001', BAN_CLEAN_BODY)
    _, out = run_verify(p.root, 'settle')
    wline = find_line(out, 'WARN', '禁用词') or ''
    a.results.append((wline == '', 'S14.7 干净正文 → 不报（WARN 只真命中才发声）',
                      wline.strip() or '(无 WARN 行)'))

    p.author_voice(AUTHOR_BAN_FENCED)
    p.body('0001', '\n'.join([
        '他推开门。屋里没人。灯还亮着。',
        '她嘴角上扬，轻笑一声，随即又恢复了那副表情。',
    ] * 5) + '\n')
    _, out = run_verify(p.root, 'settle')
    a.expect(out, 'WARN', '禁用词(#29e)',
             'S14.8 清单写在 ``` 围栏里也能解析（围栏不是块结束）')

    p.author_voice(AUTHOR_BAN_PLACEHOLDER)
    _, out = run_verify(p.root, 'settle')
    pline = find_line(out, 'PASS', '禁用词') or ''
    a.results.append(('未启用' in pline,
                      'S14.9 模板默认占位「- 由本项目定」不算启用清单（防幽灵清单）',
                      pline.strip() or find_line(out, 'WARN', '禁用词') or '(无)'))


# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser(description='Novel Engine 门禁回归自测（D-31）')
    ap.add_argument('-v', '--verbose', action='store_true', help='打印每场景 verify 关键输出行')
    ap.add_argument('--keep', action='store_true', help='保留临时夹具目录（默认自行清理）')
    args = ap.parse_args()

    tmp_root = tempfile.mkdtemp(prefix='ne_selftest_')
    total_ok = 0
    total_bad = 0
    print(f'=== Novel Engine 门禁回归自测（{len(SCENARIOS)} 场景）===')
    try:
        for fn in SCENARIOS:
            a = Asserts()
            base = os.path.join(tmp_root, fn.__name__)
            os.makedirs(base, exist_ok=True)
            fn(base, a, args.verbose)
            ok_n = sum(1 for ok, _, _ in a.results if ok)
            bad = [(d, e) for ok, d, e in a.results if not ok]
            total_ok += ok_n
            total_bad += len(bad)
            status = 'PASS' if not bad else 'NG'
            print(f'[{status}] {fn.__name__}  ({ok_n}/{len(a.results)} 断言)')
            for ok, desc, ev in a.results:
                if args.verbose or not ok:
                    print(f'    {"✓" if ok else "✗"} {desc}')
                    if not ok or args.verbose:
                        print(f'      → {ev[:160]}')
        print(f'--- 断言 {total_ok} 通过 / {total_bad} 失败 ---')
        if total_bad:
            print('结论: NG — 门禁行为回归，禁止发版。')
            return 1
        print('结论: OK — 门禁行为与登记预期一致。')
        return 0
    finally:
        if args.keep:
            print(f'（夹具保留于 {tmp_root}）')
        else:
            shutil.rmtree(tmp_root, ignore_errors=True)  # 仅清理本脚本自建的临时目录


if __name__ == '__main__':
    sys.exit(main())
