<!--
> 📍 **位置**：状态中心 → 物品状态库
> ⬆️ **上游**：阶段①强制加载；阶段⑤通过 Change Report 更新
> ⚠️ **必读前置**：无（项目初始化时从模板创建，后续持续更新）
> 📚 **相关参考**：`references/change-report-spec.md` · `references/hooks-and-memory.md`
> ⬇️ **下游**：阶段②写作（道具使用）/ 阶段⑤落库（持有链更新）
-->
---
# 物品状态库（objects.md · 功能七新增）
# 状态机 artifact：owned · lost · destroyed · sealed · transferred
# 5 通用字段：status / transition / valid_until / visibility / source_chapter
# 阶段①强制加载；每章结束后通过 Change Report 更新
---

| 物品ID | 名称 | 状态 | 当前持有者 | 持有链历史 | 关键性 | 产生于章(source_chapter) | 可见性(visibility) | 备注 |
|--------|------|------|-----------|-----------|--------|--------------------------|--------------------|------|
| obj_001 | （物品名） | owned | （持有者） | 谁→谁→谁 | plot-critical / 普通 | 1 | public | （用途/去向） |

> **关键性说明**：
> - plot-critical：登记归属与去向，防"凭空消失或凭空出现"（契诃夫之枪类道具）
> - 普通：一次性道具/环境道具，可随场景退场
>
> 每章结束，通过 Change Report 记录持有链变化、物理状态变化，同步更新本表。
