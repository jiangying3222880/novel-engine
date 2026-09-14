## Summary

novel-engine v1.5.0 六步改进全执行完毕，基于基线测试数据驱动的 skill 改进。

### 变更内容

| Step | 内容 | 产出 |
|------|------|------|
| 1 | 基线测试集(E-002) | 3题材×5章语料，B-001五阶段全跑，4/4自检pass |
| 2 | verify.py evidence校验 | --scope evidence，4条FAIL规则 |
| 3 | T-001~T-005技法丹核化 | 5个技法加7字段头部 |
| 4 | PMC Suppression机制 | target-focus.md + g_xxx目标钩子 |
| 5 | Profiles层 | 04_profiles/ 14个文件(6平台+3题材+3篇幅) |
| 6 | 模型文档 | model-guide.md 各阶段模型配置 |
| 7 | T-006~T-009技法补全+Skill完整性检查 | 4文件7字段头部+self-review.md补Q5 |
| 8 | 炼丹补充(job-0007~0009) | T-010高潮突转+T-012代入感+anti-ai原则三扩展 |

### 核心发现

- **字数系统性问题确认**：skill字数配置与实际输出能力不匹配（E-001重测）
- **C-001~C-004全部落地**：3题材×5章均可见目标追踪/因果支撑/信息差/冲突
- **自检机制有效**：B-001 evidence_ids 100%真实

### 文件变更

- 新增：references/model-guide.md, references/target-focus.md, library/techniques/高潮突转技法库.md, library/techniques/代入感技法.md
- 修改：SKILL.md(v1.5.0), routes/index.md, verify.py, hooks-and-memory.md, session-start.md, self-review.md(Q5), references/anti-ai.md(原则三扩展), 9个技法文件, library/techniques/_README.md, runtime/_README.md

### 验证方式

```bash
# verify.py evidence校验(需要Python环境)
cd novel-engine
python runtime/verify.py --root "<项目>" --scope evidence

# 测试项目(含PASS/FAIL场景)
F:/炼丹计划/05_experiments/_verify_test/
```
