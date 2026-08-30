<!--
> 📍 **位置**：状态中心 → 伏笔追踪库
> ⬆️ **上游**：阶段①强制加载；阶段⑤通过 Change Report 更新
> ⚠️ **必读前置**：无（项目初始化时从模板创建，后续持续更新）
> 📚 **相关参考**：
> - `references/05-hooks-and-memory.md` — 伏笔管理与状态落库指南
> - `references/change_report_spec.md` — 变更报告格式
> ⬇️ **下游**：阶段①规划（检查伏笔债务）/ 阶段②写作（埋伏笔）/ 阶段③自检（检查伏笔回收）
-->
---
# 伏笔追踪库
# status: active（生效中） / resolved（已回收） / abandoned（已废弃） / pending（未埋设）
# v1.4 功能七 G 定稿：新增【推进状态 status_progress】+【下一回收点 next_resolved_at】两列
# status_progress: pending(未动) / partial(部分揭示) / due(临近回收)
# 5 通用字段：status / transition / valid_until / visibility / source_chapter
# 阶段①强制加载；每章结束后通过 Change Report 更新
---

| ID | 类型 | 内容 | 埋设章(source_chapter) | 计划回收章 | 实际回收章 | 推进状态 | 下一回收点 | 状态 | 可见性 |
|----|------|------|--------|------------|------------|----------|------------|------|--------|
| h_001 | mystery/emotion/chekhov | （伏笔内容） | 1 | （计划章节） | - | pending | - | active | public |
| h_002 | （类型） | （内容） | （章节） | （计划章节） | - | pending | - | active | public |

> **类型说明**：
> - mystery：悬念/谜题类
> - emotion：情感/关系类
> - chekhov：契诃夫之枪（道具/设定回收）
> - identity：身份反转类
>
> **推进状态规则（G 定稿）**：
> - 部分揭示时：status 仍为 active（防剧透不泄底），status_progress=partial，计划回收章更新为"已揭示 X + 剩 Y"，并登记 next_resolved_at=下一回收点章号
> - 伏笔债务检测排除"partial 仍在推进"的行（active 超期未推进 ≠ partial 继续推进）
> - 完整回收时：status=resolved + 实际回收章，status_progress + next_resolved_at 清空
>
> 每章结束后，通过 Change Report 记录新埋设/推进/回收的伏笔，同步更新本表。
