---
name: ne-write
description: 小说正文写作主流程 S1-S4（骨架→血肉→检验→落库）。当用户说"写下一章""继续写""写正文""开始动笔""外包写作/给我提示词"时使用。含执行模式（multi 物理隔离 / single 模拟隔离）、身份切换与声音包接入点。
version: 2.1.5
agent_created: 2026-10-15
---

# ne-write · 正文主流程 S1-S4

## 一、写作三铁律

1. **S1 写前必读**：读 `故事/真相/` 6 个状态文件 + `novel-config.json` + 上一章细纲/检验报告 + 滚动窗口（N-5~N 章细纲，仅冲突链+信息释放两节）。**禁止全量加载设定集**——会上下文溢出、跳读、声线崩塌。
2. **章节优先**：元数据（causal_links / hooks / emotion_arc / change_summary）统一入 `故事/元数据/chapter_XXXX.md`，**正文文件保持干净无 YAML**。进度唯一真相源 = `故事/元数据/index.md`。
3. **S2 物理隔离**：执笔态**只读细纲产物文件**。检验报告必须带 `evidence_ids`，无证据的判定无效。

## 二、S1-S4 流水线契约

> 全文执行细则见 `./references/workflow-detail.md`（L2 主文件）。**改流程先改它，再回填本表。**

| 阶段 | 一句话 | 文件/模板 | 门禁点 |
|---|---|---|---|
| **S1 骨架**（编剧） | 读状态+滚动窗口 → 产 `细纲_第XXXX章.md`（四维骨架：冲突链/情绪弧/信息释放/声线透传/角色状态最小摘要/任务字数/伏笔计划） | `../ne-outline/templates/细纲模板.md` + `../ne-memory/references/session-start.md` | 细纲门：结构硬检（verify 可校验）+ 删节推理软检；节级打回 ≤2 轮 |
| **S2 血肉**（作者·执笔态） | 输入包 = **仅细纲文件** + config 字数 → 产干净正文初稿（无 YAML） | `./references/writing-guide.md` + `./references/execution-modes.md` §3 | 正文禁 YAML；multi 下禁读状态/规则/技法库 |
| **S3 检验**（编辑） | 细纲门核对 + 正文门核对 + 双视角（读者+编辑）+ 遮名测试 → 产 `检验报告_第XXXX章.md` | `../ne-review/templates/检验报告模板.md` + `../ne-review/references/self-review.md` | 无证据链判定无效；骨架问题→回 S1，表达问题→回 S2，≤2 轮保 Best |
| **S4 落库**（档案员） | Change Report → 暂存 → verify 校验 → 原子更新 6 状态 → 元数据/index → 日志 → 叙事总览 → 索引 → 角色 D 回填 | `../ne-memory/references/hooks-and-memory.md` + `../ne-memory/references/change-report-spec.md` | 未输出更新确认清单=未完成；Change Report 为空=注水打回；正文工具残留检查 |

### 产物命名（硬契约，写错门禁扫不到）

| 产物 | 正确命名 | 章节号位数 |
|---|---|---|
| 细纲 | `细纲_第0001章.md` | **4 位** |
| 检验报告 | `检验报告_第0001章.md` | **4 位**（不是"自检_第X章.md"） |
| 正文 | `第0001章 <标题>.md` | 4 位 |
| 元数据 | `chapter_0001.md` | 4 位 |

## 三、执行模式（隔离怎么落地）

| 模式 | 条件 | 隔离方式 |
|---|---|---|
| **multi** | 宿主有子 Agent 能力 | **物理隔离**：执笔态上下文里真的只有细纲文件 |
| **single** | 无子 Agent（豆包/网页版等） | **三条硬指令模拟隔离** + 日志声明 `execution_mode=single` |

完整规则见 `./references/execution-modes.md`。S4 日志必须记录本次用的模式和输入包存档。

## 四、身份（Voice）切换

环节（Lane）决定做什么，身份（Voice）决定以谁的嘴做。**S2 的主身份是作者，且必须是执笔态。**

- 身份档案：`../ne-library/library/identities/`（作者/编剧/编辑/读者/档案员）
- 路由规则：`./references/identity-routing.md`
- **定稿口径（v2.1）**：情节编剧定，文字由**作者·执笔态**出，拍板由**作者·决策态**做。
  原「讲述者」身份已删除，声线职责并入作者档案 §五-§七。
- **两个状态的判据 = 手里的文件**：只剩细纲输入包 = 执笔态；握着状态文件/技法库 = 决策态。两者不许同时握着。

> ⚠️ **AI 味的头号成因**：执笔态若只有细纲、没有声音定义，写出来必然是"通用通顺腔"。
> 解法是**把声音编译进输入包**（作者档案 §5.2 声音样本区，200-400 字成稿段 + 句法倾向），
> **不是**让执笔态多读文件——那会拆掉刚建好的隔离。

## 五、分支：外包写作（Chat-Outsource）

触发："外包写作""用网页 chat 写""给我提示词我拿去写"。

**流程**：S1 照跑 → 编译一份**自包含**最终提示词（打包细纲/目标/声线/去AI味要求，外部 chat 可独立写作）→ 用户贴入网页 chat → 正文贴回 → **S3 检验跑满 → S4 落库**。

**关键**：提示词必须自包含（外部读不到本地状态）；外部稿几乎必带 AI 味，**S3 必须跑满**；防剧透只给本章相关状态。详见 `./references/chat-outsource.md`。

## 六、门禁（每章必跑）

```
python ../ne-tools/runtime/verify.py --root <项目根> --scope settle
```

- `settle` 每章落库必跑；`trend` 连续批跑每 5 章；无 Python 环境时**跳过并在日志显式标注**，不静默假装通过。
- 无 Python 时的手动校验：按 `../ne-memory/references/hooks-and-memory.md` 的 S4 清单逐项核对。

## 七、体积红线

单状态文件 ≤ 8KB；单次对话强制加载总量 ≤ 12KB。../ne/SKILL.md 只存契约，详情下沉 references/。
