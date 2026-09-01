# runtime — 技能运行脚本

> 技能的可执行脚本（Python）。由 SKILL.md / 流程门禁调用，运行于技能根或项目根。

## 脚本用途

| 脚本 | 作用 | 何时调用 |
|------|------|---------|
| `verify.py` | **流程门禁**：检查项目目录/数据层防污染/总览骨架/双链/4位章号/config | 初始化后 `--scope init`、总览后 `--scope narrative`、每轮交付前 `all`；退出码 1=流程禁止继续 |
| `doc_sync.py` | **说明文档同步**：scan/check/update 各目录 `_README.md` 自动清单 | 修改技能文件后 `update`；发布前 `check` |
| `bm25_fts.py` | BM25+FTS 索引构建（零依赖 jieba，默认启用） | 项目初始化/每章落库后重建索引 |
| `index.py` | 章节元数据/正文/真相 → 索引文档（BM25 词项） | 被 bm25_fts 调用 |
| `query.py` | 检索查询：关键词 + 防剧透 cutoff + 知情权 visibility 过滤 | 阶段①⑤检索 |
| `check_text.py` | 文本合规检查（敏感词/边界） | 交付前 |
| `safe_edit.py` | **安全编辑**：先校验全部锚点存在再写盘，缺失即报错不写盘 | 正文扩写/改写的 Python 锚点替换统一走它；`--replace "old|||new"` 可多次，`--check-only` 只校验，`--first-only` 只替换首处 |
| `stability_test.py` | 稳定性测试（多轮采样验证） | 开发期验证 |

## 注意

- 所有脚本 UTF-8 无 BOM（Linux shebang 兼容）。
- 检索默认 BM25+FTS；ZVEC（语义检索）为可选增强，见 `references/retrieval.md`。
