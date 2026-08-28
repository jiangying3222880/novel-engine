---
name: novel-engine
description: 工业级网文写作与长篇状态管理引擎，解决AI写作呆板、假自检与上下文溢出问题。
version: 1.3.0
---

# Novel Engine v1.3 (小说创作引擎)

纯 Markdown 文件状态机，零 Python 依赖，跨平台运行。**技能只存模板，项目存内容。**

## 写作三铁律（写前必读）

1. **写前必读**：创作前必须且仅读取项目目录下 `story/truth/` 4个状态文件（characters/world/hooks/relationships）+ `novel-config.json` + 上一章 Frontmatter。禁止全量加载设定集——全量加载会导致上下文溢出、Agent 跳读、声线崩塌。
2. **章节优先**：以"章节"为唯一基本单元。所有因果链、钩子状态、情绪弧统一记入章节 Frontmatter 元数据，不另建中间文件。
3. **写后自检**：初稿完成后必须执行 4 问行为验证自检。无正文 `evidence_ids` 证据链的自检报告一律判定无效，必须重检。修正最多 3 轮，保留 Best Version。

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
- 入口 A：对话建立 config/世界观/角色/大纲 → 从 `templates/truth/` 初始化状态文件 → 进入对标书拆解环节
- 入口 B：读取已有材料 → 映射到标准结构 → 从当前章节往前推3章重建状态 → 进入对标书拆解环节

**对标书拆解环节（可选但强烈推荐）：**

> **池子是拆解出来的，不是建出来的。空池子没有价值。**
>
> | 拆解项目 | 时间投入 | 产出价值 |
> |----------|----------|----------|
> | 选3本对标书 | 30分钟 | ★★★ |
> | 拆1本 Planner（卷结构） | 1-2小时 | ★★★★★ |
> | 拆1本 Author DNA（风格） | 30-60分钟 | ★★★★ |
> | 拆1本 Unit（前10章事件） | 2-4小时 | ★★★★ |
> | 拆1本 Reference（精选段落） | 1-2小时 | ★★★ |
> | 拆1本 Knowledge（知识点） | 30分钟 | ★★ |
>
> **最低投入方案（2小时）**：选1本 + 拆Planner + 拆Author DNA
> **推荐方案（5-8小时）**：选3本 + 重点拆1本全五项 + 另两本拆Planner+DNA
>
> **入池深度档位（影响token消耗）：**
> - 轻量：仅 Planner + Author DNA（约增加 2-3KB/章）
> - 标准：以上 + Reference 精选段落（约增加 4-6KB/章）
> - 全量：五项全拆（约增加 8-12KB/章）
>
> 向用户提供以上选项，用户决定拆解深度和入池档位后，按 `templates/pools/_README.md` 中的模板引导拆解。
> 拆解完成后进入①。

---

## 五阶段 SOP 执行路由

当用户已有项目文件且发出"写下一章""规划第X章""开始写作"等指令时，严格按顺序触发：

### 阶段①：本章规划 (Planning)
- 读取参考：`references/01-session-start.md`
- **强制加载状态（必须全部读取）**：
  - `story/truth/characters.md` —— 基线摘要 + 当前状态（位置/情绪/知识/携带物品）
  - `story/truth/world.md` —— 核心规则 + 当前状态（时间/地点/环境）
  - `story/truth/hooks.md` —— 伏笔追踪
  - `story/truth/relationships.md` —— 关系网络
  > 若文件不存在，从 `templates/truth/` 初始化后再继续。
- **推荐加载（按场景）**：
  - `pools/reference/techniques/` 对应技巧 —— 知道方法论
  - `pools/author_dna/` 主对标书DNA —— 校准风格
  - `pools/planner/` 卷结构参考 —— 校准节奏
- 读入数据：`novel-config.json` → `设定/角色声线.md`（新角色/声线存疑时才读）→ 上一章 Frontmatter
- **加载确认（必须输出）**：
  - [x] characters.md 已读取（N 个角色）
  - [x] world.md 已读取
  - [x] hooks.md 已读取（X 个 active）
  - [x] relationships.md 已读取
- 新角色检查：有新角色 → 建基线档案存入 `设定/角色声线.md` + 更新 characters.md 基线摘要
- 章态注入：为本章出场角色生成声线章态（必须落在基线光谱内；状态冲突按5级优先级裁决：世界规则 > 硬边界 > 核心性格 > 章态 > 剧情需求）
- 产出：**规划清单 + Hook计划 + 本章声线章态**

### 阶段②：正文写作 (Drafting)
- 读取参考：`references/02-writing-guide.md`
- 按需调取：`pools/reference/samples/` 同类场景样本
- 执行：按规划清单+章态写作，有重点对话戏时先做嘴心5问隐式思考
- 产出：**带 Frontmatter 元数据的正文初稿**

### 阶段③：行为验证自检 (Reviewing)
- 读取参考：`references/04-self-review.md`
- 执行：4 问**行为验证**自检（检测正文中是否存在可观察的行为模式），每问必须标注 `evidence_ids`（引用原文片段，格式：`source: [角色/场景名] excerpt: [原文片段]`）
- 修正循环：最多 3 轮，保留 **Best Version**（每轮打综合分，最终输出分数最高的版本）
- 输出状态标记：`full_pass` / `partial_pass` / `needs_human_review`
- 产出：**带证据链的自检报告 + 最终正文版本**

### 阶段④：反 AI 味润色 (De-AI Process)
- 读取参考：`references/03-anti-ai.md`
- 执行：对照三大 AI 味模式做**行为检测**，命中则按**四大转换原则**（心理→动作/解释→结果/对称→不对称/总结→落物）做最小修改。参考对照式示范（AI版→转换过程→目标版）
- 产出：**精修稿**

### 阶段⑤：状态落库 (Settling)
- 读取参考：`references/05-hooks-and-memory.md` + `references/change_report_spec.md`
- 执行：
  1. 生成本章 **Change Report**（角色变化/新伏笔/伏笔回收/时间线/世界规则变化/关系变化）
  2. 根据 Change Report 更新 `story/truth/` 下的 4 个状态文件
  3. 保存正文 Frontmatter（含 change_summary）
- **更新确认（必须输出）**：
  - [x] characters.md 已更新
  - [x] world.md 已更新
  - [x] hooks.md 已更新
  - [x] relationships.md 已更新
- 产出：**Change Report + 项目最新状态**

---

## 体积红线

- 单状态文件 ≤ 8KB
- 单次对话强制加载总量 ≤ 12KB
- SKILL.md 本身 ≤ 5KB（本文件即为路由入口，不含写作细节）

## 文件索引（技能级 = 模板 + 参考）

| 文件 | 用途 | 触发阶段 |
|------|------|---------|
| `references/00-project-setup.md` | 项目初始化（从零创建/导入已有） | ⓪ |
| `references/01-session-start.md` | 项目启动与规划 SOP | ① |
| `references/02-writing-guide.md` | 冰山法则 + 对话不对称 + 章态 + 示范 | ② |
| `references/03-anti-ai.md` | 对照式转换示范 + 四大转换原则（跨题材通用） | ④ |
| `references/04-self-review.md` | 4 问行为验证自检 + 3轮修正 + Best Version | ③ |
| `references/05-hooks-and-memory.md` | 伏笔追踪 + 4 级记忆 | ⑤ |
| `references/07-workflow-detail.md` | 5 阶段 SOP 交互详解 | 全程 |
| `references/change_report_spec.md` | Change Report 格式规范 | ⑤ |
| `templates/novel-config.json` | 项目配置预设 | ⓪ |
| `templates/chapter-template.md` | 章节 Frontmatter 模板 | ② |
| `templates/voice-profile-template.md` | 角色声线基线档案模板 | ① |
| `templates/truth/` | 4个状态文件模板 | ⓪ |
| `templates/pools/_README.md` | 池子总说明（成本/使用原则/快速开始） | ⓪ |
| `templates/pools/unit/_template.md` | 语义单元模板 | ⓪⑤ |
| `templates/pools/author_dna/_template.md` | Author DNA 模板 | ⓪ |
| `templates/pools/planner/_template.md` | 结构分析模板 | ⓪ |
| `templates/pools/knowledge/_README.md` | 知识池说明 | ⓪ |
| `templates/pools/reference/_README.md` | 素材池说明 | ⓪ |

> **项目级文件**（每本书独立，不在技能目录中）：
> - `story/truth/` — 4个状态文件（基线摘要+当前状态，强制加载）
> - `pools/` — 5个素材池（对标书拆解+写作积累，按需加载）
> - `设定/` — 完整设定档案（按需读取）
> - `大纲/` — 卷纲 + 逐章细纲
> - `正文/` — 章节正文
