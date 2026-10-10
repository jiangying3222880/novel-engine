# 路由台账（文件 → 阶段 · 唯一真相源）

> 本文件是 novel-engine 全部文件的**导航唯一真相源**。任何文件改名/增删/阶段调整，只改本文件，不再遍历各文件头。
> 各 references / templates 文件头仅保留一行 `> 阶段② · 路由见 routes/index.md`，详细上下游关系一律见本文件。
>
> 路由链：`SKILL.md`（路由中枢/三铁律）→ `routes/index.md`（本文件）→ references / templates。

---

## 一、S1-S4 流水线路由（v1.9）

| 阶段 | 入口判断 | 必读文件 |
|------|---------|---------|
| ⓪ 项目初始化 | "开新书/帮我建项目/导入" | `references/project-setup.md` |
| S1 骨架（编剧） | "写下一章/规划第X章/继续写" | `references/session-start.md` + `templates/细纲模板.md` |
| 全程 地基 | 写前必读（内核三联+驱动标注） | `references/narrative-kernel.md` |
| S2 血肉（讲述者） | 细纲门通过 | `references/writing-guide.md` |
| S3 检验（编辑） | 初稿完成 | `references/self-review.md` + `templates/检验报告模板.md` |
| S3 依据 | AI味判定/表达问题打回 | `references/anti-ai.md` |
| S4 落库（档案员） | 检验通过 | `references/hooks-and-memory.md` |
| 全程参考 | 需交互细节 | `references/workflow-detail.md` |
| 全程 执行模式 | 三档 auto/single/multi + 物理/模拟隔离 + 防偷懒降级 | `references/execution-modes.md`（v1.9） |
| 全程 模块调度 | L3 模块触发卡（Agent）+ 挂载门禁 | `references/module-registry.md`（v1.8） |
| 初始化/用户询问 | 模块作用白话说明 + 依赖 + 档位 | `references/module-说明书.md`（v1.8，常驻不读） |
| S4 格式 | 落库生Report时 | `references/change-report-spec.md` |
| S3 身份 | 检验切换身份 | `references/identity-routing.md` |
| S1/S4 检索 | 写前查状态/落库建索引 | `references/retrieval.md` |
| S1/S4 目标焦点 | PMC suppression机制（g_xxx目标钩子） | `references/target-focus.md` |
| 全程 模型 | 各阶段模型选择/提示策略/限制补偿 | `references/model-guide.md` |

| S3 去味 | 深度方法库(human-signal 沉淀) | references/human-signal-zh.md |
| S1 外包 | 写作外包网页chat(流程分支) | references/chat-outsource.md |
| 短篇 | 短故事分段生成（单篇完结） | references/short-story.md（憋压三段式 + 短篇细纲门 + 每节字数门禁） |
| 短篇 引擎 | 文梗引擎库(情绪债务×兑现) | references/short-story-engines.md |
| 版本历史 | job级明细/版本摘要 | references/变更历史.md |

---

## 二、references 上下游关系

### project-setup.md · 阶段⓪ 项目初始化
```
上游：SKILL.md（"开新书/导入"触发）
前置：无
相关：templates/truth/ · templates/voice-profile-template.md · templates/pools/拆书规范.md（拆什么/入池/格式三问）· templates/pools/_README.md · templates/pools/拆解方法论.md
下游：references/session-start.md（初始化完成 → 阶段①）
```

### session-start.md · S1 骨架（编剧 · 本章细纲）
```
上游：references/project-setup.md
前置：故事/真相/ 6个状态文件（强制加载，含 objects/timeline）+ novel-config.json + 滚动窗口（N-5~N 历史细纲，仅冲突链+信息释放两节）
相关：templates/voice-profile-template.md · templates/细纲模板.md（四维骨架：冲突链/情绪弧/信息释放/声线透传/角色状态最小摘要/任务字数）· 配置/身份/（项目级身份覆盖）· 素材池/author_dna/ · 素材池/planner/ · 素材池/reference/techniques/ · 素材池/reference/samples/ · references/narrative-kernel.md（内核三联 + 信息差方向，写前必填）· references/short-story.md §1.5（驱动标注格式，长短篇同名4字段）
下游：references/writing-guide.md（细纲门通过 → S2）
```

### writing-guide.md · S2 血肉（讲述者 · 正文写作）
```
上游：references/session-start.md（细纲_第XXXX章.md 四维骨架）
前置：细纲文件（multi=唯一输入包）+ config 字数；single=三条硬指令模拟隔离
相关：素材池/reference/samples/（同类场景样本）· references/execution-modes.md §3（single 降级）
下游：references/self-review.md（初稿 → S3 检验）
```

### self-review.md · S3 检验（编辑 · 双视角评估）
```
上游：references/writing-guide.md（初稿完成）
前置：本章正文初稿 + 细纲_第XXXX章.md（核对基准）
相关：references/anti-ai.md（AI味判定/表达问题依据）· references/writing-guide.md（声线/冰山异常时回查）· templates/检验报告模板.md（S3 产出格式）
下游：检验通过 → references/hooks-and-memory.md（S4）；骨架问题 → 节级回 S1；表达问题 → 回 S2（≤2轮，保留 Best Version）
```

### anti-ai.md · AI 味判定依据（原阶段④并入 S3 打回分支）
```
上游：references/self-review.md（S3 判定表达问题时调用）
前置：本章正文 + S3 检验上下文
相关：references/writing-guide.md（冰山/对话不对称理论基础）· 素材池/reference/samples/ · 素材池/author_dna/ · references/human-signal-zh.md（深度方法库）
下游：表达问题 → 回 S2 重写（不再独立润色阶段）；通过 → S4
```

### hooks-and-memory.md · S4 落库（档案员 · 原子提交）
```
上游：references/self-review.md（检验通过）
前置：本章最终正文 + 检验报告 + Change Report（暂存→校验→提交→回滚 四步）
相关：references/change-report-spec.md · 故事/真相/ 6个状态文件（含 objects/timeline）· references/execution-modes.md §4.4（输入包存档/降级声明记录）
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
上游：SKILL.md（"外包写作/用网页chat写"触发）+ references/session-start.md（S1 细纲）
前置：故事/真相/ 6个状态文件 + 细纲 + 声线样本（素材池/author_dna + 设定/角色声线）
产出：一份自包含最终提示词（打包细纲/目标/声线样本/去AI味要求）→ 用户贴入网页chat → 正文贴回
下游：references/self-review.md（S3 检验）→ hooks-and-memory.md（S4 落库）
相关：references/anti-ai.md · references/human-signal-zh.md（回接后去AI味）
```

### change-report-spec.md · S4 格式规范
```
上游：references/hooks-and-memory.md（落库时调用）
前置：本章最终正文 + 检验报告
相关：故事/真相/characters|world|hooks|relationships（变更目标）
下游：无（格式规范文件，被 S4 落库 hooks-and-memory.md 调用）
```

### target-focus.md · 目标焦点管理（PMC Suppression · v1.5 新增）
```
上游：SKILL.md（v1.5 新增机制）
前置：PMC4266429 认知科学依据（goal remention 714ms vs new goal 908ms, p<.001）
相关：references/hooks-and-memory.md（目标焦点表 g_xxx + suppressed机制）· references/session-start.md §5（规划时检查）· references/self-review.md Q5（自检验证）
下游：阶段①规划（必须检查 focal goal 状态）/ 阶段⑤落库（更新 focal/suppressed/achieved 状态）
```

### model-guide.md · 模型文档（v1.5 新增）
```
上游：SKILL.md（v1.5 新增）
前置：skill v1.7.0 链路分析（2026-10-08 刷新；驱动标注为执行层工具、模型无关，不改变模型矩阵结论）
相关：references/chat-outsource.md（外包分支）· templates/outsource-prompt.md（外包提示词模板）
下游：全程（模型选择参考）/ templates/outsource-prompt.md（编译依据）
```


### short-story.md · 短故事创作模式（单篇完结）
```
上游：SKILL.md（"写个短故事/短篇/抖音推文风"触发）
前置：无（输入脑洞即可，不建项目/不拆书/不走 truth）；写前必填驱动标注（§1.5，4字段）；v1.9 起短篇也走细纲门（§1.3：憋压三段式细纲 + 细纲门硬软两层）
流程：S1 编剧产短篇细纲（templates/short-story-template.md）→ 细纲门 → S2 按节写（分段生成强制，§2 段一1节→段二节数按 §2.0 写前预检由 target 反推，默认 15000→6 节→段三1节；段二每节字数门禁 §2.1 ≥2000字/节，不足用 §2.2 加厚清单补足重写；段一/段三豁免门禁但须落区间）→ S3 检验（憋压/爆发/断章双视角，§4）→ 全篇验收 target±15%
相关：references/anti-ai.md（AI味判定）· references/prompt-defense.md（版权纪律）· templates/short-story-template.md（短篇细纲模板）· references/short-story-engines.md（引擎选择）· references/narrative-kernel.md（内核适配）
下游：交付单篇（短故事不进入长篇状态机）
```

### short-story-engines.md · 短篇文梗引擎库（v1.7 新增）
```
上游：SKILL.md（短篇分支）· references/short-story.md（节奏层）
前置：确定短篇题材/文梗后，按触发词选引擎（信息差/牺牲觉醒/死亡后悔/掠夺反杀/反常识钩子/公开处刑）
相关：references/short-story.md（憋压三段式）· library/techniques/单元讲法-*.md（兑现方式）· library/techniques/身份逆转反转法.md
下游：引擎卡 → 驱动标注（§1.5）→ 三段式生成
```

---

## 三、模板层路由

| 模板 | 用途 | 触发阶段 |
|------|------|---------|
| `templates/novel-config.json` | 项目配置预设 | ⓪ |
| `templates/chapter-template.md` | 章节 Frontmatter 模板 | S2 |
| `templates/voice-profile-template.md` | 角色声线基线档案模板 | S1 |
| `templates/truth/` | 6个状态文件模板（characters/world/hooks/relationships/objects/timeline） | ⓪ |
| `templates/meta/` | 章节元数据模板（chapter_XXXX.md + index.md 索引） | ⓪/S2 |
| `templates/narrative/` | Obsidian 叙事总览模板（00作品/01角色/02世界观/03伏笔/04地图/05关系网） | S4 |
| `templates/log-template.md` | 每章流程日志（S1-S4 合一） | S1~S4 |
| `templates/细纲模板.md` | 长篇四维骨架细纲（冲突链/情绪弧/信息释放/声线透传/角色状态最小摘要/任务字数） | S1 |
| `templates/检验报告模板.md` | S3 双视角检验报告（细纲门+正文门+读者/编辑视角+遮名测试） | S3 |
| `library/identities/` | 身份档案模板（作者/编剧/编辑/读者） | ⓪/全程 |
| `library/market-research.md` | 市场调查三档路由 | ⓪ |
| `library/packaging.md` | 卖点包装 + 反套路提案（doubao 融合） | ⓪/投稿/包装 |
| `templates/pools/` | 素材池模板（author_dna/planner/unit/knowledge/reference + 拆解方法论） | ⓪ |
| `templates/short-story-template.md` | 短篇细纲模板（憋压三段式四维骨架 + 细纲门 + 每节字数门禁） | 短篇 S1 |

## 四、素材库导航（用户级 + 项目级）

| 层 | 路径 | 说明 |
|----|------|------|
| 用户级 | `library/techniques/` | 通用写作方法论（按题材选 2-3 个）；场景→技法两级索引见 `references/技法速查索引.md` |
| 用户级 | `library/genres/` | 题材风格包（写玄幻选辰东式，写都市神话选斩神式） |
| 用户级 | `library/knowledge/` | 通用知识库（按本书题材预加载） |
| 用户级 | `library/platforms/` | 平台适配指南（确认目标平台风格） |
| 用户级 | `library/identities/` | 身份档案基线（作者/编剧/编辑/读者，项目级可覆盖） |
| 用户级 | `library/market-research.md` | 市场调查三档路由（快速/标准/深度） |
| 项目级 | `素材池/` | 对标书拆解出的素材池（author_dna/planner/unit/knowledge/reference） |

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
