#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
world_tick.py —— 世界状态自动推进（v2.1.3）
=========================================
把「写完一章 → 手改 world.md + timeline.md」改成机器推进。

为什么需要：
  世界状态（时间 / 地点 / 环境 / 地点状态机）以前靠 S4 档案员读 Change Report 手工改写，
  一处事件要在 world.md 时间线大事记和 timeline.md 里写两遍 —— 手写两遍的必然结果是：
  滞后（懒得补）、漂移（两处对不上）、漏更（忘了写）。门禁查不出"忘了写"，
  因为缺的那行根本不产生任何可报错的东西。

做法：Change Report 里划一块机器可解析的 WORLD-TICK 区，本脚本解析后分发：
  - timeline.md   ← 事件行（章号去重，唯一真相源）
  - world.md      ← 【当前状态】时间/地点/环境 + 【地点状态机】upsert
  world.md 不再重复登记时间线大事记（已改指回 timeline.md），事件只写一处。

用法：
  python runtime/world_tick.py --root <项目根> [--chapter 0001] [--apply] [--quiet]

  --chapter 不传 = 处理全部已找到 WORLD-TICK 的章（按章号升序）
  默认 dry-run（只打印计划，不动盘），--apply 才写盘。
  幂等：同章重复跑不产生重复行（timeline 按章号去重、地点按名 upsert、当前状态覆盖）。

五行协议（写在 Change Report 的 WORLD-TICK 区里）：
  - clock:  0001 | 三月十二 晨 → 三月十三 夜 | 1天
  - place:  主场景=青云宗外门 ｜ 新解锁=后山禁地
  - env:    天气=小雨 ｜ 季节=春 ｜ 特殊状态=战时戒严
  - loc:    青云宗外门 | destroyed | 焚毁于魔族夜袭 | 遗留：剑胎残片
  - event:  三月十三 夜 | 魔族夜袭外门 | 外门建制瓦解

退出码：0=有推进或无需推进  1=参数/路径错误  2=有章缺 WORLD-TICK 区
"""
import argparse
import os
import re
import sys

TICK_START = '<!-- WORLD-TICK-START -->'
TICK_END = '<!-- WORLD-TICK-END -->'

# 行首： - clock: xxx   （兼容 * 开头、中文冒号）
LINE_RE = re.compile(r'^\s*[-*]\s*(clock|place|env|loc|event)\s*[:：]\s*(.+?)\s*$')
# 段分隔：半角 | 与全角 ｜ 都认（中文输入下极易混用）
SEP_RE = re.compile(r'\s*[|｜]\s*')
KV_RE = re.compile(r'^\s*([^=：]{1,10})\s*[=：]\s*(.+?)\s*$')

# 地点状态机合法枚举（与 world.md 模板一致）
LOC_PHASES = ('intact', 'damaged', 'destroyed', 'abandoned', 'rebuilt', 'transformed')

REPORT_GLOBS = (
    ('故事', 'reports'),
    ('故事', '日志'),
    ('故事', '元数据'),
)


def chap4(x):
    s = re.sub(r'\D', '', str(x or ''))
    return s.zfill(4) if s else ''


def read_text(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        return f.read()


def write_text(path, txt):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)


def find_report_files(root):
    """返回 [(章号, 路径)]，按章号+路径排序。"""
    out = []
    for parts in REPORT_GLOBS:
        d = os.path.join(root, *parts)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.md'):
                continue
            m = re.search(r'(\d{3,4})', fn)
            if not m:
                continue
            out.append((chap4(m.group(1)), os.path.join(d, fn)))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def parse_tick(text):
    """抽出 WORLD-TICK 区并解析为结构化 dict。区不存在返回 None。"""
    s = text.find(TICK_START)
    if s < 0:
        return None
    e = text.find(TICK_END, s)
    body = text[s + len(TICK_START):e if e > 0 else len(text)]
    tick = {'clock': [], 'place': [], 'env': [], 'loc': [], 'event': []}
    for line in body.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        kind, payload = m.group(1), m.group(2)
        segs = [x.strip() for x in SEP_RE.split(payload) if x.strip()]
        if kind in ('clock', 'loc', 'event'):
            tick[kind].append(segs)
        else:  # place/env：k=v 形式
            kv = []
            for seg in segs:
                km = KV_RE.match(seg)
                if km:
                    kv.append((km.group(1).strip(), km.group(2).strip()))
            tick[kind].append(kv)
    if not any(tick.values()):
        return None
    return tick


def clock_end(clock_segs):
    """clock 第 2 段是『起 → 止』，取止；无箭头则取整段。"""
    if len(clock_segs) < 2:
        return ''
    span = clock_segs[1]
    for arrow in ('→', '->', '=>', '至', '到'):
        if arrow in span:
            return span.split(arrow)[-1].strip()
    return span.strip()


# ---------- world.md 区块操作 ----------

def section_range(lines, *keys):
    """定位标题含任一 key 的 ## 区块，返回 (起, 止) 或 None。"""
    start = None
    for i, l in enumerate(lines):
        if l.strip().startswith('##') and any(k in l for k in keys):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].strip().startswith('## '):
            end = j
            break
    return (start, end)


def replace_kv(lines, rng, key, value):
    """把 `- key：旧值` 整行换成新值。返回旧值（未命中返回 None）。"""
    if rng is None:
        return None
    pat = re.compile(r'^\s*[-*]\s*' + re.escape(key) + r'\s*[:：].*$')
    for i in range(rng[0], rng[1]):
        if pat.match(lines[i]):
            old = lines[i].strip()
            lines[i] = '- %s：%s' % (key, value)
            return old
    return None


def append_unlock(lines, rng, key, value):
    """已解锁地点是累积列表，追加去重而非覆盖。"""
    if rng is None:
        return None
    pat = re.compile(r'^\s*[-*]\s*' + re.escape(key) + r'\s*[:：]\s*(.*)$')
    for i in range(rng[0], rng[1]):
        m = pat.match(lines[i])
        if m:
            cur = [x.strip() for x in re.split(r'[,，、]', m.group(1)) if x.strip()]
            if value not in cur:
                cur.append(value)
            lines[i] = '- %s：%s' % (key, '、'.join(cur))
            return m.group(1).strip()
    return None


def upsert_location_row(lines, name, status, note, resource, ch):
    """地点状态机表 upsert：同名更新状态/变更于章，异名追加新行。"""
    rng = section_range(lines, '地点状态机')
    if rng is None:
        return 'skip:无地点状态机区块'
    s, e = rng
    rows = []
    for i in range(s, e):
        if lines[i].strip().startswith('|'):
            rows.append(i)
    if len(rows) < 2:
        return 'skip:表格不完整'
    target = None
    for i in rows[2:]:
        cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        if cells and cells[0] == name:
            target = i
            break
    if target is not None:
        cells = [c.strip() for c in lines[target].strip().strip('|').split('|')]
        while len(cells) < 6:
            cells.append('-')
        old = cells[1]
        if status:
            cells[1] = status
        cells[2] = '第%s章' % ch
        # 老项目产生章号可能是 1 位（如 | 1 |），统一规整为 4 位，避免同表两种写法
        if re.fullmatch(r'\d{1,4}', cells[3]):
            cells[3] = cells[3].zfill(4)
        if resource:
            cells[5] = resource
        lines[target] = '| ' + ' | '.join(cells) + ' |'
        return 'update:%s(%s→%s)' % (name, old, cells[1])
    # 新行插到表格最后一行之后
    new = '| %s | %s | 第%s章 | %s | public | %s |' % (
        name, status or 'intact', ch, ch, resource or note or '-')
    lines.insert(rows[-1] + 1, new)
    return 'insert:%s(%s)' % (name, status or 'intact')


def timeline_rows(tl_path):
    """读 timeline.md 的表格行（跳过表头/分隔）。返回 (lines, rows_idx, header_cells)。"""
    if not os.path.isfile(tl_path):
        return [], [], []
    lines = read_text(tl_path).splitlines()
    rows = [i for i, l in enumerate(lines) if l.strip().startswith('|')]
    if len(rows) < 1:
        return lines, [], []
    header = [c.strip() for c in lines[rows[0]].strip().strip('|').split('|')]
    return lines, rows, header


def ensure_timeline_table(tl_path, ch):
    """timeline.md 不存在/无表头时，按标准 5 列建表。"""
    if not os.path.isfile(tl_path):
        lines = ['# timeline', '',
                 '| 章号 | 故事时间 | 事件 | 涉及实体 | 可见性(visibility) |',
                 '|------|---------|------|---------|---------------------|']
        return lines, 5, True
    lines = read_text(tl_path).splitlines()
    rows = [i for i, l in enumerate(lines) if l.strip().startswith('|')]
    if not rows:
        lines += ['', '| 章号 | 故事时间 | 事件 | 涉及实体 | 可见性(visibility) |',
                  '|------|---------|------|---------|---------------------|']
        return lines, 5, True
    header = [c.strip() for c in lines[rows[0]].strip().strip('|').split('|')]
    return lines, len(header), False


# ---------- 主流程 ----------

def plan_chapter(root, ch, tick, dry_lines):
    """计算本章的推进计划；dry_lines=True 时不落盘，仅返回描述。"""
    acts = []
    truth_dir = os.path.join(root, '故事', '真相')
    tl_path = os.path.join(truth_dir, 'timeline.md')
    w_path = os.path.join(truth_dir, 'world.md')

    # 1) timeline.md —— 事件行（唯一真相源）
    tl_lines, ncol, _ = ensure_timeline_table(tl_path, ch)
    rows = [i for i, l in enumerate(tl_lines) if l.strip().startswith('|')]
    exist = None
    for i in rows[2:] if len(rows) >= 2 else []:
        cells = [c.strip() for c in tl_lines[i].strip().strip('|').split('|')]
        if cells and chap4(cells[0]) == ch:
            exist = i
            break
    ev_text = '；'.join(e[1] for e in tick['event'] if len(e) >= 2) or '（本章无世界级事件）'
    ev_time = tick['event'][0][0] if tick['event'] else (clock_end(tick['clock'][0]) if tick['clock'] else '')
    if ncol >= 5:
        new_row = '| %s | %s | %s | %s | %s |' % (
            ch, ev_time or '-', ev_text,
            '；'.join(loc[0] for loc in tick['loc']) or '-', 'reader_known')
    else:  # 老项目 3 列格式：章号|时间|事件
        new_row = '| %s | %s | %s |' % (ch, ev_time or '-', ev_text)
    if exist is not None:
        tl_lines[exist] = new_row
        acts.append(('timeline.md', 'update', '第%s章行已存在→覆盖' % ch))
    else:
        ins_at = (rows[-1] + 1) if rows else len(tl_lines)
        tl_lines.insert(ins_at, new_row)
        acts.append(('timeline.md', 'insert', new_row))

    # 2) world.md —— 当前状态 + 地点状态机
    w_lines = read_text(w_path).splitlines() if os.path.isfile(w_path) else []
    if w_lines:
        rng = section_range(w_lines, '当前状态')
        if rng is None:
            acts.append(('world.md', 'skip', '无【当前状态】区块（当前进度/地点/环境未推进）'))
        else:
            if tick['clock']:
                end = clock_end(tick['clock'][0])
                if end:
                    old = replace_kv(w_lines, rng, '当前进度', '第 %s 章 / %s' % (ch, end))
                    acts.append(('world.md', 'set', '当前进度→第 %s 章 / %s' % (ch, end)))
                    if old is None:
                        acts.append(('world.md', 'warn', '未找到「当前进度」行，未写入'))
            for kv in tick['place']:
                for k, v in kv:
                    if k in ('主场景', '当前地点', '地点'):
                        replace_kv(w_lines, rng, '主场景', v)
                        acts.append(('world.md', 'set', '主场景→%s' % v))
                    elif k in ('新解锁', '解锁'):
                        append_unlock(w_lines, rng, '已解锁地点', v)
                        acts.append(('world.md', 'append', '已解锁地点 +%s' % v))
            for kv in tick['env']:
                for k, v in kv:
                    if k in ('天气', '季节', '特殊状态'):
                        r = replace_kv(w_lines, rng, k, v)
                        if r is not None:
                            acts.append(('world.md', 'set', '%s→%s' % (k, v)))
                        else:
                            acts.append(('world.md', 'warn', '未找到「%s」行，未写入' % k))
        for segs in tick['loc']:
            if not segs:
                continue
            name = segs[0]
            status = segs[1] if len(segs) > 1 else ''
            note = segs[2] if len(segs) > 2 else ''
            resource = segs[3] if len(segs) > 3 else ''
            if status and status not in LOC_PHASES:
                acts.append(('world.md', 'warn',
                             '地点 %s 状态 %s 不在枚举%s，仍按原值写入' % (name, status, list(LOC_PHASES))))
            acts.append(('world.md', 'loc',
                         upsert_location_row(w_lines, name, status, note, resource, ch)))
    else:
        acts.append(('world.md', 'skip', '缺 world.md'))

    return tl_lines, w_lines, acts


def main():
    ap = argparse.ArgumentParser(description='世界状态自动推进（world_tick）')
    ap.add_argument('--root', required=True, help='项目根目录')
    ap.add_argument('--chapter', default='', help='只处理指定章（4 位章号）；不传=全部')
    ap.add_argument('--apply', action='store_true', help='真正写盘（默认 dry-run）')
    ap.add_argument('--quiet', action='store_true', help='只输出汇总行')
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print('错误：项目根不存在 → %s' % root)
        sys.exit(1)
    truth_dir = os.path.join(root, '故事', '真相')
    if not os.path.isdir(truth_dir):
        print('错误：缺 故事/真相 目录 → %s' % truth_dir)
        sys.exit(1)
    os.makedirs(truth_dir, exist_ok=True)

    want = chap4(args.chapter) if args.chapter else ''
    cands = find_report_files(root)
    if want:
        cands = [c for c in cands if c[0] == want]

    # 同章多文件（暂存 + 正式）时，取最后一个含 WORLD-TICK 的
    picked = {}
    for ch, path in cands:
        tick = parse_tick(read_text(path))
        if tick:
            picked[ch] = (path, tick)
    missing = sorted({ch for ch, _ in cands} - set(picked))

    if not picked:
        print('=== world_tick ===')
        print('  未在任何 Change Report 里找到 WORLD-TICK 区。')
        print('  Change Report 需含：')
        print('    <!-- WORLD-TICK-START -->')
        print('    - clock: 0001 | 三月十二 晨 → 三月十三 夜 | 1天')
        print('    <!-- WORLD-TICK-END -->')
        sys.exit(2)

    total = 0
    for ch in sorted(picked):
        path, tick = picked[ch]
        tl_lines, w_lines, acts = plan_chapter(root, ch, tick, not args.apply)
        total += len([a for a in acts if a[1] in ('insert', 'update', 'set', 'loc', 'append')])
        if not args.quiet:
            print('--- 第%s章 ← %s ---' % (ch, os.path.relpath(path, root)))
            for tgt, kind, desc in acts:
                mark = {'insert': '+', 'update': '~', 'set': '~', 'append': '+',
                        'loc': '~', 'skip': '!', 'warn': '?'}[kind]
                print('  [%s] %-13s %s %s' % (mark, tgt, '', desc))
        if args.apply:
            write_text(os.path.join(truth_dir, 'timeline.md'), '\n'.join(tl_lines) + '\n')
            if w_lines:
                write_text(os.path.join(truth_dir, 'world.md'), '\n'.join(w_lines) + '\n')

    print('=== world_tick：%d 章，%d 项变更，%s ===' % (
        len(picked), total, '已写盘' if args.apply else 'dry-run 未写盘（加 --apply）'))
    if missing:
        print('缺 WORLD-TICK 区的章：%s' % '、'.join(missing))
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
