# 6.7 GraphRAG 3.3.0

使用 Python 3.11 独立环境，依赖见 requirements/graph-lock.txt。5 篇中文教学短文在 data/articles/；短文足以练习流程，但不是验证 GraphRAG 优势的基准数据。

## 无密钥检查（已实跑）
```sh
python s67_graphrag.py
```
真正调用官方 CLI 的 init 和 index --dry-run --skip-validation。临时项目随后清理。skip-validation 跳过模型连接检查，dry-run 不建索引；成功仅代表配置通过，不代表 API 可用。脚本给子进程注入离线占位值，不读取或覆盖你的模型密钥。LiteLLM 使用随包价格表，避免启动时联网获取价格。

## 建立真实索引（需密钥，未在线实测）
```sh
python s67_graphrag.py --prepare .runtime/graphrag
```
已有目录时脚本拒绝覆盖。用编辑器打开新项目的 `.runtime/graphrag/.env`，把生成的 `GRAPHRAG_API_KEY` 填为自己的密钥；不要上传该文件。检查 settings.yaml 的 completion_models 与 embedding_models：默认模型分别为 gpt-5.4-mini-2026-03-17 和 text-embedding-3-small，账号必须有权限。再执行：
```sh
graphrag index --root .runtime/graphrag
graphrag query --root .runtime/graphrag --method global --query "这些材料共同关注哪些目标和风险？"
graphrag query --root .runtime/graphrag --method global --query "团队如何分工保障发布质量？"
graphrag query --root .runtime/graphrag --method local --query "李明负责什么，并与谁协作？"
graphrag query --root .runtime/graphrag --method local --query "导航学习站的进度能跨设备同步吗？"
```
命令需在 `.venv-graph` 环境内执行，或将 graphrag 换为该环境的完整路径。索引会对资料调用模型和 embedding，耗时与费用取决于模型、重试、分块和提取设置。先用这 5 篇小材料观察日志；本例没有预设美元费用，也没有宣称真实建索引已通过。

## 同数据、同问题比较普通 RAG

完成同一索引后，对上述四问分别改用 `--method basic`，这是官方提供的基础向量检索查询，可保持相同语料与 embedding，避免拿不同资料比较。
```sh
graphrag query --root .runtime/graphrag --method basic --query "团队如何分工保障发布质量？"
```
注意：basic 在已建好的 GraphRAG 项目上查询；本次总索引费用包含图提取，不能当作普通 RAG 独立索引成本。要比较完整系统成本，需另测只做分块与 embedding 的基线。

预期事实（不是承诺的模型原文）：

| 问题 | 应覆盖的证据 | 验收 |
| --- | --- | --- |
| 共同目标与风险 | 01 降低入门成本；02 可复现性；04 失败覆盖；05 费用与生产监测 | 全局问题应整合多篇，不只复述第一篇 |
| 分工保障质量 | 01、04、05：李明课程、王悦平台、陈晨评审、交叉核对 | 关系不混淆，可定位来源 |
| 李明的职责 | 02、04、05：课程、修复代码、与陈晨核对 | 局部实体相关事实完整 |
| 跨设备进度 | 03：仅当前浏览器、不自动同步 | 不因图检索补出不存在的云端功能 |

逐问记录方法、答案、引用、漏项、耗时、请求数和实际 token 用量；区分索引一次性成本与每次查询成本，费用按服务账单核对。GraphRAG 在这个小数据集上不一定更好，不预填任何质量或费用结论。

常见报错：

- `No module named graphrag` / CLI 找不到：使用 .venv-graph 及对应锁定依赖。
- 配置缺少 completion_models：不要沿用 2.x 的 models 配置；用本版本 init 生成。
- 找不到 input：运行 prepare 后确认有 5 个 .txt；单独 init 不会自动提供资料。
- 401/404/429：分别核对密钥、模型权限/名称、额度与速率；dry-run 不会发现这些问题。
- 缺少 entities / communities / community_reports 等表：先确认真实 index 成功，dry-run 不产生这些文件。
- 没有提取出实体：检查输入、extract_graph 的 entity_types 与语言提示，查看 logs，不能以空图结果下质量结论。

官方说明：https://microsoft.github.io/graphrag/get_started/ 及 https://microsoft.github.io/graphrag/cli/
