# runtime — 技能运行脚本

> 技能的可执行脚本（Python）。由 SKILL.md / 流程门禁调用，运行于技能根或项目根。

## 脚本用途

| 脚本 | 作用 | 何时调用 |
|------|------|---------|
| `verify.py` | **流程门禁**（v1.9.1.2）：39 项检查、PASS/WARN/FAIL 三态（退出码 1 = 流程禁止继续）。scope：`init`（目录/防污染/config）/ `narrative`（总览双链）/ `outline`（细纲门硬结构）/ `evidence`（证据链 #8）/ `execution`（execution_mode 声明）/ **`settle`（每章落库必跑：落库一致/timeline/hooks/证据链 #8/正文质量 #15-#33/产物 #20-#21/#27/状态 #23/#28/断链 #32）**/ `trend`（#31 退化趋势）/ `batch`（连写停机闸，含 #8）/ `all`（全部） | 初始化后 `init`、总览后 `narrative`、细纲后 `outline`、**每章 S4 必跑 `settle`**、连写跑 `batch`/`trend`、交付前 `all` |
| `doc_sync.py` | **说明文档同步**：scan/check/update 各目录 `_README.md` 自动清单 + **跨文件版本一致性**（首行标题 + 全文最高版本号扫描，v1.9.1.2 补盲） | 修改技能文件后 `update`；发布前 `check` |
| `package.py` | **发行打包**（v1.9.1.2 新增）：生成 ZIP，自动排除开发期文件（`_skill_analysis/`、`测试_基线*/`、`pr-body.md`、`.git`、`__pycache__` 等），版本号取 SKILL.md frontmatter | 发布/分发技能包时 |
| `selftest_gates.py` | **门禁回归自测**（v1.9.1.3 新增 · D-31）：8 场景 21 断言，把 verify 关键行为（#8 接线/证据双格式/#27 槽位/#16/#21/#23/#32/batch 停机闸）固化为可重放回归；`-v` 看明细、`--keep` 留夹具 | **改 verify.py 前先在此登记预期（预期先行），改完必跑；发版前必跑** |
| `bm25_fts.py` | BM25+FTS 索引构建（零依赖 jieba，默认启用） | 项目初始化/每章落库后重建索引 |
| `index.py` | 章节元数据/正文/实体类真相（characters/world/hooks/objects）→ 索引文档（BM25 词项） | 被 bm25_fts 调用 |
| `query.py` | 检索查询：关键词 + 防剧透 cutoff + 知情权 visibility 过滤 | S1/S4 检索 |
| `check_text.py` | 文本合规检查（敏感词/边界） | 交付前 |
| `safe_edit.py` | **安全编辑**：先校验全部锚点存在再写盘，缺失即报错不写盘 | 正文扩写/改写的 Python 锚点替换统一走它；`--replace "old|||new"` 可多次，`--check-only` 只校验，`--first-only` 只替换首处 |
| `stability_test.py` | 稳定性测试（多轮采样验证） | 开发期验证 |
| `index_ascii_key_test.py` | 拼音键碰撞消歧测试（P1-5：验证不同中文名 id 唯一、同中文名幂等、id 纯 ASCII） | 开发期验证 |

## 注意

- 所有脚本 UTF-8 无 BOM（Linux shebang 兼容）。
- 检索默认 BM25+FTS；**ZVEC（BM25 + 实验性词袋向量混合）为可选增强**，未装 zvec 时 `index.py`/`query.py` 自动回退 BM25+FTS，详见 `references/retrieval.md`。
- **依赖已离线 vendored**：纯 py 依赖（jieba/pyyaml/pypinyin）打包在 `runtime/deps/`，脚本已把 `deps` 注入 sys.path，clone 即用、无需 `pip install`；仅启用 ZVEC 混合检索时才需安装 `zvec`。