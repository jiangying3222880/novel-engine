---
name: ne-memory
description: 小说状态落库、跨会话续写与检索（S4）。当用户说"存盘""落库""续写上次的""跨会话恢复""检索前文""更新叙事总览""写 Change Report"时使用。含滚动窗口与六状态文件维护。
version: 2.1.1
agent_created: 2026-10-15
---

# ne-memory · 落库与续写（S4）

## 一、S4 原子四步（顺序不可乱）

```
1. 暂存    Change Report → 先写盘，不直接改状态
2. 校验    python ../ne-tools/runtime/verify.py --root <项目根> --scope settle
3. 提交    原子更新 6 状态文件 → 元数据/index → 日志 → 叙事总览 → 索引
4. 回滚    校验失败则回滚到暂存前，不留下半截状态
```

**未输出"更新确认清单" = 未完成。Change Report 为空 = 注水，打回。**

详见 `./references/hooks-and-memory.md` + `./references/change-report-spec.md`。

## 二、六状态文件（`故事/真相/`）

| 文件 | 内容 |
|---|---|
| `worldview.md` | 世界观硬规则 |
| `characters.md` | 角色状态（含声线） |
| `facts.md` | 已确立事实 |
| `objects.md` | 关键物品/资源 |
| `hooks.md` | 伏笔与钩子状态 |
| `timeline.md` | 时间线 |

每个文件维护 5 通用字段：`status` / `transition` / `valid_until` / `visibility` / `source_chapter`，供检索与一致性校验共用。

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
