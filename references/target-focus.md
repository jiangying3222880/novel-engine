> 阶段①/⑤ 目标焦点管理 · 路由见 `routes/index.md`

> 提示：不理解 suppression 机制会导致：多目标章节中读者焦点漂移、旧目标被遗忘、伏笔回收时读者无法关联。

# 目标焦点管理：PMC Suppression 机制与 Skill 实现

## 0. 认知科学来源

**PMC4266429**（Linderholm et al., 2004）：84人阅读实验，探针验证任务测量反应时。

### 核心数据

| 条件 | 反应时(ms) | 错误率(%) |
|------|-----------|-----------|
| 目标 remention（重复提及） | 713 | 1 |
| 目标首次引入 | 714 | 3 |
| **新目标引入后** | **908** | **10** |
| 中性信息后 | 834 | 8 |

**关键结论**：
- remention 维持目标激活 → 读者持续追踪
- 新目标引入后旧目标被**抑制**（p<.001，主动机制，非衰减）
- 抑制 = 压下去但不删除（伏笔回收有认知依据）
- 即使原目标成功/失败状态不明，新目标仍取代旧目标进入焦点

---

## 1. 目标焦点管理的必要性

**读者理解故事的认知依赖**：读者靠追踪主角目标来理解因果链（PMC C-001）。

**长篇的认知风险**：3个以上目标并存时，读者焦点会漂移。

**Skill 的现状缺口**：hooks.md 只管信息伏笔（读者不知道X），不管目标焦点（读者追踪Y）。

---

## 2. 两套钩子系统并列

| | 信息钩子 | 目标钩子 |
|--|---------|---------|
| ID前缀 | `h_xxx` | `g_xxx` |
| 本质 | 读者不知道某信息 | 读者追踪主角某个目标 |
| 状态 | active / resolved / abandoned | **focal（焦点）** / **suppressed（抑制）** / **achieved（已达成）** |
| PMC对应 | 悬念 | 读者焦点目标 |
| 回收机制 | 信息揭示 | 目标达成 / 主动放弃 / 明确失败 |

---

## 3. 目标焦点状态定义

### focal（焦点目标）
读者正在追踪的主角目标。当前章节写作时，主角的行动必须围绕 focal goal 展开。

**特征**：
- 出现在章节 change_summary 的"本章目标"
- 主角行动直接服务于 focal goal
- 读者知道主角在追求什么

### suppressed（抑制目标）
被新 focal goal 取代的旧目标。读者脑中仍有印象但已不活跃。

**特征**：
- hooks.md 中标记为 suppressed
- 读者下意识知道"主角还有这件事没搞定"，但当前章节不追踪
- **重新激活需要 remention**（PMC：被抑制目标 remention 后反应时恢复至714ms水平）

**重新激活条件**：
1. 正文明确 remention 旧目标（提及即可激活，不要求推进）
2. 旧目标重新进入 focal 状态

### achieved（已达成）
目标已完成（成功/失败/主动放弃），不再追踪。

**处理**：
- achieved 目标移出 hooks.md 焦点追踪表
- 可以作为角色背景保留在 characters.md

---

## 4. 操作规则

### 规则1：每章最多 1 个 focal goal
如果新目标引入导致旧 focal goal 被取代：
- 旧目标 → suppressed（不能直接 achieved，除非明确完成）
- 新目标 → focal
- **必须 remention 旧目标**（正文一句话提及即可），否则读者焦点断裂

### 规则2：remention 触发 suppressed → focal 转换
当 suppressed goal 被 remention：
- 自动恢复为 focal
- 写作时主角行动必须重新服务于该目标
- 可以在 suppressed 状态下同时推进（旧 focal 仍是 suppressed，新 focal 也存在）

### 规则3：多目标并存上限
建议 focal + suppressed 总数不超过 3 个。
超过 3 个时，建议主动标记 achieved 或通过 remention 合并。

### 规则4：伏笔回收时的目标激活
长篇伏笔回收（埋了10章以上的钩子）= suppressed goal reactivation。
PMC 数据提供了认知科学依据：这是读者自然机制，不是写作技巧。

---

## 5. hooks.md 中的目标焦点表（v1.5 新增）

在信息钩子表（`h_xxx`）之后，增加目标焦点追踪表（`g_xxx`）：

```markdown
## 目标焦点追踪（v1.5 新增 · PMC Suppression 机制）

| ID | 目标描述 | 角色 | 类型 | 埋设章 | 状态 | 备注 |
|----|---------|------|------|--------|------|------|
| g_001 | 洛林在18岁前找到结婚对象，避免被中央智脑随机分配 | 洛林 | focal | 1 | 5章remention→achieved | Ch1引入，Ch5达成 |
| g_002 | 楚元隐藏实力，在清竹峰苟到天下无敌 | 楚元 | focal | 1 | pending（超长线目标） | 历练触发前持续focal |
| g_003 | 项云峰出人头地，证明自己不是废物 | 项云峰 | suppressed | 1 | Ch3引入新目标后抑制 | 待remention |
```

---

## 6. session-start.md §5 中的 suppression 检查

阶段①规划时，额外执行以下判断：

```markdown
### 目标焦点检查（PMC Suppression · v1.5）

1. 上一章的 focal goal 是什么？ → [g_xxx]
2. 本章是否引入新目标？ → [是/否]
   - 是：旧 focal goal → suppressed（必须 remention）
   - 否：旧 focal goal 维持 focal
3. 有 suppressed goal 吗？ → [有/无]
   - 有：检查本章是否 remention（正文一句话提及即可）
   - remention 触发 suppressed → focal 转换
4. 本章 focal goal： → [g_xxx]
5. 预计推进状态：focal / suppressed / achieved
```

**典型场景与处理**：

| 场景 | 处理 |
|------|------|
| Ch5 focal goal 在 Ch6 完成 | Ch6 → achieved，无需 remention |
| Ch5 focal goal 被 Ch6 新目标取代 | Ch6 remention Ch5 goal → Ch6 gap抑制 |
| suppressed goal 在 Ch10 remention | Ch10 remention 句 → 激活 focal |
| 3个 suppressed goal 堆积 | 建议通过 achieved 清理，不建议继续堆积 |

---

## 7. self-review.md 中的目标焦点自检

阶段③自检时增加：

```
### Q5：目标焦点连贯性（PMC Suppression · v1.5）

检测行为：
1. 本章有 focal goal 吗？（必须有）
2. focal goal 是否有章节内的因果支撑？（行动→结果）
3. 如果引入了新目标，旧 focal goal 是否被 remention？
4. suppressed goal 是否在超 5 章后未 remention？

evidence_ids：
  - source: [目标相关正文片段]
```

**不通过信号**：
- 本章主角行动和 focal goal 无关（焦点漂移）
- 新目标引入但旧 focal goal 未被提及（读者焦点断裂）
- suppressed goal 超过 5 章未 remention（读者遗忘风险）

---

## 8. 适用场景判断

**目标焦点管理对以下场景尤为重要**：
- 长篇多目标并行（主线+支线+情感线）
- 角色有明确阶段性目标（修炼/复仇/恋爱）
- 伏笔回收（目标 reactivation）

**可以简化的场景**：
- 短篇（单情绪弧，1-2个目标，无多目标并存）
- 单线推进章节（没有新目标引入）
- 憋压中段（focal goal 持续蓄力，不引入新目标）
