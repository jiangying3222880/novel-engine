# references — 五阶段执行参考库

> 五阶段 SOP 的详细执行规范 + 跨阶段能力文档。SKILL.md 路由的下游落点，按阶段按需加载。

## 定位

`references/` 是阶段⓪-⑤ 的**执行规范库**，一个阶段一个专项文件；另含跨阶段能力文档。执行到某阶段时从本目录加载对应文件，不一次性全读。

## 文件分组

- **阶段文件**：project-setup（⓪初始化）/ session-start（①规划）/ writing-guide（②正文）/ self-review（③自检）/ anti-ai（④反AI味）/ hooks-and-memory（⑤落库）
- **跨阶段能力**：retrieval（检索层）/ identity-routing（身份路由）/ prompt-defense（提示词防御）/ change-report-spec（Change Report）/ chat-outsource（外包分支）/ workflow-detail（SOP 交互）
- **去AI味三件套**：`anti-ai.md`（速查骨架）→ `anti-ai-示范库.md`（四类真人对照）/ `anti-ai-词级信号.md`（词级信号）
- **深度方法库**：`human-signal-zh.md`（主文件）→ `human-signal-模式库.md`（27 模式）

## 使用

1. 按 `SKILL.md` / `routes/index.md` 的路由读取对应阶段文件。
2. 去 AI 味时先读 `anti-ai.md` 骨架；需要真人示范/词级信号时再展开对应子文件。
3. 修改本目录文件后，运行 `python runtime/doc_sync.py update` 刷新下方自动清单。

---

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| anti-ai-示范库.md | 20.2K | 2. 对照式转换示范（选自公开出版文本，覆盖四种截然不同的题材） | 2026-09-01 |
| anti-ai-词级信号.md | 3.8K | 6. 词级 AI 味信号（诊断 → 真人引导，不是禁止） | 2026-09-01 |
| anti-ai.md | 10.1K | 阶段④：叙事质感指南 | 2026-09-01 |
| change-report-spec.md | 3.0K | Change Report 格式规范 | 2026-09-01 |
| chat-outsource.md | 4.8K | 1. 何时用 / 何时不用 | 2026-09-01 |
| hooks-and-memory.md | 6.7K | 阶段⑤：状态落库与 Change Report | 2026-09-01 |
| human-signal-zh.md | 11.0K | 去 AI 味方法库（human-signal 沉淀） | 2026-09-01 |
| human-signal-模式库.md | 5.2K | 五、高频 AI 味模式库（完整版 · 04 §1 四模式的扩充） | 2026-09-01 |
| identity-routing.md | 3.2K | 身份路由（作者 × 平台 × 题材 × 阶段 → 专业身份） | 2026-08-31 |
| project-setup.md | 14.7K | 阶段⓪：项目初始化指南 | 2026-09-01 |
| prompt-defense.md | 4.3K | 提示词防御（Prompt Defense） | 2026-08-31 |
| retrieval.md | 8.0K | 检索层（功能八 · BM25+FTS 默认 + ZVEC 可选） | 2026-08-31 |
| self-review.md | 8.9K | 阶段③：行为验证自检协议 | 2026-09-01 |
| session-start.md | 7.1K | 阶段①：项目启动与本章规划 SOP | 2026-08-31 |
| short-story.md | 5.8K | 短故事创作模式（Short Story） | 2026-09-01 |
| workflow-detail.md | 5.6K | 5 阶段 SOP 交互详解 | 2026-09-01 |
| writing-guide.md | 8.7K | 阶段②：正文写作指南 | 2026-09-01 |
<!-- AUTO-LIST-END -->
