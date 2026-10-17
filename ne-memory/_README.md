# ne-memory 说明

> ⚠️ 本说明由 doc_sync.py 自动生成。请在下方补充本目录的语义说明（定位/用法/上下游），自动文件清单见文末。

<!-- 人工说明区（doc_sync 保留此区，不会覆盖） -->
**S4 落库**（档案员·写入态）：Change Report → `verify --scope settle` → 原子更新 6 状态文件。

原子四步：暂存 → 校验 → 提交 → 回滚。**未输出"更新确认清单" = 未完成**。

- 上游：`ne-review`（检验通过）
- 下游：下一章的 S1（滚动窗口）
- 门禁：每章必跑 `verify.py --scope settle`（落库一致 / 世界时钟 / timeline / hooks / 证据链 / 正文质量）

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| SKILL.md | 4.1K | ne-memory · 落库与续写（S4） | 2026-10-17 |

### 子目录

- `references/` （有说明）
- `templates/` （有说明）
<!-- AUTO-LIST-END -->
