#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_sync.py — 技能说明文档同步器
================================
解决"修改技能文件后说明文档（_README.md）容易过期"的问题。

约定：每个含 .md 文件或有子目录的目录，维护一个 `_README.md`：
  - 顶部"人工说明区"：由作者维护的语义描述（定位/用法/上下游关系），doc_sync 不触碰。
  - 底部"自动清单区"：由本脚本维护的文件清单（文件名/大小/首行标题/更新时间）。

用法：
  python runtime/doc_sync.py scan            # 列出全部目录的同步状态（缺 _README / 过期 / 正常）
  python runtime/doc_sync.py check           # 门禁：_README 缺失/过期，或 SKILL/README/变更历史版本号不一致，则 exit 1
  python runtime/doc_sync.py update          # 批量创建/刷新各目录 _README 的自动清单区
  python runtime/doc_sync.py update --root X # 指定技能根目录（默认=本文件上级）
"""
import os
import re
import sys
import io
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
# v2.0：脚本从 <技能根>/runtime/ 移到 <技能根>/ne-tools/runtime/，多了一层。
# 逐层向上找含 VERSION 或 SKILL.md 的目录作为包根，避免硬编码层数。
def _find_package_root(start):
    """向上找包根。优先级：含 VERSION > 含 ne/ 路由子技能 > 含 SKILL.md。

    注意不能只认 SKILL.md——拆分后 ne-toolst/ 自己也有 SKILL.md，会被误判成包根。
    """
    cands = []
    d = start
    for _ in range(5):
        has_ver = os.path.exists(os.path.join(d, "VERSION"))
        has_ne = os.path.isdir(os.path.join(d, "ne"))
        has_skill = os.path.exists(os.path.join(d, "SKILL.md"))
        if has_ver or has_ne or has_skill:
            cands.append((0 if has_ver else (1 if has_ne else 2), d))
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    if not cands:
        return os.path.dirname(HERE)
    cands.sort(key=lambda x: x[0])
    return cands[0][1]

DEFAULT_ROOT = _find_package_root(HERE)

MARK_START = "<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->"
MARK_END = "<!-- AUTO-LIST-END -->"
# deps = 离线 vendored 第三方依赖（jieba/pypinyin/pyyaml），非技能说明文档，跳过扫描
SKIP_DIRS = {".git", "__pycache__", ".workbuddy", "node_modules", "deps", "dist"}
# 开发期目录（与 package.py 排除规则同口径，D-19）：不进运行镜像，
# 因此也不纳入技能本体同步校验——否则镜像里跑 check 会因子目录缺失而误报过期。
SKIP_DIR_PREFIXES = ("_skill_analysis", "_selftest", "_backup", "测试_基线")
# 非技能本体的文件（与 package.py 的 EXCLUDE_FILE_PATTERNS 同口径）：
# 不进运行镜像，因此也不进自动清单，否则镜像侧 check 必然误报过期。
SKIP_FILE_PATTERNS = (r'^pr-body\.md$', r'^审查报告.*\.md$')


def walk_dirs(root):
    """返回所有含 md 或有子目录的目录（相对路径列表，'.' 代表根）。"""
    result = []
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in SKIP_DIRS and not d.startswith(SKIP_DIR_PREFIXES)]
        if ".git" in dp:
            continue
        rel = os.path.relpath(dp, root)
        has_md = any(f.endswith(".md") and not f.startswith("_") for f in files)
        has_sub = bool(dirs)
        if has_md or has_sub:
            result.append((rel, files, dirs))
    return result


def read(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


def write(p, text):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def first_heading(text):
    """取 md 第一个 # 或 ## 标题作用途，截断 34 字。"""
    m = re.search(r"^#{1,3}\s+(.+)$", text, re.M)
    if not m:
        return ""
    t = m.group(1).strip().replace("|", "／")
    return t[:34]


def human_size(n):
    return "%.1fK" % (n / 1024)


def gen_autolist(root, rel):
    """生成自动清单区文本（不含 MARK 标记）。"""
    dp = os.path.join(root, rel) if rel != "." else root
    entries = []
    files = sorted(f for f in os.listdir(dp)
                   if f.endswith(".md") and not f.startswith("_")
                   and not any(re.match(pat, f) for pat in SKIP_FILE_PATTERNS))
    for f in files:
        p = os.path.join(dp, f)
        try:
            size = os.path.getsize(p)
            c = read(p)
            purpose = first_heading(c)
            mtime = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
        except Exception:
            size, purpose, mtime = 0, "", "-"
        entries.append((f, human_size(size), purpose, mtime))
    lines = ["## 文件清单（自动生成）", "", "| 文件 | 大小 | 用途（首行标题） | 更新 |",
             "|------|------|-------------------|------|"]
    for f, sz, pur, mt in entries:
        lines.append("| %s | %s | %s | %s |" % (f, sz, pur or "-", mt))
    subdirs = sorted(d for d in os.listdir(dp)
                     if os.path.isdir(os.path.join(dp, d))
                     and d not in SKIP_DIRS
                     and not d.startswith(SKIP_DIR_PREFIXES))
    if subdirs:
        lines.append("")
        lines.append("### 子目录")
        lines.append("")
        for d in subdirs:
            sub_readme = os.path.exists(os.path.join(dp, d, "_README.md"))
            lines.append("- `%s/` %s" % (d, "（有说明）" if sub_readme else "（缺说明，运行 doc_sync update 生成）"))
    return "\n".join(lines)


def split_autolist(text):
    """把 _README 拆成 (人工区, 自动区)。自动区可能不存在。"""
    if MARK_START in text and MARK_END in text:
        head = text.split(MARK_START)[0]
        return head, True
    return text, False


def status_of(root, rel, files):
    """返回 ('missing'|'ok'|'stale', 详情)。"""
    rp = os.path.join(root, rel, "_README.md") if rel != "." else os.path.join(root, "_README.md")
    if not os.path.exists(rp):
        return "missing", ""
    text = read(rp)
    # 自动区是否存在且与最新一致
    autolist = gen_autolist(root, rel)
    if MARK_START in text and MARK_END in text:
        cur = text.split(MARK_START)[1].split(MARK_END)[0].strip()
        if cur == autolist.strip():
            return "ok", ""
        return "stale", "自动清单与目录不一致"
    # 有 _README 但无自动区
    return "stale", "缺少自动清单区（运行 doc_sync update）"


def extract_skill_version(root):
    """权威版本号（v2.0 闸 1）：优先读包级 `VERSION` 文件，取不到再回退根 SKILL.md frontmatter。

    拆分前权威源是单技能 SKILL.md frontmatter，导致"改一处忘两处"。
    v2.0 起包级 VERSION 是唯一真相源，任何子技能版本号必须等于它。
    """
    vp = os.path.join(root, "VERSION")
    if os.path.exists(vp):
        v = read(vp).strip().splitlines()[0].strip() if read(vp).strip() else ""
        if v:
            return v
    txt = read(os.path.join(root, "SKILL.md"))
    m = re.search(r'^version:\s*([0-9][0-9A-Za-z.\-]*)', txt, re.M)
    return m.group(1).strip() if m else ""


def check_subskill_versions(root):
    """v2.0 新增：所有 `ne-*` 子技能的版本号必须等于包级 VERSION。

    拆分后每个子技能各有一份 SKILL.md，版本号散落 9 处，靠人同步必然漏。
    """
    problems = []
    ver = extract_skill_version(root)
    if not ver:
        return problems  # 权威版本缺失由 check_version_consistency 报
    subs = sorted(d for d in os.listdir(root)
                  if d.startswith("ne") and os.path.isdir(os.path.join(root, d))
                  and os.path.exists(os.path.join(root, d, "SKILL.md")))
    if not subs:
        return problems
    for d in subs:
        txt = read(os.path.join(root, d, "SKILL.md"))
        m = re.search(r'^version:\s*([0-9][0-9A-Za-z.\-]*)', txt, re.M)
        if not m:
            problems.append("%s/SKILL.md 缺 version: 字段（应为 %s）" % (d, ver))
        elif m.group(1).strip() != ver:
            problems.append("%s/SKILL.md 版本 %s ≠ 包级 VERSION %s"
                            % (d, m.group(1).strip(), ver))
    return problems


def check_version_consistency(root):
    """D-18 跨文件版本一致性。

    gen_autolist 只记录各文件首行标题，结构上抓不到"SKILL/README/变更历史三处版本号
    互相矛盾"（v1.9.1 发布包曾出现 SKILL=v1.9.1 而 README 仍 v1.9.0）。故独立检查：
    ①以 SKILL.md frontmatter version 为权威，README 首行标题、变更历史最新条目须含同号；
    ②v1.9.1.2 补盲（D-18 第二次复发）：README 文末「## 版本」段曾回退到 v1.9.0 而首行检查
    全绿——改为对 SKILL/README/变更历史做**全文版本 token 扫描**，最高版本号必须等于权威
    版本（容忍历史提法，专抓"最高版本落后"的漏改段）。
    返回问题字符串列表（空=一致）。
    """
    problems = []
    ver = extract_skill_version(root)
    if not ver:
        return ["SKILL.md frontmatter 未取到 version:（权威版本缺失）"]

    def _ver_key(s):
        return tuple(int(x) for x in re.findall(r'\d+', s))

    readme = read(os.path.join(root, "README.md"))
    rm = re.search(r'^#\s+(.+)$', readme, re.M)
    rhead = rm.group(1).strip() if rm else ""
    if ver not in rhead:
        problems.append("README.md 首行标题未含版本 %s（实际：%s）"
                        % (ver, (rhead[:40] or "无标题")))
    # v2.0：变更历史是开发档案不是运行依赖，已移出技能本体到 _skill_analysis/
    hist_paths = [os.path.join(root, "_skill_analysis", "变更历史.md"),
                  os.path.join(root, "references", "变更历史.md")]
    hist = ""
    for hp in hist_paths:
        if os.path.exists(hp):
            hist = read(hp)
            break
    found = re.findall(r'v?(\d+\.\d+\.\d+(?:\.\d+)?)', hist[:3000])  # 最新条目在文件顶部
    if ver not in found:
        problems.append("变更历史.md 顶部最新条目未含版本 %s（检测到最近：%s）"
                        % (ver, found[0] if found else "无版本号"))
    # 全文最高版本号扫描（历史小版本号合法存在，只抓"最高版本落后"）。
    # README/SKILL 用全文；变更历史只扫标题行——正文常合法引用未来版本（如"第二批宜进 vX.Y.Z"），
    # 全文扫描会误报（v1.9.1.2 实测：登记表引文触发 1.9.2 ≠ 1.9.1.2 假阳性）。
    skill_txt = read(os.path.join(root, "SKILL.md"))
    hist_head = "\n".join(l for l in hist.splitlines() if l.lstrip().startswith('#'))
    for fname, ftxt in (("SKILL.md", skill_txt), ("README.md", readme),
                        ("变更历史.md", hist_head)):
        toks = re.findall(r'\d+\.\d+\.\d+(?:\.\d+)?', ftxt)
        if toks:
            top = max(toks, key=_ver_key)
            if _ver_key(top) != _ver_key(ver):
                problems.append("%s 最高版本号 %s ≠ 权威版本 %s（疑有版本段漏更新）"
                                % (fname, top, ver))
    return problems


# 模块注册表编号 → config.modules 键 → verify.py need_keys 的映射（SSOT 三方对齐用）
# 触发类型为"默认开/auto"的模块（如 M-007 多窗口执行）是执行架构，无需开关，故豁免。
MODULE_KEY_MAP = {
    "M-001": "short_story",
    "M-002": "chat_outsource",
    "M-003": "pool_teardown",
    "M-004": "obsidian_overview",
    "M-005": "zvec",
    "M-006": "book_teardown",
}
MODULE_EXEMPT = {"M-007"}  # 执行架构，宿主有子 agent 时自动启用，不占 config 开关


def check_module_consistency(root):
    """模块三方一致性：module-registry.md / novel-config.json / verify.py need_keys。

    治"文档里登记了模块，配置和门禁里却没有"这类不同步（2026-10-15 实测发现
    M-006 拆书模块有完整模块卡与模板，但 config 与 verify 都没有它的开关）。
    """
    problems = []
    # v2.0：三个文件已分散到不同子技能，按新位置查找（兼容旧位置）
    def _find(*cands):
        for c in cands:
            if os.path.exists(c):
                return c
        return None

    reg = _find(os.path.join(root, "ne-setup", "references", "module-registry.md"),
                os.path.join(root, "references", "module-registry.md"))
    if not reg:
        return problems
    reg_txt = read(reg)
    mods = re.findall(r'^###\s+(M-\d{3})', reg_txt, re.M)
    if not mods:
        return problems

    cfg_p = _find(os.path.join(root, "ne-setup", "templates", "novel-config.json"),
                  os.path.join(root, "templates", "novel-config.json"))
    ver_p = _find(os.path.join(root, "ne-tools", "runtime", "verify.py"),
                  os.path.join(root, "runtime", "verify.py"))
    cfg_txt = read(cfg_p) if cfg_p else ""
    ver_txt = read(ver_p) if ver_p else ""
    for m in sorted(set(mods)):
        if m in MODULE_EXEMPT:
            continue
        key = MODULE_KEY_MAP.get(m)
        if key is None:
            problems.append("%s 未在 MODULE_KEY_MAP 中登记映射（新增模块后请补）" % m)
            continue
        if '"%s"' % key not in cfg_txt:
            problems.append("%s 的开关键 '%s' 不在 templates/novel-config.json（该模块无法关闭）"
                            % (m, key))
        if "'%s'" % key not in ver_txt:
            problems.append("%s 的开关键 '%s' 不在 runtime/verify.py 的 need_keys（门禁不校验）"
                            % (m, key))
    return problems


def do_scan_or_check(root, check=False):
    bad = 0
    for rel, files, dirs in walk_dirs(root):
        st, msg = status_of(root, rel, files)
        if st == "ok":
            continue
        bad += 1
        label = "[缺说明]" if st == "missing" else "[已过期]"
        print("%s %s  (%s)" % (label, rel if rel != "." else "[根]", msg))
    for vp in check_version_consistency(root):
        bad += 1
        print("[版本不一致] %s" % vp)
    for sp in check_subskill_versions(root):
        bad += 1
        print("[子技能版本不一致] %s" % sp)
    for mp in check_module_consistency(root):
        bad += 1
        print("[模块不一致] %s" % mp)
    if not bad:
        print("全部目录说明文档已同步，且 SKILL/README/变更历史版本一致 ✓")
    return 1 if (bad and check) else 0


def do_update(root):
    made, refreshed = 0, 0
    for rel, files, dirs in walk_dirs(root):
        rp = os.path.join(root, rel, "_README.md") if rel != "." else os.path.join(root, "_README.md")
        autolist = gen_autolist(root, rel)
        block = "\n\n%s\n%s\n%s\n" % (MARK_START, autolist, MARK_END)
        if os.path.exists(rp):
            text = read(rp)
            if MARK_START in text and MARK_END in text:
                head = text.split(MARK_START)[0].rstrip()
                new_text = head + block
            else:
                new_text = text.rstrip() + block
            if new_text != text:
                write(rp, new_text)
                refreshed += 1
                print("刷新: %s/_README.md" % rel)
        else:
            name = os.path.basename(rel) if rel != "." else "技能根"
            head = "# %s 说明\n\n> ⚠️ 本说明由 doc_sync.py 自动生成。请在下方补充本目录的语义说明（定位/用法/上下游），自动文件清单见文末。\n\n<!-- 人工说明区（doc_sync 保留此区，不会覆盖） -->\n（待补充）" % name
            write(rp, head + block)
            made += 1
            print("生成: %s/_README.md" % rel)
    print("完成：新建 %d 个，刷新 %d 个" % (made, refreshed))


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "scan"
    root = DEFAULT_ROOT
    if "--root" in args:
        i = args.index("--root")
        root = os.path.abspath(args[i + 1])
    if cmd == "update":
        do_update(root)
    elif cmd == "check":
        sys.exit(do_scan_or_check(root, check=True))
    else:
        do_scan_or_check(root, check=False)


if __name__ == "__main__":
    main()
