<!--
> 📍 **位置**：状态中心 → 时间线
> ⬆️ **上游**：阶段①强制加载；阶段⑤通过 Change Report 更新
> ⚠️ **必读前置**：无（项目初始化时从模板创建，后续持续更新）
> 📚 **相关参考**：`references/hooks-and-memory.md` · `references/identity-routing.md`
> ⬇️ **下游**：阶段②写作（时间锚点）/ 阶段⑤落库（新增时间条目）
-->
---
# 时间线（timeline.md · 功能七新增）
# 用途：全局时间轴，章号 ↔ 故事时间 ↔ 事件
# 防剧透：按 in_story_time 排序时，未来事件自动后置；visibility 区分作者真相/读者已知
# 5 通用字段：status / transition / valid_until / visibility / source_chapter(4位章号)
# 阶段①强制加载；每章结束后通过 Change Report 更新
---

| 章号 | 故事时间 | 事件 | 涉及实体 | 可见性(visibility) |
|------|---------|------|---------|---------------------|
| 1 | （纪元/日期） | （事件） | （实体名） | reader_known / author_truth |

> **visibility 说明**：
> - reader_known：读者已知的事实（可用于正文直接引用）
> - author_truth：作者真相（防剧透，检索时按 cutoff 过滤）
>
> 回溯/连集对齐：写作前按时间线核对"当前故事时间"与"上一章结束时间"是否衔接。
> 每章结束，通过 Change Report 新增时间条目，同步更新本表。
