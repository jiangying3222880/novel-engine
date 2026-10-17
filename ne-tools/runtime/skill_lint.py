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
import io
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

_MD_REF_RE = re.compile(r'[\`\(]([^\`\)\n]+\.md)[\`\)]')

# 包内 .md 文件索引缓存（跨子技能引用解析用）：{包根: {basename: 绝对路径}}
_PKG_INDEX = {}


def pkg_root(skill_dir):
    """包根定位：优先含 VERSION，其次含 ne/ 路由目录（v2.0 拆分后 ne-* 平铺在包根下）。

    为什么不能只认 SKILL.md：ne-tools 自己也有 SKILL.md，会被误判成包根。
    """
    p = os.path.dirname(os.path.abspath(skill_dir))
    for _ in range(3):
        if os.path.isfile(os.path.join(p, 'VERSION')) or os.path.isdir(os.path.join(p, 'ne')):
            return p
        p = os.path.dirname(p)
    return None


def pkg_file_index(pkg):
    if not pkg:
        return {}
    if pkg in _PKG_INDEX:
        return _PKG_INDEX[pkg]
    idx = {}
    for dirpath, dirnames, files in os.walk(pkg):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', '__pycache__', '_skill_analysis')]
        for f in files:
            if f.endswith('.md'):
                idx.setdefault(f, os.path.join(dirpath, f))
    _PKG_INDEX[pkg] = idx
    return idx

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
    refs = set(_MD_REF_RE.findall(body))
    # 行内豁免：文档里提到"历史异名/反面例子"时，写的本来就是不存在的名字。
    # 在那一行加 <!-- link-exempt -->（或 truth-naming-exempt）即可，否则是假警报。
    exempt_refs = set()
    for line in body.splitlines():
        if 'link-exempt' in line or 'truth-naming-exempt' in line:
            exempt_refs.update(_MD_REF_RE.findall(line))
    broken = []
    for r in sorted(refs):
        if r.startswith('http') or r in exempt_refs:
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
        if any(os.path.exists(c) for c in cands):
            continue
        # 跨子技能引用：技能包是一个整体，ne-memory 里写 `relationships.md` 指的就是
        # ne-setup/templates/truth/relationships.md，那不是断链（v2.1.3 修的假警报）。
        # 只按 basename 在包内找——写成路径的引用（如 ./references/x.md）不参与跨包解析。
        if '/' not in r and os.path.basename(r) in pkg_file_index(pkg_root(root)):
            continue
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
                     'timeline.md', 'world.md', 'novel-config.json',
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


# 「路径样 token」：含 / 且带 .md 扩展名。只在这类 token 里找八进制串，
# 否则技法编号 T-021/040/065、约束编号 C-001/002/003 会误报。
PATHISH = re.compile(r'[\w\u4e00-\u9fff\-.]*/[\w\u4e00-\u9fff\-./]*\.md')
# 连续 3 段以上的「三位八进制数 / 分隔」= git quotepath 转义被当成路径分隔符写进了文档
OCTET_PATH_RUN = re.compile(r'/(?:[0-7]{3}/){2,}')


# 6 状态文件正名（唯一口径源：ne-setup/templates/truth/ 下的 6 个模板）
TRUTH_CANON = ('world.md', 'characters.md', 'hooks.md',
               'objects.md', 'relationships.md', 'timeline.md')
# 历史遗留的异名——曾同时存在于仓库不同文件里，导致人和 LLM 各读到一套
TRUTH_ALIAS = {'worldview.md': 'world.md', 'facts.md': 'objects.md',
               'charactor.md': 'characters.md', 'plot.md': 'hooks.md'}


def check_truth_naming(root):
    """（检查 15）状态文件命名统一。

    根因：v2.0 拆分时没统一口径，仓库里同时存在三套叫法——
      ne-setup/templates/truth/ 用 world.md / relationships.md，
      ne-review/consistency-checklist.md 用 facts.md，
      ne-memory/SKILL.md 与 skill_lint 旧白名单用 worldview.md。
    代价不是"不好看"：外部 LLM 审计这个项目时，有的读到 worldview、有的读到 facts，
    各自报出不同的"6 状态文件清单"，看起来像模型幻觉，实际是仓库自己在自相矛盾。
    门禁也不校验文件名，于是用错名字建的项目照样全绿。
    """
    bad = []
    skip = ('.git', '.workbuddy', 'deps', '_skill_analysis')
    pat_truth = re.compile(r'(?:故事/)?真相/([A-Za-z_][A-Za-z0-9_]*\.md)')
    pat_alias = re.compile(r'\b(worldview|facts|charactor|plot)\.md\b')
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if not f.endswith(('.md', '.py')):
                continue
            # 跳过别名字典的定义处本身，否则检查项会命中自己写的 'facts.md' 字面量
            if f in ('verify.py', 'skill_lint.py'):
                continue
            p = os.path.join(dp, f)
            try:
                txt = io.open(p, encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            rel = os.path.relpath(p, root).replace('\\', '/')
            # 逐行扫描：文档为了说明历史而必须提到异名的行，用显式标记豁免，
            # 不豁免就会被自己的说明文字反复误报（宽泛跳过"历史"字样则会放过真违规）
            for line in txt.splitlines():
                if 'truth-naming-exempt' in line:
                    continue
                for m in pat_truth.finditer(line):
                    name = m.group(1)
                    if name not in TRUTH_CANON:
                        bad.append('%s: 真相/%s（正名：%s）' % (
                            rel, name, TRUTH_ALIAS.get(name, '/'.join(TRUTH_CANON))))
                for m in pat_alias.finditer(line):
                    name = m.group(0)
                    if name in TRUTH_ALIAS:
                        bad.append('%s: %s（应为 %s）' % (rel, name, TRUTH_ALIAS[name]))
            if bad:
                break
        if bad:
            break
    if bad:
        return ('FAIL', '状态文件命名统一', '; '.join(bad[:4]))
    return ('PASS', '状态文件命名统一', '6 状态文件口径一致')


def check_technique_ids(root):
    """（检查 16）技法编号唯一。

    根因（与检查 15 同源）：T-106 被两个完全不同的技法同时使用——
    「以退为进法」和「时间节点对照法」。撞号时引用 T-106 不知道指哪一个，
    S1 按编号选技法就会选错，而**没有任何东西会报错**（门禁不查，人也不翻表）。
    已把后者改为 T-107；这里加闸防复发。

    只匹配表格行首的 `| T-xxx |`，散文里提到编号（如更新日志）不会误命中。
    """
    def norm(s):
        # 「最强最弱反差法」vs「最强=最弱反差法」是同一个技法的写法差异，不是冲突
        return re.sub(r'[\s=＝·、，,。]', '', s)

    pat_row = re.compile(r'^\|\s*(T-\d{3,4})\s*\|\s*([^|]+)')
    pat_head = re.compile(r'^#{2,4}\s*(T-\d{3,4})\s+(.*)$')
    dup, total = [], 0
    # 编号 -> [(技法名, 来源文件), ...]。
    # ⚠️ 不能用 setdefault(tid, (name,rel)) 只留第一条——那样跨文件永远比不出差异，
    #    这条分支会变成**恒定绿灯**（2026-10-17 负向测试抓到：改了名字照样 PASS）。
    table = {}
    libs = os.path.join(root, 'ne-library', 'library')
    for dp, dirs, files in os.walk(libs):
        for f in sorted(files):
            if not f.endswith('.md'):
                continue
            p = os.path.join(dp, f)
            try:
                txt = io.open(p, encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            rel = os.path.relpath(p, root).replace('\\', '/')
            # (1) 同文件内判重——同一张表/同一文件里两个不同技法用同一编号 = 真撞号
            seen = {}
            for line in txt.splitlines():
                m = pat_row.match(line) or pat_head.match(line)
                if not m:
                    continue
                tid, name = m.group(1), norm(m.group(2))
                total += 1
                if tid in seen and seen[tid] != name:
                    dup.append('%s: %s 同文件撞号（%s / %s）' % (rel, tid, seen[tid], name))
                seen.setdefault(tid, name)
                table.setdefault(tid, []).append((name, rel))
    # (2) 跨文件一致性：同一编号在两份文档里指向不同技法 = 更隐蔽的撞号。
    #     判重不能按"出现次数"算（对比分析本来就会引用索引里的编号），
    #     必须按"编号 → 技法名"是否一致来判。
    conflict = []
    for tid, items in sorted(table.items()):
        names = {}
        for name, rel in items:
            names.setdefault(name, rel)
        if len(names) > 1:
            detail = ' / '.join('[%s]=%s' % (n, r.split('/')[-1]) for n, r in sorted(names.items()))
            conflict.append('%s 跨文件不一致：%s' % (tid, detail))
    bad = dup + conflict
    if bad:
        return ('FAIL', '技法编号唯一', '; '.join(sorted(set(bad))[:3]))
    return ('PASS', '技法编号唯一', '%d 行编号，%d 个唯一号，跨文件一致' % (total, len(table)))


def check_path_escapes(root):
    """（检查 14）路径八进制转义残留。

    根因：git 默认 core.quotepath=true，中文路径在 diff 里显示成 \\346\\227\\247，
    批量修引用的脚本若把反斜杠当路径分隔符，就会把八进制串当成目录层级写进文档。
    为什么普通断链检查抓不到：它按 basename 解析，这类串的最后一段仍是合法文件名，
    于是被当成"存在的文件"放过——必须单独按形状拦。

    ⚠️ 本函数用 io.open，缺 import io 时会被 except 静默吞成恒 PASS（踩过）。
    """
    bad = []
    skip = ('.git', '.workbuddy', 'deps', '_skill_analysis')
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if not f.endswith(('.md', '.py')):
                continue
            p = os.path.join(dp, f)
            try:
                txt = io.open(p, encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            if f == os.path.basename(__file__):   # 本文件 docstring 里有反例说明，跳过自身
                continue
            for m in PATHISH.finditer(txt):
                if OCTET_PATH_RUN.search(m.group(0)):
                    bad.append('%s: …%s…' % (os.path.relpath(p, root).replace('\\', '/'),
                                             m.group(0)[-40:]))
                    break
    uniq = sorted(set(bad))
    if uniq:
        return ('FAIL', '路径转义残留',
                '%d 个文件含 git 八进制转义路径（中文文件名被破坏）：%s'
                % (len(uniq), '；'.join(uniq[:3])))
    return ('PASS', '路径转义残留', '未检出八进制转义路径')


def main():
    ap = argparse.ArgumentParser(description='Skill 标准化自检')
    ap.add_argument('--root', default='', help='技能根目录（默认=本文件上级的上级）')
    ap.add_argument('--all', action='store_true', help='遍历 root 下所有含 SKILL.md 的子目录')
    # 一致性子集：只跑"会不会让流程静默失效"的项——全仓断链 / 产物模板契约 / 产物命名契约 /
    # 路径转义 / 状态文件命名 / 技法编号唯一。共同点：撞了不会报错，只会让人按错的口径做事。
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
            rows = [check_repo_refs(t), check_artifact_templates(t),
                    check_report_naming(t), check_path_escapes(t),
                    check_truth_naming(t), check_technique_ids(t)]
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
