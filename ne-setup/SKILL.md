---
name: ne-setup
description: 小说项目立项与初始化。当用户说"开新书""建项目""开始写新书""导入已有设定/大纲"时使用。建立 novel-config.json、故事/真相/ 六状态文件、身份档案与可选模块开关，完成后必须通过 init 门禁。
version: 2.1.6
agent_created: 2026-10-15
---

# ne-setup · 立项与项目初始化

## 一、两个入口

| 入口 | 场景 | 流程 |
|---|---|---|
| **A 从零创建** | 用户只有想法 | 对话建立 config/世界观/角色/大纲 → 从 `templates/truth/` 初始化状态文件 → 素材准备 |
| **B 导入已有** | 用户已有设定/大纲/正文 | 读取已有材料 → 映射标准结构 → **从当前章节往前推 3 章重建状态** → 素材准备 |

完整流程见 `./references/project-setup.md`。

## 二、必建产物（缺一项 = init 门禁 FAIL）

```
<项目根>/
├─ novel-config.json              从 templates/novel-config.json 复制后填
├─ 叙事总览.md                    根 MOC 入口，从 ../ne-memory/templates/narrative/叙事总览.md 复制
├─ 叙事总览/                       6 个骨架页，从 ../ne-memory/templates/narrative/ 复制后填
├─ 故事/真相/                      6 个状态文件，从 templates/truth/ 复制
├─ 故事/元数据/                     chapter_XXXX.md + index.md
├─ 故事/日志/                       每章流程日志（模板在 ../ne-memory/templates/log-template.md）
├─ 正文/                           第000X章 <标题>.md
└─ 配置/身份/                       项目级身份档案，从 ./templates/identity/_template.md 复制
```

> ⚠️ **两个高频坑**（都是"文档写了但模板没有"造成的）：
> 1. **根 `叙事总览.md` 没有独立模板**——只有 6 个子页模板。必须从 `../ne-memory/templates/narrative/叙事总览.md` 复制，只建空目录会 FAIL。
> 2. **`配置/身份/` 是必填不是可选**——门禁要求每个身份文件实质内容 ≥50 字，**作者档案必须填且含声音样本**（作者是唯一产出正文的角色）。

## 三、身份档案（项目级覆盖）

技能级基线在 `../ne-library/library/identities/`（作者/编剧/编辑/读者/档案员）。项目级 `配置/身份/` 存在则优先，**两级不合并存储**（避免漂移）。

> v2.1：原「讲述者」身份已删除，声线职责并入作者档案（§五 声音与声线 / §六 两个状态 / §七 自锚三问）。
> 作者在 S2 以**执笔态**出现（只读细纲+声音样本，不改情节），在立项和 S4 以**决策态**出现（全知、可拍板）。

**作者档案 §5.2 声音样本必须项目级覆盖**：技能级给不出你的声音，这是设计必然不是漏填。填法见该节（200-400 字成稿段 + 句法倾向）。

## 四、模块开关（Step 5.6，每本书重新确认，不跨项目继承）

模块配置只存 `novel-config.json → modules`（SSOT）。向用户逐项问过再写：

| 键 | 默认 | 说明 |
|---|---|---|
| `short_story` | true | 短故事模式（显式触发） |
| `chat_outsource` | true | 外包写作（显式触发） |
| `pool_teardown` | true | 对标书素材池 |
| `book_teardown` | true | 拆书模块 |
| `obsidian_overview` | false | Obsidian 叙事总览（需用户装 Obsidian） |
| `zvec` | false | ZVEC 检索（未装 SDK 自动降级 BM25） |

用户决策版说明见 `./references/module-说明书.md`，Agent 调度卡见 `./references/module-registry.md`。

## 五、素材准备（双层）

- **第一层 用户级**（跨项目共享，在 `../ne-library/library/`）：genres/ 选 1-2 题材包、techniques/ 选核心方法论、platforms/ 读匹配到的风格卡、knowledge/ 预加载
- **第二层 项目级**（每本书独立拆解）：两阶段（快速预览 → 用户确认 → 深度拆解）；档位 轻量 2-3KB / 标准 4-6KB / 全量 8-12KB。规范见 `../ne-library/templates/pools/拆书规范.md`

**题材与平台不手填、不追问**，由 Step 4.5 从世界观+大纲反推后一次确认。
规则见 `./references/题材与平台自动确认.md`；平台维取**风格口味**不取审核规约（8 张风格卡在 `../ne-library/library/platforms/`）。
题材与商业定位参考 `./references/商业立意与题材选择.md`。

## 六、门禁

```
python ../ne-tools/runtime/verify.py --root <项目根> --scope init
```

PASS 才允许进入写作。FAIL 必须修后重跑（退出码 1 = 禁止继续）。
