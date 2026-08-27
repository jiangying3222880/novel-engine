---
name: novel-engine
description: 工业级网文写作与长篇状态管理引擎，解决AI写作呆板、假自检与上下文溢出问题。
version: 1.1.0
---

# Novel Engine v1.1 (小说创作引擎)

纯 Markdown 文件状态机，零 Python 依赖，跨平台运行。

## 写作三铁律（写前必读）

1. **写前必读**：创作前必须且仅读取 `novel-config.json`、`hooks.md` 及上一章 Frontmatter。禁止全量加载设定集——全量加载会导致上下文溢出、Agent 跳读、声线崩塌。
2. **章节优先**：以"章节"为唯一基本单元。所有因果链、钩子状态、情绪弧统一记入章节 Frontmatter 元数据，不另建中间文件。
3. **写后自检**：初稿完成后必须执行 4 问举证自检。无正文 `evidence_ids` 证据链的自检报告一律判定无效，必须重检。

---

## 执行路由

根据用户指令判断入口：

| 用户指令 | 路由 |
|---------|------|
| "开新书""帮我建项目""开始写新书" | → 阶段⓪入口A |
| "导入""我有设定/大纲""把已有项目导进来" | → 阶段⓪入口B |
| "写下一章""规划第X章""继续写" | → 阶段①（需已有 novel-config.json） |

### 阶段⓪：项目初始化 (Setup)

**入口 A（从零创建）或入口 B（导入已有）**
- 读取参考：`references/00-project-setup.md`
- 入口 A：对话建立 config/世界观/角色/大纲/hooks → 完成后进入①
- 入口 B：读取已有材料 → 映射到标准结构 → 完成后进入①

---

## 五阶段 SOP 执行路由

当用户已有项目文件且发出"写下一章""规划第X章""开始写作"等指令时，严格按顺序触发：

### 阶段①：本章规划 (Planning)
- 读取参考：`references/01-session-start.md` + `references/06-knowledge-pack.md`
- 读入数据：`novel-config.json` → `hooks.md` → `设定/角色声线.md` → 上一章 Frontmatter
- 新角色检查：有新角色 → 建基线档案存入 `设定/角色声线.md`
- 章态注入：为本章出场角色生成声线章态（必须落在基线光谱内）
- 产出：**规划清单 + Hook计划 + 本章声线章态**

### 阶段②：正文写作 (Drafting)
- 读取参考：`references/02-writing-guide.md`
- 执行：按规划清单+章态写作，有重点对话戏时先做嘴心5问隐式思考
- 产出：**带 Frontmatter 元数据的正文初稿**

### 阶段③：举证自检 (Reviewing)
- 读取参考：`references/04-self-review.md`
- 执行：4 问自检，每问必须标注 `evidence_ids`（正文行号/段落）
- 产出：**带证据链的客观自检报告**（举证失败则修正初稿后重检）

### 阶段④：反 AI 味润色 (De-AI Process)
- 读取参考：`references/03-anti-ai.md`
- 执行：逐段对照三大AI味模式（乒乓球短句/段末升华/解释腔），命中则按示范重构
- 产出：**最终可发布精修稿**

### 阶段⑤：状态落库 (Settling)
- 读取参考：`references/05-hooks-and-memory.md`
- 执行：更新 hooks.md 状态 + 更新 memory + 保存正文 Frontmatter
- 产出：**项目最新状态**

---

## 体积红线

- 单文件 ≤ 8KB
- 单次对话加载总量 ≤ 12KB
- SKILL.md 本身 ≤ 4KB（本文件即为路由入口，不含写作细节）

## 文件索引

| 文件 | 用途 | 触发阶段 |
|------|------|---------|
| `references/00-project-setup.md` | 项目初始化（从零创建/导入已有） | ⓪ |
| `references/01-session-start.md` | 项目启动与规划 SOP | ① |
| `references/02-writing-guide.md` | 冰山法则 + 对话不对称 + 章态 + 示范 | ② |
| `references/03-anti-ai.md` | 3 大AI味模式 + 高质感示范文本 | ④ |
| `references/04-self-review.md` | 4 问举证自检（含OOC检测） | ③ |
| `references/05-hooks-and-memory.md` | 伏笔追踪 + 4 级记忆 | ⑤ |
| `references/06-knowledge-pack.md` | 8 大写作技巧分类索引 | ① |
| `references/07-workflow-detail.md` | 5 阶段 SOP 交互详解 | 全程 |
| `templates/novel-config.json` | 项目配置预设 | ① |
| `templates/chapter-template.md` | 章节 Frontmatter 模板 | ② |
| `templates/voice-profile-template.md` | 角色声线基线档案模板 | ① |
