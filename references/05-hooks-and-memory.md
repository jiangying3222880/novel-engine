> 阶段⑤ 状态落库与 Change Report · 路由见 `routes/index.md`

<!-- 提示：如果不阅读本文件，会导致：伏笔状态紊乱、长篇逻辑前后矛盾。 -->

# 阶段⑤：状态落库与 Change Report

## 1. 核心原则

- **状态集中在 `story/truth/`**：6个文件（characters / world / hooks / relationships / objects / timeline）是唯一真相中心
- **Change Report 驱动更新**：先出报告，再改状态文件，确保所有变更可追溯
- **池子只放对标书内容**：素材池是高质量对标书的拆解产物，不存自己的稿件

---

## 2. story/truth/ 六层状态体系（功能七 · 5 通用字段）

> 每个实体/状态记录带 5 通用字段：`status` / `transition` / `valid_until` / `visibility` / `source_chapter`。检索（功能八）与一致性校验（时空守门）共用这套字段。

| 文件 | 内容 | 状态机 | 更新频率 |
|------|------|--------|----------|
| `characters.md` | 基线摘要 + 当前状态（位置/情绪/知识/物品） | mortal（alive/missing/false_dead/true_dead/resurrected） | 每章 |
| `world.md` | 核心规则 + 当前状态（时间/地点/环境/大事记）+ 地点阶段 | location_phase（intact/damaged/destroyed/abandoned/rebuilt/transformed） | 每章 |
| `hooks.md` | 伏笔追踪（active/resolved/abandoned/pending + 推进状态） | 推进状态（pending/partial/due） | 每章 |
| `relationships.md` | 关系矩阵 + 量化距离 + 事件史 | relation（ally/support/neutral/tension/hostile/severed/reconciled） | 每章 |
| `objects.md` | 物品状态 + 持有链（【新增】） | artifact（owned/lost/destroyed/sealed/transferred） | 每章 |
| `timeline.md` | 全局时间轴：章号↔故事时间↔事件（【新增】） | 回溯/连集对齐/防剧透 | 每章 |

> **完整设定档案**（`设定/角色声线.md`、`设定/世界观.md`）是深度参考，不在强制加载范围内。只有当声线存疑或需要深挖设定时才读取。

---

## 3. hooks 语法规范

伏笔状态允许四种 + 推进状态（G 定稿）：

| 状态 | 含义 |
|------|------|
| `active` | 已埋下，尚未回收，读者心中有悬念 |
| `resolved` | 已回收，悬念已解答 |
| `abandoned` | 已废弃（需备注原因） |
| `pending` | 已规划但尚未埋设（伏笔计划表） |

| 推进状态 | 含义 |
|---------|------|
| `pending` | 未动 |
| `partial` | 部分揭示（status 仍 active，防剧透不泄底） |
| `due` | 临近回收 |

```markdown
| ID | 类型 | 内容 | 埋设章 | 计划回收章 | 实际回收章 | 推进状态 | 下一回收点 | 状态 |
|----|------|------|--------|------------|------------|----------|------------|------|
| h_001 | mystery | 主角腰间的黑色令牌到底来自哪个门派？ | 1 | 5 | - | pending | - | active |
```

### 推进状态规则（G 定稿）

- **部分揭示**：status 仍 active，status_progress=partial，计划回收章更新为"已揭示 X + 剩 Y"，登记 next_resolved_at=下一回收点章号
- **完整回收**：status=resolved + 实际回收章，status_progress + next_resolved_at 清空

### 伏笔债务管理

- `active` 超过 10 章未推进的钩子标记为"伏笔债务"（**排除 status_progress=partial 仍在推进的行**）
- 每次落库时检查是否有债务，在报告末尾提示用户
- 如果 `active` 超过 20 章未推进，强制在下一章规划中安排推进或废弃

---

## 4. Change Report 生成与落库流程

正文确认后，按以下步骤执行：

### Step 1：生成 Change Report

参照 `references/change_report_spec.md`，生成本章变更报告，包含：

1. **角色变化**：哪些角色的位置/情绪/已知信息/携带物品变了
2. **新伏笔**：本章埋了哪些新伏笔（含部分揭示的推进状态更新）
3. **伏笔回收**：本章回收了哪些旧伏笔
4. **时间线**：故事时间推进了多少（timeline.md 新增条目）
5. **世界规则变化**：有没有新设定确立（world.md 地点阶段更新）
6. **关系变化**：哪些角色关系变了（量化距离变化）
7. **物品变化**：关键道具的持有/物理状态变化（objects.md）
8. **新出场/升级角色检查（D 回填）**：本章台词≥2句的新角色 → 触发 B 类建档（characters.md 加一行精简基线）

### Step 2：更新 story/truth/ 状态文件

根据 Change Report 内容，逐个更新 6 个状态文件：

- `characters.md` → 更新「当前状态」表格，「基线摘要」极少变动；新 B 类角色加一行精简基线
- `world.md` → 更新「当前状态」+「时间线大事记」+ 地点阶段，「核心规则」极少变动
- `hooks.md` → 新伏笔追加行，回收的伏笔改状态 + 填实际回收章；部分揭示更新推进状态/下一回收点
- `relationships.md` → 更新关系矩阵强度 + 量化距离 + 事件史
- `objects.md` → 更新物品持有链/物理状态（plot-critical 道具必须登记去向）
- `timeline.md` → 新增本章时间条目（章号↔故事时间↔事件）

### Step 3：写入元数据 + 日志 + 索引（功能三/四/八）

- **元数据**：写入 `story/meta/chapter_XXX.md`（causal_links / hooks / emotion_arc / change_summary）。**正文文件保持干净无 YAML**（功能三 YAML 迁移）。
- **进度**：更新 `story/meta/index.md`（进度唯一真相源）。
- **流程日志**：写 `story/logs/第XXX章.md`（5 阶段合一，模板见 `templates/log-template.md`）。
- **联动总览**：更新 `叙事总览/`（功能五：新角色卡/伏笔卡/章节地图）。
- **增量索引**：ZVEC 可用时运行 `python runtime/index.py upsert --chapter N`（功能八）。

### Step 4：输出落库报告

按下方模板输出。

---

## 5. 落库报告输出模板

```
### 落库报告：第 X 章

## 状态更新
  ✓ characters.md：[变化简述，如：林深位置→上传舱，情绪→紧张]
  ✓ world.md：[变化简述，如：时间推进32分钟，新增"意识上传"规则]
  ✓ hooks.md：新增 X 个，回收 X 个，部分揭示 X 个
    - 新增：h_00X（内容简述）
    - 回收：h_00X
    - 部分揭示：h_00X（已揭示…剩…，下一回收点第N章）
  ✓ relationships.md：[变化简述，如：林深↔方若华 从6→7]
  ✓ objects.md：[变化简述，如：量子玻璃持有者→林深]
  ✓ timeline.md：[故事时间推进到…]
  ✓ story/meta/index.md：进度已更新

## 伏笔债务
  - h_002 已 active 12 章，建议下章推进
  - 无新增债务

## Change Report 摘要
  [一句话总结本章核心变化]

## 入池状态
  - 池子为静态（对标书拆解内容），不随写作增长
```
