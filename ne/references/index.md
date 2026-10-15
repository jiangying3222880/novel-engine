# 路由台账（文件 → 阶段 · 唯一真相源）

> 本文件是 novel-engine 全部文件的**导航唯一真相源**。任何文件改名/增删/阶段调整，只改本文件，不再遍历各文件头。
> 各 references / templates 文件头仅保留一行 `> S1/S4 · 路由见 ./index.md`（旧"阶段②"兼容标注可不改），详细上下游关系一律见本文件。
>
> 路由链：`../../ne/SKILL.md`（路由中枢/三铁律）→ `./index.md`（本文件）→ references / templates。

---

## 一、S1-S4 流水线路由（v1.9）

| 阶段 | 入口判断 | 必读文件 |
|------|---------|---------|
| 立项/初始化 | "开新书/帮我建项目/导入" | `../../ne-setup/references/project-setup.md` |
| S1 骨架（编剧） | "写下一章/规划第X章/继续写" | `../../ne-memory/references/session-start.md` + `../../ne-outline/templates/细纲模板.md` |
| 全程 地基 | 写前必读（内核三联+驱动标注） | `../../ne-outline/references/narrative-kernel.md` |
| S2 血肉（讲述者） | 细纲门通过 | 唯一输入包 = `../../ne-outline/templates/细纲模板.md` 产物（细纲_第XXXX章.md）+ config 字数；**禁读规则/状态/技法文件**（口径见 `../../ne-write/references/execution-modes.md` §2.2，v1.9.1.2） |
| S3 检验（编辑） | 初稿完成 | `../../ne-review/references/self-review.md` + `../../ne-review/templates/检验报告模板.md` |
| S3 依据 | AI味判定/表达问题打回 | `../../ne-review/references/anti-ai.md` |
| S4 落库（档案员） | 检验通过 | `../../ne-memory/references/hooks-and-memory.md` |
| 全程参考 | 需交互细节 | `../../ne-write/references/workflow-detail.md` |
| 全程 执行模式 | 三档 auto/single/multi + 物理/模拟隔离 + 防偷懒降级 | `../../ne-write/references/execution-modes.md`（v1.9） |
| 全程 模块调度 | L3 模块触发卡（Agent）+ 挂载门禁 | `../../ne-setup/references/module-registry.md`（v1.8） |
| 初始化/用户询问 | 模块作用白话说明 + 依赖 + 档位 | `../../ne-setup/references/module-说明书.md`（v1.8，常驻不读） |
| S4 格式 | 落库生Report时 | `../../ne-memory/references/change-report-spec.md` |
| S3 身份 | 检验切换身份 | `../../ne-write/references/identity-routing.md` |
| S1/S4 检索 | 写前查状态/落库建索引 | `../../ne-memory/references/retrieval.md` |
| S1/S4 目标焦点 | PMC suppression机制（g_xxx目标钩子） | `../../ne-outline/references/target-focus.md` |
| 全程 模型 | 各阶段模型选择/提示策略/限制补偿 | `../../ne-write/references/model-guide.md` |

| S3 去味 | 深度方法库(human-signal 沉淀) | ../../ne-review/references/human-signal-zh.md |
| S1 外包 | 写作外包网页chat(流程分支) | ../../ne-write/references/chat-outsource.md |
| 短篇 | 短故事分段生成（单篇完结） | ../../ne-short/references/short-story.md（憋压三段式 + 短篇细纲门 + 每节字数门禁） |
| 短篇 引擎 | 文梗引擎库(情绪债务×兑现) | ../../ne-short/references/short-story-engines.md |
| 版本历史 | job级明细/版本摘要 | ../../_skill_analysis/变更历史.md |

---

## 二、references 上下游关系

### project-setup.md · 立项初始化
```
上游：../../ne/SKILL.md（"开新书/导入"触发）
前置：无
相关：templates/truth/ · ../../ne-write/templates/voice-profile-template.md · ../../ne-library/templates/pools/拆书规范.md（拆什么/入池/格式三问）· ../../ne-library/templates/pools/_README.md · ../../ne-library/templates/pools/拆解方法论.md
下游：../../ne-memory/references/session-start.md（初始化完成 → S1）
```

### session-start.md · S1 骨架（编剧 · 本章细纲）
```
上游：../../ne-setup/references/project-setup.md
前置：故事/真相/ 6个状态文件（强制加载，含 objects/timeline）+ novel-config.json + 滚动窗口（N-5~N 历史细纲，仅冲突链+信息释放两节）
相关：../../ne-write/templates/voice-profile-template.md · ../../ne-outline/templates/细纲模板.md（四维骨架：冲突链/情绪弧/信息释放/声线透传/角色状态最小摘要/任务字数）· 配置/身份/（项目级身份覆盖）· 素材池/author_dna/ · 素材池/planner/ · 素材池/reference/techniques/ · 素材池/reference/samples/ · ../../ne-outline/references/narrative-kernel.md（内核三联 + 信息差方向，写前必填）· ../../ne-short/references/short-story.md §1.5（驱动标注格式，长短篇同名4字段）
下游：../../ne-write/references/writing-guide.md（细纲门通过 → S2）
```

### writing-guide.md · 写作技法与文风库（S1 编译素材 · S3 打回依据 · S2 写作期禁读 · v1.9.1.2 澄清）
```
上游：../../ne-memory/references/session-start.md（细纲_第XXXX章.md 四维骨架）
前置：S2 写作期**禁读本文件**（v1.9 物理隔离；S2 输入包仅细纲+config 字数）。本文件由 S1 取材（声线透传/声音包编译）与 S3 打回时引用
相关：素材池/reference/samples/（同类场景样本）· ../../ne-write/references/execution-modes.md §3（single 降级）
下游：../../ne-review/references/self-review.md（初稿 → S3 检验）
```

### self-review.md · S3 检验（编辑 · 双视角评估）
```
上游：../../ne-write/references/writing-guide.md（初稿完成）
前置：本章正文初稿 + 细纲_第XXXX章.md（核对基准）
相关：../../ne-review/references/anti-ai.md（AI味判定/表达问题依据）· ../../ne-write/references/writing-guide.md（声线/冰山异常时回查）· ../../ne-review/templates/检验报告模板.md（S3 产出格式）
下游：检验通过 → ../../ne-memory/references/hooks-and-memory.md（S4）；骨架问题 → 节级回 S1；表达问题 → 回 S2（≤2轮，保留 Best Version）
```

### anti-ai.md · AI 味判定依据（原阶段④并入 S3 打回分支）
```
上游：../../ne-review/references/self-review.md（S3 判定表达问题时调用）
前置：本章正文 + S3 检验上下文
相关：../../ne-write/references/writing-guide.md（冰山/对话不对称理论基础）· 素材池/reference/samples/ · 素材池/author_dna/ · ../../ne-review/references/human-signal-zh.md（深度方法库）
下游：表达问题 → 回 S2 重写（不再独立润色阶段）；通过 → S4
```

### hooks-and-memory.md · S4 落库（档案员 · 原子提交）
```
上游：../../ne-review/references/self-review.md（检验通过）
前置：本章最终正文 + 检验报告 + Change Report（暂存→校验→提交→回滚 四步）
相关：../../ne-memory/references/change-report-spec.md · 故事/真相/ 6个状态文件（含 objects/timeline）· ../../ne-write/references/execution-modes.md §4.4（输入包存档/降级声明记录）
下游：本章完成，等待用户指令进入下一章
```

### workflow-detail.md · 全程参考（S1-S4 流水线交互详解）
```
前置：无（可选参考，非强制）
相关：references/project-setup / session-start / writing-guide / self-review / anti-ai / hooks-and-memory（各阶段详细 SOP）
下游：无（纯参考文件）
```

### chat-outsource.md · 外包写作分支（Chat-Outsource）
```
上游：../../ne/SKILL.md（"外包写作/用网页chat写"触发）+ ../../ne-memory/references/session-start.md（S1 细纲）
前置：故事/真相/ 6个状态文件 + 细纲 + 声线样本（素材池/author_dna + 设定/角色声线）
产出：一份自包含最终提示词（打包细纲/目标/声线样本/去AI味要求）→ 用户贴入网页chat → 正文贴回
下游：../../ne-review/references/self-review.md（S3 检验）→ hooks-and-memory.md（S4 落库）
相关：../../ne-review/references/anti-ai.md · ../../ne-review/references/human-signal-zh.md（回接后去AI味）
```

### change-report-spec.md · S4 格式规范
```
上游：../../ne-memory/references/hooks-and-memory.md（落库时调用）
前置：本章最终正文 + 检验报告
相关：故事/真相/characters|world|hooks|relationships（变更目标）
下游：无（格式规范文件，被 S4 落库 hooks-and-memory.md 调用）
```

### target-focus.md · 目标焦点管理（PMC Suppression · v1.5 新增）
```
上游：../../ne/SKILL.md（v1.5 新增机制）
前置：PMC4266429 认知科学依据（goal remention 714ms vs new goal 908ms, p<.001）
相关：../../ne-memory/references/hooks-and-memory.md（目标焦点表 g_xxx + suppressed机制）· ../../ne-memory/references/session-start.md §5（规划时检查）· ../../ne-review/references/self-review.md Q5（自检验证）
下游：S1 规划（必须检查 focal goal 状态）/ S4 落库（更新 focal/suppressed/achieved 状态）
```

### model-guide.md · 模型文档（v1.5 新增）
```
上游：../../ne/SKILL.md（v1.5 新增）
前置：skill v1.7.0 链路分析（2026-10-08 刷新；驱动标注为执行层工具、模型无关，不改变模型矩阵结论）
相关：../../ne-write/references/chat-outsource.md（外包分支）· ../../ne-write/templates/outsource-prompt.md（外包提示词模板）
下游：全程（模型选择参考）/ ../../ne-write/templates/outsource-prompt.md（编译依据）
```


### short-story.md · 短故事创作模式（单篇完结）
```
上游：../../ne/SKILL.md（"写个短故事/短篇/抖音推文风"触发）
前置：无（输入脑洞即可，不建项目/不拆书/不走 truth）；写前必填驱动标注（§1.5，4字段）；v1.9 起短篇也走细纲门（§1.3：憋压三段式细纲 + 细纲门硬软两层）
流程：S1 编剧产短篇细纲（../../ne-short/templates/short-story-template.md）→ 细纲门 → S2 按节写（分段生成强制，§2 段一1节→段二节数按 §2.0 写前预检由 target 反推，默认 15000→6 节→段三1节；段二每节字数门禁 §2.1 ≥2000字/节，不足用 §2.2 加厚清单补足重写；段一/段三豁免门禁但须落区间）→ S3 检验（憋压/爆发/断章双视角，§4）→ 全篇验收 target±15%
相关：../../ne-review/references/anti-ai.md（AI味判定）· ../../ne-library/references/prompt-defense.md（版权纪律）· ../../ne-short/templates/short-story-template.md（短篇细纲模板）· ../../ne-short/references/short-story-engines.md（引擎选择）· ../../ne-outline/references/narrative-kernel.md（内核适配）
下游：交付单篇（短故事不进入长篇状态机）
```

### short-story-engines.md · 短篇文梗引擎库（v1.7 新增）
```
上游：../../ne/SKILL.md（短篇分支）· ../../ne-short/references/short-story.md（节奏层）
前置：确定短篇题材/文梗后，按触发词选引擎（信息差/牺牲觉醒/死亡后悔/掠夺反杀/反常识钩子/公开处刑）
相关：../../ne-short/references/short-story.md（憋压三段式）· library/techniques/单元讲法-*.md（兑现方式）· ../../ne-library/library/techniques/身份逆转反转法.md
下游：引擎卡 → 驱动标注（§1.5）→ 三段式生成
```

---

## 三、模板层路由

| 模板 | 用途 | 触发阶段 |
|------|------|---------|
| `../../ne-setup/../../ne-setup/templates/novel-config.json` | 项目配置预设 | 立项 |
| `../../ne-write/templates/chapter-template.md` | 章节 Frontmatter 模板 | S2 |
| `../../ne-write/templates/voice-profile-template.md` | 角色声线基线档案模板 | S1 |
| `templates/truth/` | 6个状态文件模板（characters/world/hooks/relationships/objects/timeline） | 立项 |
| `templates/meta/` | 章节元数据模板（chapter_XXXX.md + index.md 索引） | 立项/S4 |
| `templates/narrative/` | Obsidian 叙事总览模板（00作品/01角色/02世界观/03伏笔/04地图/05关系网） | S4 |
| `../../ne-memory/templates/log-template.md` | 每章流程日志（S1-S4 合一） | S1~S4 |
| `../../ne-outline/templates/细纲模板.md` | 长篇四维骨架细纲（冲突链/情绪弧/信息释放/声线透传/角色状态最小摘要/任务字数） | S1 |
| `../../ne-review/templates/检验报告模板.md` | S3 双视角检验报告（细纲门+正文门+读者/编辑视角+遮名测试） | S3 |
| `library/identities/` | 身份档案模板（作者/编剧/编辑/读者） | 立项/全程 |
| `../../ne-library/library/market-research.md` | 市场调查三档路由 | 立项 |
| `../../ne-library/library/packaging.md` | 卖点包装 + 反套路提案（doubao 融合） | 立项/投稿/包装 |
| `templates/pools/` | 素材池模板（author_dna/planner/unit/knowledge/reference + 拆解方法论） | 立项 |
| `../../ne-short/templates/short-story-template.md` | 短篇细纲模板（憋压三段式四维骨架 + 细纲门 + 每节字数门禁） | 短篇 S1 |

## 四、素材库导航（用户级 + 项目级 · 全目录级）

> 各目录 `_README.md` 只承载 doc_sync 自动清单 + 内容本体（若有），**语义导航一律以本表为准**。

### 用户级 `library/`

| 路径 | 说明 |
|------|------|
| `library/techniques/` | 通用写作方法论：T-卡 103 张（T-001~T-118，编号有空缺）+ 方法论 21 篇 = 124 文件；**场景→技法两级索引见 `../../ne-library/references/技法速查索引.md`** |
| `library/genres/` | 题材风格包：`xuanhuan-chendong`（辰东式玄幻）/ `urban-myth-zanshen`（斩神式都市神话）/ `都市` / `仙侠修真` / `悬疑`，各含 1-4 个 md |
| `library/knowledge/` | 通用知识库：`corpus`（语料索引 4 份）/ `analysis`（技法对比 2 份） |
| `library/platforms/` | 平台适配指南（**内容本体在 `_README.md`**：8 平台速览 + 写作要点 + 红线） |
| `library/identities/` | 身份档案基线（作者/编剧/编辑/读者，项目级可覆盖） |
| `../../ne-library/library/market-research.md` | 市场调查三档路由（快速/标准/深度） |

### 项目级模板 `templates/`

| 路径 | 说明 |
|------|------|
| `templates/` | 模板总览（config/chapter/voice-profile/log/细纲/检验报告/短篇/外包） |
| `templates/truth/` | 6 状态文件模板（characters/world/hooks/relationships/objects/timeline） |
| `templates/meta/` | 章节元数据模板（chapter_XXXX.md + index.md） |
| `templates/narrative/` | Obsidian 叙事总览模板（00作品/01角色/02世界观/03伏笔/04地图/05关系网） |
| `templates/identity/` | 项目级身份覆盖模板 |
| `templates/pools/` | 素材池模板（拆书规范 + 拆解方法论；author_dna/planner/unit/_template.md） |
| `templates/pools/knowledge/` | 知识池说明（**内容本体在 `_README.md`**） |
| `templates/pools/reference/` | 文学素材池说明（**内容本体在 `_README.md`**） |
| `templates/pools/reference/techniques/` | 项目池技巧分类 8 大类（**内容本体在 `_README.md`**） |
| `templates/pools/reference/samples/` | 实战样本库 7 类（coolness/suspense/action/humor/horror/worldbuilding/xianxia，各 1 份样本；**内容本体在 `_README.md`**） |

### 其他目录

| 路径 | 说明 |
|------|------|
| `references/` | 方法库（阶段参考，上下游见本文件 §二） |
| `runtime/` | Python 运行时（脚本用途表见 `../../ne-tools/runtime/_README.md`） |
| `routes/` | 本文件（路由台账唯一真相源） |
| `story/` | 项目结构示意（仅示意） |

---

## 五、项目级文件（每本书独立，不在技能目录）

| 用途 | 路径 |
|------|------|
| 状态真相（强制加载） | `故事/真相/`（6 个文件：characters/world/hooks/relationships/objects/timeline） |
| 章节元数据 + 章节索引 | `故事/元数据/`（已启用） |
| Obsidian 叙事总览（纯展示）| 项目根 `叙事总览.md` + `叙事总览/`（已启用） |
| 流程日志 | `故事/日志/`（已启用） |
| 素材池（按需加载） | `素材池/` |
| 完整设定档案 | `设定/` |
| 卷纲+细纲 | `大纲/` |
| 章节正文 | `正文/` |
