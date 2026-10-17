---
name: ne-memory
description: 小说状态落库、跨会话续写与检索（S4）。当用户说"存盘""落库""续写上次的""跨会话恢复""检索前文""更新叙事总览""写 Change Report"时使用。含滚动窗口与六状态文件维护。
version: 2.1.6
agent_created: 2026-10-15
---

# ne-memory · 落库与续写（S4）

## 一、S4 原子四步（顺序不可乱）

```
1. 暂存    Change Report（必须含 WORLD-TICK 五行）→ 先写盘，不直接改状态
2. 校验    python ../ne-tools/runtime/verify.py --root <项目根> --scope settle
3. 提交    ① python ../ne-tools/runtime/world_tick.py --root <项目根> --apply   ← 先机器推进
           ② 再手写其余 4 状态文件 → 元数据/index → 日志 → 叙事总览 → 索引
4. 回滚    校验失败则回滚到暂存前，不留下半截状态
```

> **3① 是 v2.1.3 的新步骤，不能跳**：world.md / timeline.md 现在由 world_tick.py 从
> Change Report 的 WORLD-TICK 区自动推进。手改这两个文件 = 与机器推进打架，且同一条事件
> 会被写成两遍（两遍必然对不上）。世界时钟停在旧章 → settle 判 FAIL。

**未输出"更新确认清单" = 未完成。Change Report 为空 = 注水，打回。
WORLD-TICK 区为空 = 世界没推进，打回。**

详见 `./references/hooks-and-memory.md` + `./references/change-report-spec.md`。

## 二、六状态文件（`故事/真相/`）

| 文件 | 内容 |
|---|---|
| `world.md` | 世界状态 + 硬规则 **【自动】**（当前状态/地点状态机 由 world_tick 推进；时间线已移出，不再在此登记） |
| `characters.md` | 角色状态（含声线） |
| `relationships.md` | 角色关系网络 + 量化距离 |
| `objects.md` | 关键物品/资源 **+ 已确立事实台账**（金额/约定/数值锚点，S3 核对依据） |
| `hooks.md` | 伏笔与钩子状态 |
| `timeline.md` | 时间线 **【自动】**（时间线唯一真相源，由 world_tick 推进） |

> 唯一口径源 = `../ne-setup/templates/truth/` 下 6 个模板文件。
> 历史上有过 `facts.md` / `worldview.md` 两套异名（本文件曾列 facts 而未列 relationships），<!-- truth-naming-exempt -->
> 现已统一——外部文档若仍写异名，一致性核对会指向不存在的文件。

通用字段 3 必填：`status` / `visibility` / `source_chapter`；
`transition` / `valid_until` 为**预留**，按需补充（写不写都不算错）。供检索与一致性校验共用。

**单状态文件 ≤ 8KB**，超了拆子文件。

## 三、滚动窗口（跨会话续写的命门）

S1 读历史细纲时**只读 N-5 ~ N 章**，且**只取冲突链 + 信息释放两节**，不读全文。
这是防上下文溢出的硬规则——全量加载会导致跳读和声线崩塌。

> ⚠️ `细纲摘要_卷X.md` 在旧文档里标为"可选"，但 F-01 跨会话续写又要求"强制重读摘要"。
> **可选 = 大概率没人做**，这条链以前是虚的。现在按强制产物处理：每卷落库时必须生成。

## 四、流程日志（每章必填）

模板：`./templates/log-template.md`

**必须记录**：
- `execution_mode`（multi / single / no_python）
- 输入包存档（S2 实际拿到了哪些文件）
- 降级声明（若有）

命名与阶段一律用 **S1-S4**，不要写"④润色"之类已废弃的阶段号（v1.9 起润色并入 S3）。

## 五、叙事总览（Obsidian 展示层）

- 根 MOC：`叙事总览.md`，模板在 `./templates/narrative/叙事总览.md`
- 6 个骨架页：`templates/narrative/0*.md`（00 作品总览 / 01 角色总览 / 02 世界观总览 / 03 伏笔追踪 / 04 章节地图 / 05 关系网）
- 每 5 章全量对齐一次；仅在 `modules.obsidian_overview = true` 时启用

**只建空目录不复制骨架 = 缺陷**（曾导致总览全空）。

## 六、检索

- **BM25 必跑**（`../ne-tools/runtime/index.py`）
- **ZVEC 可选**（未装 SDK 自动降级 BM25 + 提醒，不自动装）
- 规则见 `./references/retrieval.md`

## 七、跨会话恢复

会话开始时读 `./references/session-start.md`：加载角色状态最小摘要 + 滚动窗口 + 声线透传标注，然后才能续写。
