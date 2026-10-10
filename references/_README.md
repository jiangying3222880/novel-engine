# references — 五阶段执行参考库

> 五阶段 SOP 的详细执行规范 + 跨阶段能力文档。SKILL.md 路由的下游落点，按阶段按需加载。

## 定位

`references/` 是阶段⓪-⑤ 的**执行规范库**，一个阶段一个专项文件；另含跨阶段能力文档。执行到某阶段时从本目录加载对应文件，不一次性全读。

## 文件分组

- **阶段文件**：project-setup（⓪初始化）/ session-start（①规划）/ writing-guide（②正文）/ self-review（③自检）/ anti-ai（④反AI味）/ hooks-and-memory（⑤落库）
- **跨阶段能力**：retrieval（检索层）/ identity-routing（身份路由）/ prompt-defense（提示词防御）/ change-report-spec（Change Report）/ chat-outsource（外包分支）/ workflow-detail（SOP 交互）
- **去AI味三件套**：`anti-ai.md`（速查骨架）→ `anti-ai-示范库.md`（四类真人对照）/ `anti-ai-词级信号.md`（词级信号）
- **深度方法库**：`human-signal-zh.md`（主文件）→ `human-signal-模式库.md`（27 模式）
- **短故事创作**：`short-story.md`（三段式憋压爆发 + §1.5 驱动标注写前必填）→ `short-story-rhythm-origin.md`（憋压原理·用户验证版）/ `short-story-engines.md`（六引擎：情绪债务×兑现）
- **叙事内核（写前地基）**：`narrative-kernel.md`（L0/L1 冻结内核表 + 编译落点，修改须走 CCP+用户批准）
- **版本与模型**：`变更历史.md`（各版本 job 明细）/ `model-guide.md`（各阶段模型推荐）/ `target-focus.md`（目标焦点管理）

## 使用

1. 按 `SKILL.md` / `routes/index.md` 的路由读取对应阶段文件。
2. 去 AI 味时先读 `anti-ai.md` 骨架；需要真人示范/词级信号时再展开对应子文件。
3. 修改本目录文件后，运行 `python runtime/doc_sync.py update` 刷新下方自动清单。

---

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| anti-ai-swaps.md | 3.0K | anti-ai-swaps.md — 功能导向换法表（写作纪律 ·  | 2026-09-04 |
| anti-ai-示范库.md | 20.2K | 2. 对照式转换示范（选自公开出版文本，覆盖四种截然不同的题材） | 2026-09-01 |
| anti-ai-词级信号.md | 6.0K | 6. 词级 AI 味信号（诊断 → 真人引导，不是禁止） | 2026-10-08 |
| anti-ai.md | 15.0K | 叙事质感指南（AI 味判定与表达问题打回依据） | 2026-10-10 |
| change-report-spec.md | 3.0K | Change Report 格式规范 | 2026-09-01 |
| chat-outsource.md | 5.8K | 1. 何时用 / 何时不用 | 2026-09-04 |
| consistency-checklist.md | 2.3K | 阶段③ · 一致性自检清单（人工） | 2026-09-04 |
| execution-modes.md | 7.0K | 执行模式与物理隔离（Execution Modes · v1.9） | 2026-10-10 |
| hooks-and-memory.md | 10.4K | S4 落库：状态落库与 Change Report | 2026-10-10 |
| human-signal-zh.md | 11.0K | 去 AI 味方法库（human-signal 沉淀） | 2026-09-01 |
| human-signal-模式库.md | 5.2K | 五、高频 AI 味模式库（完整版 · 04 §1 四模式的扩充） | 2026-09-01 |
| identity-routing.md | 6.0K | 身份路由（作者 × 平台 × 题材 × 阶段 → 专业身份） | 2026-09-04 |
| model-guide.md | 8.4K | 模型文档 · 各阶段适用模型与提示策略 | 2026-10-08 |
| module-registry.md | 6.4K | 模块注册表（Module Registry · Agent 调度版  | 2026-10-10 |
| module-说明书.md | 5.4K | 模块说明书（Module Guide · 用户决策版 · v1.8） | 2026-10-10 |
| narrative-kernel.md | 7.9K | 叙事内核（Narrative Kernel · 冻结版） | 2026-10-08 |
| project-setup.md | 16.5K | 阶段⓪：项目初始化指南 | 2026-10-10 |
| prompt-defense.md | 4.3K | 提示词防御（Prompt Defense） | 2026-08-31 |
| retrieval.md | 9.1K | 检索层（功能八 · BM25+FTS 默认 + ZVEC 可选） | 2026-09-02 |
| self-review.md | 15.3K | S3 检验：行为验证 + 双视角评估协议 | 2026-10-10 |
| session-start.md | 9.5K | S1 骨架：项目启动与本章细纲 SOP | 2026-10-10 |
| short-story-engines.md | 11.8K | 短篇文梗引擎库（Short Story Engines） | 2026-10-08 |
| short-story-rhythm-origin.md | 2.5K | 短故事节奏原理（用户验证版） | 2026-09-04 |
| short-story.md | 15.7K | 短故事创作模式（Short Story） | 2026-10-10 |
| target-focus.md | 6.7K | 目标焦点管理：PMC Suppression 机制与 Skill 实 | 2026-10-08 |
| workflow-detail.md | 15.7K | S1-S4 物理隔离流水线详解（v1.9） | 2026-10-10 |
| writing-guide.md | 15.5K | 阶段②：正文写作指南（S2 血肉 · 讲述者） | 2026-10-10 |
| 变更历史.md | 25.5K | 变更历史（novel-engine） | 2026-10-10 |
| 商业立意与题材选择.md | 4.8K | 商业立意与题材选择 | 2026-10-08 |
| 技法速查索引.md | 11.2K | 技法速查索引（Technique Quick Index） | 2026-10-10 |
| 简介写法.md | 3.2K | 简介写法 | 2026-10-08 |
| 读者吸引技法.md | 3.7K | 读者吸引技法 | 2026-10-08 |
<!-- AUTO-LIST-END -->
