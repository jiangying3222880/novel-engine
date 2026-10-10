# templates — 项目初始化模板

> 新建项目时复制到项目对应目录的**模板集**。全部为机器可读/可复制的规范文件。

## 定位

`templates/` 是项目脚手架的来源：初始化时按 `references/project-setup.md` 复制到 `故事/` 等中文目录。**数据层模板（meta/truth）保持零双链、机器可读**；叙事层模板（narrative）才用 Obsidian 双链。

## 子目录

- `meta/` — 章节元数据模板（chapter_XXXX.md + index.md），正文 YAML 的迁出地
- `truth/` — 六份真相状态文件（characters/hooks/objects/relationships/timeline/world），零双链
- `narrative/` — 叙事总览（作品总览/角色/世界观/伏笔/章节地图/关系网），供 Obsidian 可视化
- `identity/` — 身份档案模板（作者/编辑/平台题材）
- `pools/` — 素材池模板（author_dna/planner/reference/unit/knowledge + 拆解方法论 + 拆书规范）

## v1.9 模板说明（S1-S4 流水线产物模板）

- `细纲模板.md`（v1.9 重写）— S1 编剧产出：长篇四维骨架细纲。11 节：骨架模板路由 → 基本信息 → 冲突链叙述形态四节点（想要/阻拦/弄砸/代价）+节级切分 → 情绪弧 → 信息释放 → 声线要求（从角色卡透传标注来源）→ 角色状态最小摘要（知道什么/不知道什么）→ 任务字数 → 伏笔计划 → 主角主动表达节点 → 参考素材槽位 → 章末钩子
- `检验报告模板.md`（v1.9 新增）— S3 检验产出：细纲门核对（硬性结构 + 软性删节推理）→ 正文门核对（骨架逐节点对齐 + evidence）→ 双视角评估（读者+编辑）→ 遮名测试 → 打回方向
- `short-story-template.md`（v1.9 重写）— 短篇 S1 细纲：憋压三段式四维骨架（单链冲突 + 删节推理 + 三段任务字数）+ 细纲门/写后双清单

## 使用

1. 初始化时整目录复制到项目，再按本书填内容。
2. 修改模板后运行 `python runtime/doc_sync.py update` 刷新自动清单。

---

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| chapter-template.md | 1.7K | 第X章 章节标题 | 2026-09-04 |
| log-template.md | 4.5K | 章节流程日志：第 X 章 | 2026-10-10 |
| outsource-prompt.md | 5.1K | 外包写作 · 最终提示词模板（自包含） | 2026-09-04 |
| short-story-template.md | 3.8K | 短篇细纲模板（憋压三段式 · v1.9） | 2026-10-10 |
| voice-profile-template.md | 2.1K | 角色声线基线档案模板 | 2026-08-31 |
| 检验报告模板.md | 3.2K | 检验报告：第 X 章（双视角 · v1.9） | 2026-10-10 |
| 细纲模板.md | 4.7K | 细纲模板：第 X 章（四维骨架 · v1.9） | 2026-10-10 |

### 子目录

- `identity/` （有说明）
- `meta/` （有说明）
- `narrative/` （有说明）
- `pools/` （有说明）
- `truth/` （有说明）
<!-- AUTO-LIST-END -->
