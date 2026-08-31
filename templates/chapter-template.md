<!--
> 📍 **位置**：章节输出 → 正文骨架模板（v1.4 功能三：无 YAML）
> ⬆️ **上游**：阶段②写作完成后输出正文文件
> ⚠️ **必读前置**：本章规划清单 + story/meta/ 上一章
> 📚 **相关参考**：
> - `templates/meta/chapter_XXX.md` — 本章元数据（原 Frontmatter 迁出地）
> - `templates/log-template.md` — 每章流程日志（5 阶段合一）
> - `references/session-start.md` — 阶段①规划章态
> ⬇️ **下游**：阶段③自检 / 阶段⑤落库（元数据从 story/meta/ 读取，正文文件保持干净）
-->
# 第X章 章节标题

正文从这里开始。

第一段建议直接进入冲突或动作，不要先铺环境。

对话段：

"台词。"他说，加一个动作描写。

叙事段：保持视角人物的主观滤镜，不要用上帝视角解释。

（每500字左右有一个小转折或钩子）

（章末留悬念或情绪未完感，不要圆满收束）

---

> **v1.4 说明（功能三 YAML 迁移）：**
> - 正文文件**不再包含 YAML Frontmatter**。章节元数据（causal_links / hooks / emotion_arc / change_summary）统一存放于 `story/meta/chapter_XXX.md`。
> - 每章流程日志（输入/输出/关键决策/身份）存放于 `story/logs/第XXX章.md`。
> - 阶段①读取：story/meta/上一章 + index；阶段⑤落库：更新 meta + index + 状态文件。
> - 检索字段（source_chapter / visibility 等）随功能七状态文件维护，不写进正文。
