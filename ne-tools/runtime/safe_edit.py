#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Novel Engine v1.4 安全编辑工具（safe_edit.py）
=============================================
解决"Python 锚点替换断言失败"三类顽疾：
  1. 弯直引号 / 近似词导致 old 锚点未命中（逐个校验、缺失即报错，不写盘）
  2. 断言失败时"已替换部分只改内存、未写盘导致编辑丢失"
  3. new 多行字符串被拆成表达式 / 三引号末尾误用等脚本语法坑（用 ||| 分隔规避）

用法：
  python runtime/safe_edit.py --file <正文路径> --replace "old|||new" [--replace "old2|||new2" ...]
  python runtime/safe_edit.py --file <路径> --check-only          # 只校验锚点，不写盘
  python runtime/safe_edit.py --file <路径> --replace "a|||b" --first-only  # 每个锚点只替换首个

行为保证：
  - 先校验【全部】锚点在目标文件中存在；任一缺失 → 打印缺失列表，退出码 1，不写任何改动。
  - 全部存在 → 统一执行替换并写盘，逐条打印替换次数。
  - new 文本内如需换行，用字面量 \n（自动转成换行）；分隔符用 |||，规避引号/三引号语法坑。

退出码：0=全部锚点命中并完成  1=存在缺失锚点（未写盘）
"""
import argparse, io, sys

SEP = '|||'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True, help='目标文件绝对路径')
    ap.add_argument('--replace', action='append', default=[], metavar='old|||new',
                    help='替换对，可多次传入，格式 old|||new；new 内换行用字面量 \\n')
    ap.add_argument('--check-only', action='store_true', help='只校验锚点存在性，不写盘')
    ap.add_argument('--first-only', action='store_true', help='每个锚点只替换首次出现')
    ap.add_argument('--encoding', default='utf-8')
    args = ap.parse_args()

    if not args.replace:
        print('[错误] 至少需要一个 --replace "old|||new"')
        sys.exit(1)

    # 解析替换对
    pairs = []
    for r in args.replace:
        if SEP not in r:
            print(f'[错误] 替换对缺少分隔符 {SEP}: {r!r}')
            sys.exit(1)
        old, new = r.split(SEP, 1)
        if not old:
            print(f'[错误] old 为空: {r!r}')
            sys.exit(1)
        # 字面量 \n 转真换行（跨行 new 用 \n 拼接，避免多行字符串拆表达式）
        new = new.replace('\\n', '\n')
        pairs.append((old, new))

    # 读取文件
    try:
        text = io.open(args.file, encoding=args.encoding).read()
    except Exception as e:
        print(f'[错误] 读取文件失败 {args.file}: {e}')
        sys.exit(1)

    # 1 先校验全部锚点（不写盘）
    missing = []
    for old, _ in pairs:
        if old not in text:
            missing.append(old[:40])
    if missing:
        print('[FAIL] 以下锚点未命中（文件未改动，请先读实际文本核对引号/用词）：')
        for m in missing:
            print(f'  - {m!r}')
        print('退出码=1，未写盘。')
        sys.exit(1)

    if args.check_only:
        print(f'[PASS] 全部 {len(pairs)} 个锚点命中（check-only，未写盘）')
        sys.exit(0)

    # 2 全部命中 → 统一执行替换
    changed = 0
    for old, new in pairs:
        cnt = text.count(old)
        if args.first_only and cnt > 1:
            text = text.replace(old, new, 1)
            changed += 1
            print(f'  [替换] {cnt}处→首处: {old[:30]!r} -> {new[:30]!r}')
        else:
            text = text.replace(old, new)
            changed += cnt
            print(f'  [替换] {cnt}处: {old[:30]!r} -> {new[:30]!r}')

    # 3 写盘
    try:
        io.open(args.file, 'w', encoding=args.encoding).write(text)
    except Exception as e:
        print(f'[错误] 写盘失败 {args.file}: {e}')
        sys.exit(1)
    print(f'完成：{len(pairs)} 个锚点，共 {changed} 处替换已写盘。')
    sys.exit(0)


if __name__ == '__main__':
    main()
