> 阶段①/⑤ · ZVEC 检索层 · 路由见 `routes/index.md`

<!-- 提示：检索层是"写前查状态/防剧透"和"落库后建索引"的运行时。ZVEC 不可用时回退 markdown 检索门，防剧透不丢失。 -->

# 检索层（功能八 · BM25+FTS 默认 + ZVEC 可选）

## 0. 检索层分级（初始化默认启用 L1）

| 层 | 方案 | 依赖 | 默认 | 特点 |
|----|------|------|------|------|
| L0 | 纯 Markdown 门 | 零 | 兜底 | 扫文件做关键词匹配；质量最低，仅降级用 |
| **L1** | **BM25 + FTS** | **jieba（已有）** | **✅ 默认启用** | 分词→BM25 打分全文检索，专名精确命中；`runtime/bm25_fts.py` |
| L2 | ZVEC 混合检索 | zvec SDK（可选装） | 关闭 | BM25 + dense 实验性词袋向量 + RRF 融合；多一路近似召回（⚠️ dense 非语义 embedding） |

**BM25+FTS 与 ZVEC 的差别（初始化时告知用户）**：
- **BM25+FTS（L1，默认）**：词法匹配。查"沈青梧/剑胎/血月后第N天"这类**精确专名**命中率高；换同义词就查不到。零依赖（jieba 已有），索引小，初始化即可用。
- **ZVEC（L2，可选）**：词法 + dense 向量混合。多一路**近似召回**（dense 为 jieba 词袋向量，实验性，非语义 embedding，别期待"同义改写"级语义）；但需额外安装 zvec SDK（Windows 长路径可能阻 torch，见 embedding 注记），索引较大。
- **两者共有**：防剧透（source_chapter cutoff）+ 知情权（visibility）过滤，一致。**未装 zvec 时 index.py/query.py 自动回退 BM25+FTS。**
- **选择建议**：写长篇专名检索为主 → L1 已够；想要多一路近似召回 → 可开 L2（当前 dense 非语义 embedding）。

**L1 调用**：
```
python runtime/bm25_fts.py build  --root <项目根>                  # 初始化/落库后重建（默认 故事/索引/bm25/）
python runtime/bm25_fts.py query --root <项目根> --text "剑胎" --cutoff 5 [--visibility public] [--topk 10]
```

## 1. 定位

novel-engine 从"纯 Markdown"升级为 **Markdown 主状态 + ZVEC 检索运行时（唯一 Python 部件 = runtime/ 目录，含 9 个脚本、其余全纯 Markdown）**。检索层是**真混合检索**（向量 + BM25 + RRF 融合），不是 markdown 兜底。

- **运行时位置**：`runtime/`（唯一 Python 部件：目录含 9 个脚本，其余零 Python）
- **索引产物**：`故事/索引/`
- **数据源**：故事/真相（仅四类实体状态：characters/world/hooks/objects）+ 故事/元数据（元数据）+ 正文（分块）+ 设定（按需）
- **索引边界**：`relationships.md`、`timeline.md` 的关系/时间信息**不产独立实体索引**，靠全文检索（FTS/BM25）+ 阶段①原文加载（对齐 `references/hooks-and-memory.md` 映射表）

## 2. 调用点

| 阶段 | 调用 | 目的 |
|------|------|------|
| ① 规划前 | `query.py` 带 cutoff=本章-1 检索 | 查旧状态/伏笔/设定，防止写到未来 |
| ⑤ 落库后 | `index.py` 增量 upsert 本章 | 正文块 + 实体类 truth（characters/world/hooks/objects）变更入索引；relationships/timeline 靠全文检索；正文改写按章删除重建 |
| 全程 | 手动检索 | 跨章查角色/地点/物品/伏笔 |

## 3. 索引 Schema（复用功能七 5 通用字段）

每条索引 = 一个语义块：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | STRING | 唯一 ID：`doc_type.entity_key.chapter`（ASCII 点分隔，zvec 实测不允许 `/`） |
| `text` | 索引正文 | 语义块原文（truth 状态卡 / meta 元数据 / 正文分块 / 设定条目） |
| `dense` | VECTOR | 实验性词袋向量（jieba 分词→hash 桶；bge-small-zh 语义 embedding 为预留项、未接入） |
| `sparse` | SPARSE | BM25 中文稀疏向量（jieba 预处理） |
| `doc_type` | STRING | truth / meta / 正文 / 设定 |
| `chapter` | INT | 所在章号 |
| `source_chapter` | INT | 产生于哪章（防剧透基准，=chapter） |
| `visibility` | STRING | 知情权：public / 角色名 / 阵营 |
| `status` | STRING | 状态机值快照（alive/true_dead/destroyed…） |
| `valid_until` | INT/null | 状态失效章 |
| `path` | STRING | 源文件路径（回链） |

**entity_id 唯一性规范（功能八 F · 已定稿 ✅ · 含 Z1 实测修正）**：
- **索引 id 必须 ASCII 且不含 `/`**（zvec 0.7.0 实测：中文 id 报 `contains invalid characters`，斜杠 id 同样报错；`.`/`_`/`-` 允许）。故 entity_id 用**拼音键**（pypinyin 自动生成，如 `沈青梧`→`shenqingwu`），中文全名存 `entity_cn` 字段，检索/展示时用 `entity_cn`。
- id 格式：`doc_type.entity_key.chapter`（点分隔，示例 `truth.shenqingwu.5`）。非字母数字字符（括号等）清洗为 `_`。
- 唯一性保证：**拼音键 = 全局唯一**（同角色同键，幂等）；**不同中文名拼音相同时自动消歧**（P1-5：如"陈晨"/"晨尘"→ 同为 `chenchen`，后出现者追加码点后缀 `chenchen_6668_5c18`，id 不再互相覆盖并打印碰撞告警），中文名存 `entity_cn` 字段。
- 拼音缩写（mc/yn/zyz…）仅 truth 表内允许作为行内短键，且表头声明映射，禁止写入 hooks / meta / 正文 / 日志 / 索引。
- 检索归一：查询"沈青梧"→ 映射 `shenqingwu`（entity_id）→ 命中；"mc"→ 查 truth 表头映射 → 同一 entity_id。
- 验收：查询"沈青梧"与"mc"二次检索召回一致（通过映射表）。

## 4. 防剧透检索门（核心 · 双查询）

```python
# zvec 0.7.0 实测 API（规划 MultiQuery/VectorQuery/FTSQuery/fusion=RRF 写法在 0.7.0 不存在，以此为准）
# 查询对象 = zvec.Query(field_name, vector=..., fts=...)；topk 在 collection.query(q, topk=N) 传
# dense 查询
q_dense = zvec.Query(field_name="dense", vector=q_emb)         # q_emb 为 512 维归一化向量
# BM25 全文查询
q_fts   = zvec.Query(field_name="text", fts=zvec.Fts(match_string=q_text))

# 主查询：已解锁范围（dense + FTS 分别查，代码层合并去重；0.7.0 无 MultiQuery/RRF，weight 用代码层 RRF 近似）
unlocked = []
for q_ in (q_dense, q_fts):
    for r in collection.query(q_, topk=20):
        f = r.fields
        if f["source_chapter"] <= cutoff and f["visibility"] in visible_set:
            unlocked.append(r)   # 返回全文

# 副查询：未解锁范围（只返回"存在但未解锁"占位，不泄露词句）
locked_hit = False
for q_ in (q_dense, q_fts):
    for r in collection.query(q_, topk=20):
        if r.fields["source_chapter"] > cutoff:
            locked_hit = True   # 只输出 [未解锁：第N章 / 实体名]
```

- 真死角色：`status=true_dead` 且 `source_chapter ≤ cutoff` 可查往事；`> cutoff` 只返回"status=true_dead，下线于第N章"
- 未来章命中只给 `[未解锁：第N章]` 占位，**不返回任何原文词句**

## 5. 降级链路

**ZVEC 不可用（未装 SDK / 建库失败）→ 回退纯 markdown 检索门**：
- 用 grep/顺序扫描 故事/真相 + 故事/元数据，按 `source_chapter ≤ cutoff` + `visibility` 过滤
- 防剧透逻辑不变（未解锁只给占位）
- **运行降级，不是功能降级**：检索质量降低，但防剧透与知情权不丢失

## 6. 实施阶段（Z1-Z5）

```
Z1  ✅ 实测通过：zvec 0.7.0 在 Windows 可用。关键发现：①doc id 必须 ASCII 且不含 /（中文/斜杠报 invalid characters）；②CollectionSchema+FieldSchema+VectorSchema 建库；③create_and_open/open 工厂；④zvec.Query(field_name, vector/fts) 查询，topk 在 col.query(q, topk=N) 传；⑤默认 FLAT 索引，勿传 HnswQueryParam（类型不匹配报错）；⑥stats 是属性非方法。
Z2  ✅ runtime/index.py：schema（5通用字段）+ 拼音 entity_id + 四类实体（hooks/objects/characters/world）状态索引写入；relationships/timeline 不产独立实体（靠全文检索）；正文/meta 分块索引为扩展点
Z3  ✅ embedding：jieba TF-IDF dense 已落地（index.py/_embed，真实词法语义，零重依赖）；bge-small-zh-v1.5 为升级路径（torch 被 Windows 长路径阻断，见 config.yaml）
Z4  ✅ runtime/query.py：dense + BM25(match_string) 双查询，代码层合并；0.7.0 无 MultiQuery/RRF，权重近似
Z5  ✅ 防剧透双查询 + 知情权过滤，落 故事/索引/；ZVEC 缺失时 markdown 门降级
```

## 7. 验收 Checklist

- [x] Z1 在 Windows 实测通过（zvec 0.7.0；id 必须 ASCII 无 /）
- [x] 仅 runtime/ 目录为 Python 部件（含 9 个脚本），其余零 Python
- [x] schema 复用 5 通用字段，四类实体状态（hooks/objects/characters/world）索引（43 条实测；relationships/timeline 不产独立实体、靠全文检索）
- [x] 混合检索（dense + BM25 match_string）返回相关结果（"剑胎"命中剑胎相关条目）
- [ ] 本地 bge-small-zh-v1.5 embedding 生效（Z3 待接入，当前 hash 占位）
- [x] 双查询：cutoff 内返回全文、cutoff 外返回 `[未解锁：第N章]`
- [x] 真死角色依据 visibility 正确过滤
- [x] ZVEC 缺失时自动回退 markdown 门，防剧透仍生效
- [x] 索引产物可落 故事/索引/ 并支持清空重建
