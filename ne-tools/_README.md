# 技能根 说明

> ⚠️ 本说明由 doc_sync.py 自动生成。请在下方补充本目录的语义说明（定位/用法/上下游），自动文件清单见文末。

<!-- 人工说明区（doc_sync 保留此区，不会覆盖） -->
**脚本与门禁**（不是写作技能，是工程侧）。改技能前后都在这里收口。

- `verify.py` —— 流程门禁（41 项，PASS/WARN/FAIL，退出码 1 = 禁止继续）
- `doc_sync.py` —— 文档同步 + 版本一致性校验（pre-commit 强制）
- `skill_lint.py` —— 技能标准化自检（15 项）
- `world_tick.py` —— 解析 WORLD-TICK 自动推进 world.md / timeline.md
- `selftest_gates.py` —— 门禁回归自测（11 场景 38 断言）
- `deploy.py` —— 同步运行镜像（默认 dry-run）

**脚本实际在 `runtime/` 下**，不是本目录根。

<!-- AUTO-LIST-START: 由 doc_sync.py 自动维护，请勿手改 -->
## 文件清单（自动生成）

| 文件 | 大小 | 用途（首行标题） | 更新 |
|------|------|-------------------|------|
| SKILL.md | 4.1K | ne-tools · 运行时工具 | 2026-10-17 |

### 子目录

- `runtime/` （有说明）
<!-- AUTO-LIST-END -->
