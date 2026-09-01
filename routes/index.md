# 路由台账（文件 → 阶段 · 唯一真相源）

> 本文件是 novel-engine 全部文件的**导航唯一真相源**。任何文件改名/增删/阶段调整，只改本文件，不再遍历各文件头。
> 各 references / templates 文件头仅保留一行 `> 阶段② · 路由见 routes/index.md`，详细上下游关系一律见本文件。
>
> 路由链：`SKILL.md`（路由中枢/三铁律）→ `routes/index.md`（本文件）→ references / templates。

---

## 一、五阶段 SOP 路由

| 阶段 | 入口判断 | 必读文件 |
|------|---------|---------|
| ⓪ 项目初始化 | "开新书/帮我建项目/导入" | `references/project-setup.md` |
| ① 本章规划 | "写下一章/规划第X章/继续写" | `references/session-start.md` |
| ② 正文写作 | 规划完成 | `references/writing-guide.md` |
| ③ 自检 | 初稿完成 | `references/self-review.md` |
| ④ 反AI润色 | 自检通过 | `references/anti-ai.md` |
| ⑤ 状态落库 | 润色完成 | `references/hooks-and-memory.md` |
| 全程参考 | 需交互细节 | `references/workflow-detail.md` |
| ⑤ 格式 | 落库生Report时 | `references/change-report-spec.md` |
| ③/④ 身份 | 自检/润色切换身份 | `references/identity-routing.md` |
| ④ 防御 | 全程防诱导 | `references/prompt-defense.md` |
| ①/⑤ 检索 | 写前查状态/落库建索引 | `references/retrieval.md` |

| ②③④ 去味 | 深度方法库(human-signal 沉淀) | references/human-signal-zh.md |
| ② 外包 | 写作外包网页chat(流程分支) | references/chat-outsource.md |
| 短篇 | 短故事一次成篇(单篇完结) | references/short-story.md |

---

## 二、references 上下游关系

### project-setup.md · 阶段⓪ 项目初始化
```
上游：SKILL.md（"开新书/导入"触发）
前置：无
相关：templates/truth/ · templates/voice-profile-template.md · templates/pools/拆书规范.md（拆什么/入池/格式三问）· templates/pools/_README.md · templates/pools/拆解方法论.md
下游：references/session-start.md（初始化完成 → 阶段①）
```

### session-start.md · 阶段① 本章规划
```
上游：references/project-setup.md
前置：故事/真相/ 6个状态文件（强制加载，含 objects/timeline）+ novel-config.json
相关：templates/voice-profile-template.md · templates/细纲模板.md（B/E 回填：主角主动表达+参考素材槽位）· 配置/身份/（项目级身份覆盖）· 素材池/author_dna/ · 素材池/planner/ · 素材池/reference/techniques/ · 素材池/reference/samples/
下游：references/writing-guide.md（规划完成 → 阶段②）
```

### writing-guide.md · 阶段② 正文写作
```
上游：references/session-start.md（规划清单）
前置：规划清单 + 章态 + 素材
相关：素材池/reference/samples/（同类场景样本）
下游：references/self-review.md（初稿 → 阶段③）
```

### self-review.md · 阶段③ 行为验证自检
```
上游：references/writing-guide.md（初稿完成）
前置：本章正文初稿 + 故事/真相/ 状态文件
相关：references/anti-ai.md（检出AI味时查修正方法）· references/writing-guide.md（声线/冰山异常时回查）
下游：自检通过 → references/anti-ai.md；自检不通过 → 回阶段②改写（≤3轮，保留Best Version）
```

### anti-ai.md · 阶段④ 反AI味润色
```
上游：references/self-review.md（自检通过）
前置：本章正文 + self-review 自检结果
相关：references/writing-guide.md（冰山/对话不对称理论基础）· 素材池/reference/samples/ · 素材池/author_dna/
下游：references/hooks-and-memory.md（润色完成 → 阶段⑤）
```

### hooks-and-memory.md · 阶段⑤ 状态落库
```
上游：references/anti-ai.md（润色完成）
前置：本章最终正文 + 自检结果
相关：references/change-report-spec.md · 故事/真相/ 6个状态文件（含 objects/timeline）
下游：本章完成，等待用户指令进入下一章
```

### workflow-detail.md · 全程参考（5阶段SOP交互详解）
```
前置：无（可选参考，非强制）
相关：references/01~05 各阶段详细 SOP
下游：无（纯参考文件）
```

### chat-outsource.md · 外包写作分支（Chat-Outsource）
```
上游：SKILL.md（"外包写作/用网页chat写"触发）+ references/session-start.md（阶段①规划）
前置：故事/真相/ 6个状态文件 + 规划清单 + 声线样本（素材池/author_dna + 设定/角色声线）
产出：一份自包含最终提示词（打包状态/目标/声线样本/去AI味要求）→ 用户贴入网页chat → 正文贴回
下游：references/self-review.md（阶段③）→ 04（④跑满）→ 05（⑤落库）
相关：references/anti-ai.md · references/human-signal-zh.md（回接后去AI味）
```

### change-report-spec.md · 阶段⑤ 格式规范
```
上游：references/hooks-and-memory.md（落库时调用）
前置：本章最终正文 + 自检/润色结果
相关：故事/真相/characters|world|hooks|relationships（变更目标）
下游：无（格式规范文件，被05调用）
```

### short-story.md · 短故事创作模式（单篇完结）
```
上游：SKILL.md（"写个短故事/短篇/抖音推文风"触发）
前置：无（输入脑洞即可，不建项目/不拆书/不走 truth）
相关：references/anti-ai.md（强制过检）· references/prompt-defense.md（版权纪律）· templates/short-story-template.md
下游：交付单篇（短故事不进入五阶段状态机）
```

---

## 三、模板层路由

| 模板 | 用途 | 触发阶段 |
|------|------|---------|
| `templates/novel-config.json` | 项目配置预设 | ⓪ |
| `templates/chapter-template.md` | 章节 Frontmatter 模板 | ② |
| `templates/voice-profile-template.md` | 角色声线基线档案模板 | ① |
| `templates/truth/` | 6个状态文件模板（characters/world/hooks/relationships/objects/timeline） | ⓪ |
| `templates/meta/` | 章节元数据模板（chapter_XXXX.md + index.md 索引） | ⓪/② |
| `templates/narrative/` | Obsidian 叙事总览模板（00作品/01角色/02世界观/03伏笔/04地图/05关系网） | ⑤ |
| `templates/log-template.md` | 每章流程日志（5阶段合一） | ①~⑤ |
| `library/identities/` | 身份档案模板（作者/编剧/编辑/读者） | ⓪/全程 |
| `library/market-research.md` | 市场调查三档路由 | ⓪ |
| `library/packaging.md` | 卖点包装 + 反套路提案（doubao 融合） | ⓪/投稿/包装 |
| `templates/pools/` | 素材池模板（author_dna/planner/unit/knowledge/reference + 拆解方法论） | ⓪ |
| `templates/short-story-template.md` | 短故事极简骨架（故事核/导语/四幕/断章） | 短篇 |

## 四、素材库导航（用户级 + 项目级）

| 层 | 路径 | 说明 |
|----|------|------|
| 用户级 | `library/techniques/` | 通用写作方法论（按题材选 2-3 个） |
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
| 状态真相（强制加载） | `故事/真相/`（characters/world/hooks/relationships） |
| 章节元数据 + 章节索引 | `故事/元数据/`（已启用） |
| Obsidian 叙事总览（纯展示）| 项目根 `叙事总览.md` + `叙事总览/`（已启用） |
| 流程日志 | `故事/日志/`（已启用） |
| 素材池（按需加载） | `素材池/` |
| 完整设定档案 | `设定/` |
| 卷纲+细纲 | `大纲/` |
| 章节正文 | `正文/` |
