> 全程参考 · 5阶段SOP交互详解 · 路由见 `routes/index.md`

# 5 阶段 SOP 交互详解

## 流程总览

```
用户："写第X章"
    │
    ▼
[阶段① 规划] 读取 story/truth/4文件 + 01-session-start.md
    │ （状态冲突按5级优先级裁决）
    │ （按需加载 pools/ 素材 + techniques 技巧）
    │ 输出：规划清单
    ▼
[阶段② 写作] 读取 02-writing-guide.md
    │ （按需加载 pools/reference/samples/ 同类场景样本）
    │ 输出：正文初稿（无 YAML；元数据写 story/meta/chapter_XXX.md，功能三）
    ▼
[阶段③ 自检] 读取 03-self-review.md
    │ 4问行为验证检测（不是"自夸"，是检测行为模式）
    │ 最多 3 轮修正 + Best Version 保留
    │ 输出：自检报告 + 最终正文版本
    ▼
[阶段④ 润色] 读取 04-anti-ai.md
    │ 对照式转换：AI版 → 转换过程 → 目标版
    │ 输出：精修稿
    ▼
[阶段⑤ 落库] 读取 05-hooks-and-memory.md + change_report_spec.md
    │ 输出：生成 Change Report → 更新 story/truth/4文件 → 保存正文
    ▼
完成，等待用户下一指令
```

## 阶段间交互规范

- 每个阶段完成后，向用户输出该阶段的产出物
- 用户可以喊停修改，修改后从当前阶段继续
- 不要把多个阶段的结果合在一起一次性输出（防止跳过自检）
- 如果用户说"直接写不要规划"，可以跳过阶段①，但必须在正文末尾附上 Frontmatter

## 阶段① 规划交互

```
Agent 读取（强制）：
  story/truth/characters.md — 基线摘要 + 当前状态
  story/truth/world.md — 核心规则 + 当前状态
  story/truth/hooks.md — 伏笔追踪
  story/truth/relationships.md — 关系网络
  novel-config.json — 项目配置
  上一章 Frontmatter — change_summary + emotion_arc

Agent 读取（按需）：
  pools/author_dna/ — 风格校准
  pools/planner/ — 节奏校准
  pools/reference/techniques/ — 对应技巧方法论
  pools/reference/samples/ — 同类场景样本
  设定/角色声线.md — 仅新角色或声线存疑

Agent 内部判断：
  状态冲突？→ 按5级优先级裁决（世界规则 > 硬边界 > 核心性格 > 章态 > 剧情需求）

Agent 输出：规划清单（按 01-session-start.md 模板）
用户确认或修改
```

如果用户说"按你说的来"或"继续"，直接进入阶段②。

## 阶段② 写作交互

```
Agent 读取：02-writing-guide.md（内化写作原则）
Agent 执行：
  1. 有对话戏 → 先在脑中完成嘴心5问
  2. 按规划清单写作
  3. 写完后元数据写入 story/meta/chapter_XXX.md（含 change_summary + review_status，正文无 YAML）
Agent 输出：完整正文初稿
```

写作时不解释"我在用什么技巧"，直接输出正文。

## 阶段③ 自检交互

```
Agent 读取：03-self-review.md
Agent 执行：4 问行为验证检测
  Q1：章末悬念行为检测
  Q2：声线行为检测（对照 characters.md 基线摘要）
  Q3：三大AI味模式行为检测（计数命中数）
  Q4：感官行为检测
  每问必须标注 evidence_ids（原文片段）
Agent 输出：自检报告
```

### 修正循环（最多 3 轮）

```
第1轮自检 → 通过 → 阶段④
        ↘ 未通过 → 修正（只改命中项，不全面重写）→ 第2轮自检
                                        ↘ 通过 → 阶段④
                                        ↘ 未通过 → 再修正 → 第3轮自检
                                                          ↘ 通过 → 阶段④
                                                          ↘ 未通过 → 停止，输出 Best Version
```

### Best Version 保留机制

每轮自检后打一个综合分（1-10，粗略即可），3轮后输出**分数最高的版本**，不一定是第3轮。越改越差时回退到之前的最佳版本。

### review_status 标记

最终 Frontmatter 的 `review_status` 字段：
- `full_pass` — 4/4 全部通过
- `partial_pass` — 3/4 通过，剩余 1 项有瑕疵但可放行
- `needs_human_review` — ≤2/4 通过，需要作者重点审稿

## 阶段④ 润色交互

```
Agent 读取：04-anti-ai.md
Agent 执行：
  1. 逐段扫描 3 大检测模式（乒乓球短句/段末升华/解释腔）
  2. 命中 → 对照四大转换原则（心理→动作/解释→结果/对称→不对称/总结→落物）
  3. 参考对照示范的转换过程，最小修改
  4. 不命中 → 不改
Agent 输出：精修稿（完整正文，不是 diff）
```

润色后简要说明改了什么（命中了几处、改了哪类问题），不要输出完整 diff。

## 阶段⑤ 落库交互

```
Agent 读取：05-hooks-and-memory.md + change_report_spec.md
Agent 执行：
  1. 生成 Change Report（角色/伏笔/时间线/世界规则/关系变化）
  2. 根据 Change Report 更新 story/truth/ 下 6 个状态文件（含 objects/timeline）
  3. 保存正文文件（含 Frontmatter + review_status）
Agent 输出：落库报告
```

落库后提示用户下一章的伏笔债务状态。

## 中断与恢复

如果对话中途断开（compact 或新会话）：
1. 读取最近章节的 Frontmatter 恢复上下文
2. 读取 story/truth/ 6个状态文件（含 objects/timeline）确认当前状态
3. 检查 hooks.md 确认伏笔状态
4. 如果有未完成的自检（阶段③未完成），重新自检
5. 如果正文已落库但自检未做，补做自检后再继续
6. 如果 Best Version 记录丢失，按当前版本继续，不回溯

## 并行写作

不支持。一次只写一章，一章只走一遍完整 SOP。
