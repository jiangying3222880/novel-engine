---
name: ne-tools
description: 小说创作引擎的运行时工具。当用户说"跑门禁""校验项目""刷新索引""打包技能""同步运行镜像""跑自测"时使用。提供 verify/doc_sync/index/query/package/deploy/skill_lint 等脚本。
version: 2.0.0
agent_created: 2026-10-15
---

# ne-tools · 运行时工具

> 依赖已 vendored 在 `runtime/deps/`（jieba / pyyaml / pypinyin），**clone 即可跑，不需要 pip 装任何东西**。

## 一、流程门禁（写作时用）

```
python <技能根>/ne-tools/runtime/verify.py --root <项目根> --scope <阶段>
```

| scope | 时机 | 覆盖 |
|---|---|---|
| `init` | 项目初始化完成 | 目录结构 / 真相防污染 / config 合法性 / **根 MOC 存在** |
| `outline` | 细纲产出后 | 细纲门硬性结构 |
| `execution` | S3 检验后 | 正文质量 / 工具与框架残留 |
| `settle` | **每章落库必跑** | 落库一致 / timeline / hooks / 证据链 |
| `trend` | 连续批跑·每 5 章 | 退化趋势 |
| （不写） | 交付前兜底 | 全部 |

**退出码 1 = 流程禁止继续。** PASS 才允许下一步，FAIL 必须修后重跑。

> verify.py 是**校验器**不是执行器：它证明结果对，不自动把结果做对。展示层产物仍由 Agent 生成。

**无 Python 环境时**：门禁跳过，但**必须在流程日志显式标注** `execution_mode=no_python，verify.py 跳过，手动校验：…`——不静默假装通过。

## 二、文档同步门禁（改技能时用）

```
python runtime/doc_sync.py update    # 刷新各目录自动索引
python runtime/doc_sync.py check     # 退出码 1 = 有缺失/过期，禁止提交
```

`pre-commit` hook 会自动跑 check，不同步直接拒绝提交。这就是治"升级完文档不同步"的机器闸。

## 三、标准化自检

```
python runtime/skill_lint.py                # 完整自检（含体量/description 质量）
python runtime/skill_lint.py --consistency  # 只跑一致性子集（pre-commit 用这个）
python runtime/skill_lint.py --all          # 遍历所有 ne-* 子技能
```

检查项：目录名==name / description 含"何时用"触发信号 / token 预算 <5000 / agent_created / 全仓引用断链 / 产物模板契约 / 产物命名契约。

> 官方 `quick_validate.py` 只查 5 项基础，给的 "Skill is valid!" 是**假绿灯**。

## 四、镜像同步

```
python runtime/deploy.py            # 演练，不动盘
python runtime/deploy.py --apply    # 真正同步（旧镜像先重命名备份）
```

## 五、其他脚本

| 脚本 | 用途 |
|---|---|
| `index.py` / `query.py` | BM25 检索索引与查询 |
| `selftest_gates.py` | 门禁回归自测（8 场景 21 断言），**改 verify.py 前后必跑** |
| `safe_edit.py` | 锚点安全替换（先校验全部锚点存在，缺失即报错不写盘） |
| `package.py` | 打发行包 |
| `check_text.py` | 文本检查 |
| `bm25_fts.py` | BM25 全文检索 |

## 六、约定

- **改 verify.py 先登记预期**（`selftest_gates.py` 里写预期），改完必跑、发版前必跑。
- **改文档后**先 `doc_sync.py update` 再 `git commit`（hook 自动校验）再 `deploy.py --apply`。
- 锚点改写一律走 `safe_edit.py`，禁止裸 Python 内联替换。
