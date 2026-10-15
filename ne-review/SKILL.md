---
name: ne-review
description: 小说章节检验与去 AI 味（S3）。当用户说"检验这章""自检""去AI味""写得像不像人""遮名测试""这段有没有问题"时使用。产出检验报告（必须带 evidence_ids，无证据的判定无效）。
version: 2.1.1
agent_created: 2026-10-15
---

# ne-review · 检验与去 AI 味（S3）

## 一、核心原则

**无证据的判定无效。** 每一条问题都必须带 `evidence_ids`（指向具体文件或行段）。
verify.py 会校验这一点，缺 evidence 的检验报告等于没做。

## 二、产物命名（硬契约）

```
故事/reports/检验报告_第0001章.md
```

⚠️ **不是** `自检_第X章.md`——章号必须 4 位，名字必须是"检验报告"。
写错的话文件存在但门禁扫不到，会误判"缺检验报告"，且 evidence 校验被静默跳过。

模板：`./templates/检验报告模板.md`

## 三、四步检验

| 步 | 内容 | 依据 |
|---|---|---|
| **1 细纲门核对** | 结构硬检（四维度/冲突链/声线来源/任务字数） | `../ne-outline/templates/细纲模板.md` |
| **2 正文门核对** | 骨架逐节点对齐 + 证据 | `./references/self-review.md` |
| **3 双视角评估** | **读者先读**（体验通道：弃书点/卡顿/出戏）→ **编辑再审**（留存通道：前100字/主角五项/连载风险） | `./references/self-review.md` §Q1-Q5 |
| **4 遮名测试** | 遮住角色名，看能不能靠说话方式认出是谁——**声线有没有真的进嘴** | `./references/self-review.md` §Q2a |

> 顺序不能反：读者在前，编辑在后。体验在前，留存在后。

## 四、去 AI 味的判定依据

`anti-ai.md` **是 S3 的判定依据，不是一个独立环节**（v1.9 起润色已并入 S3，不存在"④润色"阶段）。

| 文件 | 用途 |
|---|---|
| `./references/anti-ai.md` | 主判定依据（旁白性质根因、理念分层） |
| `./references/anti-ai-词级信号.md` | 词级信号清单 |
| `./references/anti-ai-swaps.md` | 替换对照 |
| `./references/anti-ai-示范库.md` | 正反示范 |
| `./references/human-signal-zh.md` | 中文人味信号 |
| `./references/human-signal-模式库.md` | 人味模式库 |
| `./references/consistency-checklist.md` | 一致性清单 |

## 五、打回闭环（≤2 轮）

- **骨架问题**（缺节点/冲突链断了/伏笔没接）→ 回 S1 重排
- **表达问题**（AI 味/声线不对/节奏拖）→ 回 S2 重写
- **保留 Best Version**，不要为了过门禁越改越差

## 六、已知边界：门禁会误伤正常正文

框架自指检查（"这是细纲第 X 节""我用了 XX 技巧"）是全文正则，**第一人称叙述里的"我用了技巧"会被误判**。

遇到这种误报：判定为表达问题交给人确认，不要为了过门禁改掉正常叙述。
建议把此类检查的严格度降到 warn（见 `../ne-write/references/execution-modes.md`）。

## 七、门禁

```
python ../ne-tools/runtime/verify.py --root <项目根> --scope execution
```

检验通过后 → 转 `ne-memory` 做 S4 落库。
