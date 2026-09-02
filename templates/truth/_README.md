# truth 说明

> ⚠️ 本说明由 doc_sync.py 自动生成。请在下方补充本目录的语义说明（定位/用法/上下游），自动文件清单见文末。

<!-- 人工说明区（doc_sync 保留此区，不会覆盖） -->
> 📍 **位置**：6 个状态文件模板（角色/世界/伏笔/关系/物品/时间线）——**强制加载核心**。
> ⬆️ **上游**：阶段⓪初始化生成于 `故事/真相/`；阶段⑤落库用 Change Report 驱动更新。
> 🚀 **使用引导**：
> 1. **每章写前必读**：创作前必须加载 `故事/真相/` 6 个文件（characters/world/hooks/relationships/objects/timeline）+ config + 上一章 meta。
> 2. **机器可读**：truth 是数据层，禁 Obsidian 双链（防污染，影响检索一致性）。
> 3. **通用 5 字段**：status / transition / valid_until / visibility / source_chapter，供检索（防剧透+知情权）与一致性校验共用。
> 4. **更新纪律**：只经阶段⑤ Change Report 更新，正文不直接改真相。
> ⬇️ **下游**：阶段①②③④⑤全程强制加载。

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| characters.md | 2.7K | 角色状态矩阵 | 2026-09-02 |
| hooks.md | 2.2K | 伏笔追踪库 | 2026-09-01 |
| objects.md | 1.4K | 物品状态库（objects.md · 功能七新增） | 2026-09-01 |
| relationships.md | 1.2K | 角色关系网络 | 2026-08-31 |
| timeline.md | 1.4K | 时间线（timeline.md · 功能七新增） | 2026-09-01 |
| world.md | 3.1K | 世界状态 + 时间线 | 2026-09-02 |
<!-- AUTO-LIST-END -->
