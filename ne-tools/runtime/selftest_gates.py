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

    def body(self, ch, text=None):
        (self.root / '正文' / f'第{ch}章 测试.md').write_text(text or tiny_body(), encoding='utf-8')

    def index(self, rows):
        lines = ['# 章节索引', '', '| 章号 | 标题 | 状态 |', '|------|------|------|']
        lines += [f'| {ch} | 测试 | {st} |' for ch, st in rows]
        (self.root / '故事/元数据' / 'index.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def outline(self, ch):
        (self.root / '大纲' / f'细纲_第{ch}章.md').write_text(f'# 细纲：第 {ch} 章\n\n- 冲突链：占位\n', encoding='utf-8')

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
