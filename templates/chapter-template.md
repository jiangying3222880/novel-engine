<!--
> 📍 **位置**：章节输出 → 章节 Frontmatter 模板
> ⬆️ **上游**：阶段②写作完成后填充 Frontmatter
> ⚠️ **必读前置**：本章正文 + 规划清单
> 📚 **相关参考**：
> - `references/01-session-start.md` — 阶段①规划章态
> - `references/05-hooks-and-memory.md` — 阶段⑤落库时读取 Frontmatter
> ⬇️ **下游**：阶段③自检 / 阶段⑤落库（均读取 Frontmatter 获取章节元数据）
-->
---
chapter_id: 001
title: "章节标题"
word_count: 0
causal_links:
  from_chapter: 000
  trigger: "（第1章填：开篇事件；后续章填：上一章主角的抉择或遭遇）"
hooks_planted: ["HK001"]
hooks_resolved: []
emotion_arc: "起点情绪 → 终点情绪"
change_summary:
  characters: "（本章角色状态的核心变化，一句话）"
  world: "（本章世界状态的变化，无则填"无"）"
  relationships: "（本章关系变化，无则填"无"）"
review_status: "full_pass"  # full_pass / partial_pass / needs_human_review
---

# 第X章 章节标题

正文从这里开始。

第一段建议直接进入冲突或动作，不要先铺环境。

对话段：

"台词。"他说，加一个动作描写。

叙事段：保持视角人物的主观滤镜，不要用上帝视角解释。

（每500字左右有一个小转折或钩子）

（章末留悬念或情绪未完感，不要圆满收束）

---

> **Frontmatter 字段说明：**
> - `change_summary`：本章核心变化摘要，下一章读 Frontmatter 就能快速知道上一章变了什么，不用翻完整 Change Report
> - `review_status`：自检结果标记。full_pass = 4/4 全通过；partial_pass = 3/4 通过有瑕疵；needs_human_review = ≤2/4 通过需作者重点审稿
