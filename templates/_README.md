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

## 使用

1. 初始化时整目录复制到项目，再按本书填内容。
2. 修改模板后运行 `python runtime/doc_sync.py update` 刷新自动清单。

---

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| chapter-template.md | 1.5K | 第X章 章节标题 | 2026-09-01 |
| log-template.md | 4.4K | 章节流程日志：第 X 章 | 2026-09-01 |
| outsource-prompt.md | 3.2K | 外包写作 · 最终提示词模板（自包含） | 2026-09-01 |
| short-story-template.md | 1.5K | 短故事骨架模板 | 2026-09-04 |
| voice-profile-template.md | 2.1K | 角色声线基线档案模板 | 2026-08-31 |
| 细纲模板.md | 1.9K | 细纲模板：第 X 章 | 2026-09-01 |

### 子目录

- `identity/` （有说明）
- `meta/` （有说明）
- `narrative/` （有说明）
- `pools/` （有说明）
- `truth/` （有说明）
<!-- AUTO-LIST-END -->
