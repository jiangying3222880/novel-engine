# Novel Engine v1.1

工业级网文写作 Skill，纯 Markdown 驱动，零 Python 依赖。

## 解决什么问题

| 痛点 | 本引擎方案 |
|------|-----------|
| AI 写作呆板 | 去硬约束，改示范驱动（Few-shot）；反 AI 味从黑名单重构为质感标杆 |
| Agent 跳读/只读一半 | 单文件 ≤8KB，单次加载 ≤12KB，文件头加"后果提示"利用损失厌恶 |
| Agent 不遵守约束 | 3 条铁律（底线）+ 其余全部降为 Guide；自检强制 evidence_ids 证据链 |
| 假自检 | 4 问必须标注正文行号/段落，无证据的"通过"判定无效 |
| 乒乓球式短句/装酷感 | 对话不对称三原则（答非所问/动作打断/声线不对称）+ 双层声线系统 |
| 不敢留白/解释腔 | 冰山法则（默认读者看过同类作品，只写物理结果不写原理） |
| 角色 OCC（出戏） | 基线档案（永久）+ 章态（每章动态），章态必须落在基线情绪光谱内 |

## 快速使用

1. 将 `novel-engine-v1/` 整个目录复制到 Agent 技能目录
2. 编辑 `templates/novel-config.json` 填入你的作品信息
3. 对 Agent 说"写第1章"即可启动五阶段 SOP
4. 新角色首次登场时，Agent 自动按 `templates/voice-profile-template.md` 建立基线档案

## 五阶段工作流

```
规划(含声线章态) → 写作(含嘴心5问) → 举证自检 → 反AI味润色 → 落库
```

每个阶段只读必要的参考文件，产出明确的交付物，阶段间不传递历史报错。

## 可选：knowledge/ 自定义技巧库

`references/06-knowledge-pack.md` 提供了 8 大通用写作技巧索引。如果某个技巧在你的项目中落地困难，可在**项目目录**下创建 `knowledge/` 目录（与 `设定/`、`大纲/`、`正文/` 同级），为该技巧补充完整示范段落。

**何时建**：当 Agent 读了索引但写出效果不理想时。
**命名规则**：`knowledge/技巧名.md`
**文件格式**：

```markdown
### [技巧名]
核心：[一句话说明]

示范段落：
> [一段完整的好文字示范，200-400字]

关键点：
- [该示范好在哪里，2-3 条]
```

**示例**（`knowledge/延迟满足.md`）：

```markdown
### 延迟满足
核心：读者越想要什么，越不立刻给。

示范段落：
> 老张的刀已经出鞘了。韩铮的手还按在刀柄上，没拔。
> "你不拔刀？"老张问。
> 韩铮没回答。他在等。等老张说完。等他把这辈子想说的狠话全说完。
> 因为说完之后，他就没力气了。

关键点：
- 读者知道韩铮能打，但就是不让他拔刀——延迟
- 章末断在"他就没力气了"——不写结果，读者翻页
```

建好后，Agent 在阶段①规划时会自动读取 `knowledge/` 目录下与本章相关的文件。

## 文件体积控制

- SKILL.md ≤ 4KB（路由入口）
- 每个 reference ≤ 8KB
- 单次对话加载总量 ≤ 12KB
- 全部文件总计 ~32KB

---

## 项目历程

### 第一代：novel-writer-jy v5.4（纯 Skill，硬约束路线）

起点是 `novel-writer-jy`（AI辅助中文网文写作专家 Skill）的 v5.4 版本，核心理念是"用规则约束 AI 写出好文字"。

**做了什么：**
- 100+ 条硬约束：20 条正则黑名单、7 条零容忍铁律、14 项禁止行为
- 20 维审核体系：逐维度打分审查
- 知识库 25 分类：每个分类独立参考文件
- shared.md 14.8KB（所有 Agent 必读）+ planner.md 12KB

**暴露的问题：**
1. **呆板**：100+ 条约束让 Agent 进入防守模式，不再追求写好故事，而是追求"不违规"。文字变成小心翼翼的流水账。
2. **只读一半**：单次必读 27KB 远超 LLM 最佳注意力范围，Agent 跳读后后半部分约束全部失效。
3. **不遵守约束**：约束数量超载（vs Agent 工作记忆 7±2 块）+ 全部"零容忍"导致优先级模糊，Agent 产生假审核（填完检查表直接开写）。
4. **乒乓球短句**：为了规避"AI 长句"检测，Agent 写出一连串极短对话，变成另一种 AI 味——假装克制的装酷感。

### 第二代：novel-writer-pure（Python 项目，重型架构路线）

`novel-writer-pure` 是将 `novel-writer-jy` v5.4 的写作理念工程化为 Python 桌面应用的尝试，核心理念是"用代码强制约束执行 + 多 Agent 协作"。

**做了什么：**
- PySide6 GUI 桌面应用
- SQLite 24 张表的数据层
- 8 个 Agent 协作（Planner/Writer/Auditor/Desloper 等）
- Story Unit 单元架构（拆章→单元→段落三级）
- 20 维评分系统 + Checkpoint 机制

**暴露的问题：**
1. **维护成本失控**：一个人维护数千行 Python + GUI + 数据库，功能越多 bug 越多，最终扛不住。
2. **架构过重**：单元架构增加了认知负担（双时间线、unit 索引、拆章逻辑），但纯 Skill 场景下不需要这么重的中间层。
3. **回到原点**：Python 项目的复杂度最终超过了它要解决的问题。

### 第三代：story-engine-skill v6.0（纯 Skill，Guide 引导路线）

`story-engine-skill` 是从 `novel-writer-pure` 项目回归纯 Markdown Skill 的版本，吸取 v5.4 教训，改用"引导而非禁止"。

**做了什么：**
- Guide 系统替代硬约束
- 单元中心架构（从 novel-writer-pure 继承但简化）
- 4 级记忆系统
- 双时间线、叙事压力计
- 题材自适应

**暴露的问题：**
1. **丢了关键能力**：为了精简，砍掉了 `novel-writer-jy` v5.4 的知识库、Hook 追踪、审核体系、真人感维度。
2. **自身仍有问题**：SKILL.md 11.1KB 仍然偏大，subsystems.md 22.8KB 严重超限，19 步工作流太多。
3. **Agent 仍有 AI 味**：Guide 解决了呆板问题，但没解决句子层面的 AI 味——乒乓球短句、段末升华、解释腔依然存在。

### 第四代：Novel Engine v1.0（融合方案）

综合 `novel-writer-jy` v5.4 和 `story-engine-skill` v6.0 的优点，去除各自的缺陷。

**设计决策：**
- 以 `story-engine-skill` 架构为骨架（Guide 引导 + 文件系统）
- 恢复 `novel-writer-jy` v5.4 丢掉的能力（知识库/Hook/审核），但全部降级为 Guide
- 去单元架构 → 章节中心
- 去心智6问 → 被其他部分覆盖，冗余
- 7 问自检 → 4 问（翻页/OCC/质感/因果）
- SKILL.md ≤4KB，每文件 ≤8KB，5 阶段工作流
- 3 条铁律：写前必读 / 章节优先 / 写后自检
- evidence_ids 强制举证自检
- 纯 Markdown，零 Python 依赖

### 第五代：Novel Engine v1.1（当前版本）

在 v1.0 基础上解决句子层面的 AI 味问题。

**核心改进：**
1. **双层声线系统**：基线档案（永久，防 OCC）+ 章态（每章动态，适应情绪变化）。新角色登场时按模板建基线，每章规划时建章态，章态必须落在基线情绪光谱内。
2. **示范驱动替代黑名单**：03-anti-ai.md 从"6 大检测黑名单"重构为"3 大模式 + 3 段高质感示范文本"。给 Agent 看好文字是什么样的，而不是列 100 条"不许这样写"。
3. **冰山法则**：默认读者看过同类型作品，禁止通过对话/旁白解释设定，只写物理结果。
4. **对话不对称三原则**：答非所问（优先响应内心冲突）、动作打断（台词穿插物理动作）、声线不对称（不同角色用词与节奏严禁对齐）。
5. **自检升级**：Q2 加 OOC 光谱校验，Q3 加质感三大模式检测。

### 设计哲学

**从"控制输出"到"控制输入状态"：**
- `novel-writer-jy` v5.4 试图用 100 条规则控制输出 → 呆板
- `novel-writer-pure` 试图用 Python 代码强制约束 → 维护失控
- `story-engine-skill` v6.0 试图用 Guide 引导 → 丢了关键能力
- Novel Engine v1.0 试图用 evidence_ids 控制质量验证 → 结构对了，文字还有 AI 味
- Novel Engine v1.1 通过注入角色心理状态 + 提供高质量示范，让 Agent 在写作前就进入正确状态
- LLM 底层特性：few-shot learning（样例驱动）远强于 instruction following（指令遵守）

**分层架构：**
- 技能层（通用）：写作方法、声线模板、工作流 SOP — 写在 Skill 文件里，跨项目复用
- 项目层（特定）：角色基线、novel-config、hooks — 项目目录里，每个项目独立
- 章节层（动态）：声线章态、规划清单 — 阶段①输出里，当章用完即弃

## 文件索引

| 文件 | 用途 | 触发阶段 |
|------|------|---------|
| `SKILL.md` | 路由入口 + 3 铁律 + 5 阶段 SOP | 全程 |
| `references/01-session-start.md` | 项目启动 + 角色基线 + 章态注入 | ① |
| `references/02-writing-guide.md` | 冰山法则 + 对话不对称 + 章态 + 示范 | ② |
| `references/03-anti-ai.md` | 3 大 AI 味模式 + 高质感示范文本 | ④ |
| `references/04-self-review.md` | 4 问举证自检（含 OOC 检测） | ③ |
| `references/05-hooks-and-memory.md` | 伏笔追踪 + 4 级记忆 | ⑤ |
| `references/06-knowledge-pack.md` | 8 大写作技巧分类索引 | ① |
| `references/07-workflow-detail.md` | 5 阶段 SOP 交互详解 | 全程 |
| `templates/novel-config.json` | 项目配置预设 | ① |
| `templates/chapter-template.md` | 章节 Frontmatter 模板 | ② |
| `templates/voice-profile-template.md` | 角色声线基线档案模板 | ① |
| `templates/hooks-template.md` | 伏笔记录卡模板 | ⑤ |

## 版本

- v1.0.0：从 novel-writer-jy v5.4（硬约束）+ story-engine-skill v6.0（Guide 引导）融合而来。去单元架构、去心智6问、去 Python 依赖。3 条铁律 + evidence_ids 举证自检 + Frontmatter 状态追踪。
- v1.1.0：引入双层声线系统（基线+章态，防 OCC）、冰山法则（留白）、对话不对称三原则、示范驱动替代黑名单。解决 v1.0 残留的乒乓球短句和段末升华问题。
