#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_lint.py — Skill 标准化自检（v2.0 闸 0）
==============================================
补官方 quick_validate.py 的不足。

背景：skill-creator 的 quick_validate.py 只有 64 行，只查 5 项基础
（frontmatter 格式 / name 存在 / description 存在 / name 命名 / 无 XML 标签），
**不查体量、不查 description 是否含触发条件、不查目录名一致性、不查引用断链**。
所以 "Skill is valid!" 只是最低门槛，不是合格。

本脚本在官方 5 项之上追加：
  6. 目录名 == name 字段
  7. description 必须含"何时用"触发信号（否则 AI 不知道什么时候该调用）
  8. SKILL.md token 预算（渐进式披露要求 < 5000 token / < 500 行）
  9. WorkBuddy 要求的 agent_created 字段
  10. SKILL.md 引用的 references/ 文件是否真的存在（断链）
  11. 全仓引用断链（references/templates/library/runtime/routes 内部引用）
  12. 产物模板契约（verify.py 硬要求的根产物，templates/ 必须有模板可复制）

11/12 的来由（2026-10-15 实测发现的两类「不同步」）：
  · templates/log-template.md 让 AI 把检验报告写成 `自检_第X章.md`，
    而 verify.py 只认 `检验报告_第(\\d{4})章.md` 且无 legacy 别名 —— 报告写了但门禁扫不到。
  · verify.py `--scope init` 强制要求根 `叙事总览.md`，但 templates/narrative/ 只有 6 个子页、
    没有根 MOC 模板，也没有任何脚本生成它 —— 每个新项目初始化必 FAIL。
  两者都属于「索引/参考文档改了，最末端模板与脚本契约没跟上」，
  只校验 SKILL.md 断链（检查 10）根本扫不到。

用法：
  python runtime/skill_lint.py                  # 检查本技能根（默认）
  python runtime/skill_lint.py --root <路径>    # 检查指定技能目录
  python runtime/skill_lint.py --root <路径> --all   # 遍历该目录下所有子技能

退出码：0=全部 PASS（可能有 WARN）；1=有 FAIL
"""
import argparse
import os
import re
import sys

# 渐进式披露预算（官方建议）
MAX_LINES = 500
MAX_TOKENS = 5000
# 中文 token 估算系数：中文 1 字约 1.5-2 token，取 1.7；其余按 4 字符 1 token
CJK_TOKEN_RATE = 1.7
LATIN_TOKEN_RATE = 0.25

# description 必须出现的"何时用"信号（命中任一即算合格）
TRIGGER_SIGNALS = [
    '当', '时', '用于', '适用', '触发', 'use when', 'when the user',
    '用于', 'should be used', '请求', '想', '需要',
]

CJK_RE = re.compile(r'[\u4e00-\u9fff]')

# 项目级路径前缀：属于每本书自己的目录，不在技能内，断链检查应跳过
PROJECT_PATH_PREFIXES = ('故事/', '正文/', '设定/', '追踪/', '叙事总览/')


def parse_frontmatter(text):
    if not text.startswith('---'):
        return None, 'SKILL.md 未以 --- 开头（frontmatter 缺失）'
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None, 'frontmatter 未闭合（缺少第二个 ---）'
    return parts[1], None


def field(fm, key):
    m = re.search(r'^%s:\s*(.+)$' % re.escape(key), fm, re.M)
    return m.group(1).strip() if m else None


def estimate_tokens(text):
    cjk = len(CJK_RE.findall(text))
    latin = len(text) - cjk
    return int(cjk * CJK_TOKEN_RATE + latin * LATIN_TOKEN_RATE)


def check_skill(root):
    """返回 [(级别, 项名, 说明)]，级别 ∈ PASS/WARN/FAIL"""
    res = []
    skill_md = os.path.join(root, 'SKILL.md')

    if not os.path.exists(skill_md):
        return [('FAIL', 'SKILL.md 存在', '未找到 %s' % skill_md)]

    text = open(skill_md, encoding='utf-8', errors='ignore').read()
    fm, err = parse_frontmatter(text)
    if err:
        return [('FAIL', 'frontmatter', err)]

    # ---- 官方 5 项 ----
    name = field(fm, 'name')
    if not name:
        res.append(('FAIL', 'name 存在', 'frontmatter 缺 name'))
    else:
        if not re.match(r'^[a-z0-9-]+$', name):
            res.append(('FAIL', 'name 格式', '应为小写字母/数字/连字符，实际：%s' % name))
        elif name.startswith('-') or name.endswith('-') or '--' in name:
            res.append(('FAIL', 'name 格式', '不能以连字符开头结尾，不能含连续连字符'))
        else:
            res.append(('PASS', 'name 格式', name))

    desc = field(fm, 'description')
    if not desc:
        res.append(('FAIL', 'description 存在', 'frontmatter 缺 description'))
    else:
        if '<' in desc or '>' in desc:
            res.append(('FAIL', 'description 无 XML 标签', '含 < 或 >'))
        if len(desc) > 1024:
            res.append(('FAIL', 'description 长度', '%d 字符 > 上限 1024' % len(desc)))

    # ---- 追加项 ----
    # 6. 目录名 == name
    dirname = os.path.basename(os.path.abspath(root))
    if name and dirname != name:
        res.append(('FAIL', '目录名==name', '目录「%s」≠ name「%s」' % (dirname, name)))
    elif name:
        res.append(('PASS', '目录名==name', dirname))

    # 7. description 触发信号
    if desc:
        if any(s in desc.lower() for s in TRIGGER_SIGNALS):
            res.append(('PASS', 'description 含触发条件', '已说明何时使用'))
        else:
            res.append(('FAIL', 'description 含触发条件',
                        '未出现"何时用"信号词——AI 可能无法判断何时调用'))
        # 领域关键词（有具体动作词更好）
        if len(desc) < 20:
            res.append(('WARN', 'description 信息量', '仅 %d 字符，建议写清做什么+何时用' % len(desc)))

    # 8. 体量预算
    body = text.split('---', 2)[2] if len(text.split('---', 2)) > 2 else text
    lines = len(body.splitlines())
    tokens = estimate_tokens(body)
    if lines > MAX_LINES:
        res.append(('FAIL', 'SKILL.md 行数', '%d 行 > %d' % (lines, MAX_LINES)))
    else:
        res.append(('PASS', 'SKILL.md 行数', '%d 行（上限 %d）' % (lines, MAX_LINES)))
    if tokens > MAX_TOKENS:
        res.append(('FAIL', 'SKILL.md token 预算',
                    '约 %d token > %d（渐进式披露红线，应下沉到 references/）'
                    % (tokens, MAX_TOKENS)))
    else:
        res.append(('PASS', 'SKILL.md token 预算', '约 %d token（上限 %d）' % (tokens, MAX_TOKENS)))

    # 9. agent_created（WorkBuddy 要求）
    if field(fm, 'agent_created') is None:
        res.append(('WARN', 'agent_created', '缺失；WorkBuddy 的 skill_manage 需要此字段'))
    else:
        res.append(('PASS', 'agent_created', '存在'))

    # 10. 引用断链
    refs = set(re.findall(r'[\`\(]([^\`\)\n]+\.md)[\`\)]', body))
    broken = []
    for r in sorted(refs):
        if r.startswith('http'):
            continue
        # 跳过模板占位符与项目级路径：它们不在技能目录内，运行时才生成
        # （否则「第000X章 <标题>.md」「故事/元数据/chapter_XXXX.md」会被误报为断链）
        if any(ch in r for ch in ('XXXX', '<', '>', '{', '}')):
            continue
        if r.startswith(PROJECT_PATH_PREFIXES):
            continue
        if is_runtime_artifact(r):
            continue
        cands = [os.path.join(root, r),
                 os.path.join(root, 'references', r),
                 os.path.join(root, 'templates', r)]
        if not any(os.path.exists(c) for c in cands):
            broken.append(r)
    if broken:
        res.append(('WARN', '引用断链', '%d 处：%s' % (len(broken), '、'.join(broken[:5]))))
    else:
        res.append(('PASS', '引用断链', '检查 %d 个引用，无断链' % len(refs)))

    # ---- 11. 全仓引用断链（末端模板往往比索引迟一步） ----
    res.append(check_repo_refs(root))

    # ---- 12. 产物模板契约（verify.py 硬要求 vs templates/ 是否有模板） ----
    res.append(check_artifact_templates(root))
    # ---- 13. 产物命名契约（模板里的废弃别名/错位数章号） ----
    res.append(check_report_naming(root))

    return res


# 11/12 只在「本技能根」模式下有意义（子技能遍历时可跳过）
SKILL_INNER_DIRS = ('references', 'templates', 'library', 'runtime', 'routes')
DEV_DIR_PREFIX = ('_skill_analysis', '_selftest', '_backup', '测试_基线')
# 运行时由项目自己生成的路径前缀，不是技能文件，跳过
RUNTIME_PATH_PREFIX = ('故事/', '正文/', '设定/', '追踪/', '叙事总览/',
                       '配置/', '素材池/', '真相/', '大纲/', '兜底/')

# v2.0：运行时产物文件名（不带目录，纯文件名引用时会被误判为断链）
# 例：SKILL.md 里写「产 检验报告_第0001章.md」「更新 characters.md」——
# 这些是每本书自己生成的产物，技能包里当然没有。
RUNTIME_FILE_RE = re.compile(
    r'(第\d{3,4}章|_第[X\d]{1,4}章|chapter_[\dX]{4}|第X章)', re.I)
RUNTIME_BASENAMES = {'characters.md', 'facts.md', 'hooks.md', 'objects.md',
                     'timeline.md', 'worldview.md', 'novel-config.json',
                     'index.md'}


def is_runtime_artifact(ref):
    """判断一个 .md 引用是否指向项目运行时产物（而非技能内文件）。"""
    base = os.path.basename(ref).lower()
    if RUNTIME_FILE_RE.search(ref):
        return True
    # 通配符与占位符（如 templates/narrative/0*.md、细纲摘要_卷X.md）
    if '*' in ref or '卷X' in ref or '第X' in ref:
        return True
    if base in RUNTIME_BASENAMES:
        return True
    # 叙事总览.md：模板在 templates/narrative/ 下，裸文件名引用 = 项目根产物
    if base == '叙事总览.md' and 'narrative' not in ref.lower() \
            and 'templates' not in ref.lower():
        return True
    return False


def _iter_md(root):
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'dist',
                                                '.workbuddy', 'node_modules', 'deps')]
        top = os.path.relpath(dp, root).replace('\\', '/')
        if top != '.' and any(top.startswith(p) for p in DEV_DIR_PREFIX):
            continue
        for f in files:
            if f.endswith('.md'):
                yield os.path.join(dp, f)


def _deep_exists(root, path):
    """技能树内任意深度查找（library/genres/<题材>/xxx.md 这类深层路径也能定位）。"""
    if os.path.exists(os.path.join(root, path)):
        return True
    base = os.path.basename(path)
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
        if base in files:
            return True
    return False


def check_repo_refs(root):
    """全仓内部引用断链。"""
    ref_re = re.compile(r'[\`\(\[]\s*([A-Za-z\u4e00-\u9fff0-9_/\.\-]+\.(?:md|py|json))\s*[\`\)\]]')
    checked, missed = 0, []
    for p in _iter_md(root):
        try:
            t = open(p, encoding='utf-8-sig', errors='ignore').read()
        except Exception:
            continue
        for raw in ref_re.findall(t):
            if '://' in raw:
                continue
            if any(ch in raw for ch in ('XXXX', 'XXX', '<', '>', '{', '}', 'N章')):
                continue
            if raw.startswith(RUNTIME_PATH_PREFIX):
                continue
            bare = '/' not in raw
            if bare:
                # 裸文件名：只在它确实存在于技能树时才当作内部引用（避免 truth 文件误报）
                if not _deep_exists(root, raw):
                    continue
            else:
                if raw.split('/')[0] not in SKILL_INNER_DIRS:
                    continue
            checked += 1
            if not _deep_exists(root, raw):
                missed.append((os.path.relpath(p, root).replace('\\', '/'), raw))
    if missed:
        uniq = sorted(set(raw for _, raw in missed))
        first_src = {}
        for src, raw in missed:
            first_src.setdefault(raw, src)
        return ('WARN', '全仓引用断链',
                '%d 个：%s' % (len(uniq), '、'.join('%s(%s)' % (u, first_src[u]) for u in uniq[:3])))
    return ('PASS', '全仓引用断链', '检查 %d 处内部引用，无断链' % checked)


def _find_artifact_in_package(root, name):
    """v2.0：拆分后 verify.py 在 ne-tools，模板可能在别的子技能。

    先在自身 templates/ 找，找不到就往上找包根，在整个包内搜同名文件。
    """
    for sub in ('templates', ''):
        p = os.path.join(root, sub, name)
        if os.path.exists(p):
            return os.path.relpath(p, root).replace('\\', '/')
    # 往上找包根
    d = root
    for _ in range(4):
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
        if os.path.exists(os.path.join(d, 'VERSION')) or os.path.isdir(os.path.join(d, 'ne')):
            for dp, dirs, files in os.walk(d):
                dirs[:] = [x for x in dirs
                           if x not in ('.git', '__pycache__', 'dist', 'story')
                           and not x.startswith('_') and not x.startswith('测试')]
                if name in files:
                    return os.path.relpath(os.path.join(dp, name), root).replace('\\', '/')
            break
    return None


def check_artifact_templates(root):
    """verify.py 硬性要求的根产物，必须在 templates/ 下有一份可复制的模板。"""
    verify = os.path.join(root, 'runtime', 'verify.py')
    if not os.path.exists(verify):
        return ('PASS', '产物模板契约', '无 verify.py，跳过')
    try:
        vt = open(verify, encoding='utf-8', errors='ignore').read()
    except Exception:
        return ('PASS', '产物模板契约', 'verify.py 不可读，跳过')

    # 提取 os.path.isfile(os.path.join(root, 'XXX')) 形式的根产物要求
    req = set(re.findall(r"os\.path\.isfile\(os\.path\.join\(root,\s*'([^']+\.(?:md|json))'\)\)", vt))
    if not req:
        return ('PASS', '产物模板契约', '未检出硬性根产物要求')

    have = set()
    tdir = os.path.join(root, 'templates')
    if os.path.isdir(tdir):
        for dp, dirs, files in os.walk(tdir):
            have.update(files)
    # v2.0：自身没有则在整个技能包内找（模板可能归到别的子技能）
    located = {}
    for r in req:
        if r in have:
            located[r] = 'templates/'
        else:
            hit = _find_artifact_in_package(root, r)
            if hit:
                located[r] = hit
    missing = sorted(r for r in req if r not in located)
    if missing:
        return ('FAIL', '产物模板契约',
                'verify.py 硬性要求但全包内均无模板：%s（项目初始化必然 FAIL，AI 无从复制）'
                % '、'.join(missing))
    detail = '、'.join('%s→%s' % (k, located[k]) for k in sorted(located))
    return ('PASS', '产物模板契约', '%d 个硬要求产物均有模板：%s' % (len(req), detail))


# 13 的已知「废弃别名 → 规范名」对照表。
# 只登记真正出过事的一律rename：新增词条时请在下方注释写明时间与原委。
RETIRED_ARTIFACT_ALIASES = {
    # 2026-10-15：log-template 让 AI 写 `自检_第X章.md`，而 verify.py 只认
    # `检验报告_第(\d{4})章.md`（无 legacy 别名）→ 报告写了但门禁扫不到。
    '检验报告': ['自检'],
}
# 模板中允许出现的非门禁产物（有意为之，不是别名错用）
NONGATED_ARTIFACTS = ('变更',)


def _extract_canonical_artifacts(root):
    verify = os.path.join(root, 'runtime', 'verify.py')
    if not os.path.exists(verify):
        return set()
    try:
        vt = open(verify, encoding='utf-8', errors='ignore').read()
    except Exception:
        return set()
    return (set(re.findall(r"f'([^']+?)_第\{[a-z_]+\}章\.md'", vt))
            | set(re.findall(r"r'\^([^']+?)_第\(\\d\{4\}\)章\\\.md\$'", vt)))


def check_report_naming(root):
    """（检查 13）模板里若出现已废弃的产物别名 + 错误章号位数，直接 FAIL。

    为什么只看 templates/：参考文档里的历史叙述会提到旧名（合法），
    但**模板是要被 AI 逐章填的**，写错一个文件名就会让整条门禁链静默失效。
    """
    canon = _extract_canonical_artifacts(root)
    if not canon:
        return ('PASS', '产物命名契约', '未检出门禁产物命名，跳过')
    bad = []
    tdir = os.path.join(root, 'templates')
    for dp, dirs, files in os.walk(tdir):
        for f in files:
            if not f.endswith('.md'):
                continue
            p = os.path.join(dp, f)
            # 说明性引用（出现在"不要写成..."的警示句里）不算违规
            lines = [ln for ln in open(p, encoding='utf-8-sig', errors='ignore').read().splitlines()
                     if '不可改' not in ln and '写成' not in ln and '（✗' not in ln]
            body = '\n'.join(lines)
            for m in re.finditer(r'([A-Za-z\u4e00-\u9fff]+)_第([0-9X]{1,4})章\.md', body):
                pre, num = m.group(1), m.group(2)
                if pre in NONGATED_ARTIFACTS or pre in canon:
                    continue
                for c in canon:
                    if pre.endswith(c) or c.endswith(pre):
                        break
                else:
                    for c, aliases in RETIRED_ARTIFACT_ALIASES.items():
                        if any(pre.endswith(a) or a in pre for a in aliases):
                            bad.append('%s: %s → 应为 %s_第XXXX章.md（4 位章号）'
                                       % (os.path.relpath(p, root).replace('\\', '/'),
                                          m.group(0), c))
                            break
    uniq = sorted(set(bad))
    if uniq:
        return ('FAIL', '产物命名契约',
                '%d 处用了废弃别名/错位数章号：%s' % (len(uniq), '；'.join(uniq[:3])))
    return ('PASS', '产物命名契约', 'templates/ 内无废弃产物别名')


def main():
    ap = argparse.ArgumentParser(description='Skill 标准化自检')
    ap.add_argument('--root', default='', help='技能根目录（默认=本文件上级的上级）')
    ap.add_argument('--all', action='store_true', help='遍历 root 下所有含 SKILL.md 的子目录')
    # 一致性子集：只跑"会不会让流程静默失效"的三项（全仓断链 / 产物模板契约 / 产物命名契约）。
    # 给 pre-commit 用——完整自检里 description/token 那两项是长期待办，
    # 若一并进门禁会导致每次提交都被拒，反而逼人用 --no-verify 绕开。
    ap.add_argument('--consistency', action='store_true',
                    help='只跑一致性三项，供提交门禁调用')
    args = ap.parse_args()

    # v2.0：脚本从 <包根>/runtime/ 移到 <包根>/ne-tools/runtime/，多了一层。
    # 逐层向上找包根：优先含 VERSION，其次含 ne/ 路由技能，最后含 SKILL.md。
    # 不能只认 SKILL.md——拆分后 ne-tools/ 自己也有 SKILL.md，会被误判成包根。
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
    default_root = _find_package_root(here)
    root = args.root or default_root

    targets = []
    if args.all:
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, 'SKILL.md')):
                targets.append(p)
    else:
        targets.append(root)

    total_fail = total_warn = 0
    for t in targets:
        print('\n=== %s ===' % os.path.basename(os.path.abspath(t)))
        if args.consistency:
            rows = [check_repo_refs(t), check_artifact_templates(t), check_report_naming(t)]
        else:
            rows = check_skill(t)
        for level, item, detail in rows:
            print('  [%s] %-28s %s' % (level, item, detail))
            if level == 'FAIL':
                total_fail += 1
            elif level == 'WARN':
                total_warn += 1

    print('\n--- 合计：FAIL %d / WARN %d ---' % (total_fail, total_warn))
    if total_fail:
        print('结论：FAIL — 未达标准，修复后再提交。')
        return 1
    print('结论：PASS' + ('（有 WARN，建议处理）' if total_warn else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
