# 第 6 阶段：可复现实验

7 个入口均已在 Python 3.11.15 / macOS Apple Silicon 运行。模型响应默认固定，真正执行框架的 Agent、状态图、角色交接或文件工具。Dify 使用本地响应契约样本；GraphRAG 仅初始化与 dry-run。不要把离线结果解释为真实模型能力。

## 安装：只装当前课程需要的环境

以下命令先进入本目录：源码站为 `cd examples/stage6`；ZIP 解压后为 `cd stage6`。不要复用第 5 阶段虚拟环境，三个依赖集合包含不同版本的 OpenAI、Pydantic 和向量库。

macOS / Linux：
```sh
python3.11 -m venv .venv-frameworks
.venv-frameworks/bin/python -m pip install -r requirements/frameworks-lock.txt
# 6.3 才需要
python3.11 -m venv .venv-crew
.venv-crew/bin/python -m pip install -r requirements/crew-lock.txt
# 6.7 才需要
python3.11 -m venv .venv-graph
.venv-graph/bin/python -m pip install -r requirements/graph-lock.txt
```

Windows PowerShell：将创建环境命令中的 `python3.11` 改为 `py -3.11`，所有 `.venv-名称/bin/python` 改为 `.\.venv-名称\Scripts\python.exe`；无需激活环境或修改执行策略。例如：
```powershell
py -3.11 -m venv .venv-frameworks
.\.venv-frameworks\Scripts\python.exe -m pip install -r requirements/frameworks-lock.txt
.\.venv-frameworks\Scripts\python.exe s61_langchain.py
```
Windows/Linux 未在本次主机实测。锁文件记录当前安装的完整版本集合；如果目标系统没有某个轮子，先查看报错所指包的官方支持平台，不要混装另一课程的环境。安装需联网，CrewAI/GraphRAG 包含较大的向量与数值依赖。

| 课节 | 直接依赖基线 | 运行命令（macOS/Linux） |
| --- | --- | --- |
| 6.1 | langchain 1.4.7；langchain-openai 1.7.3（扩展适配器） | `.venv-frameworks/bin/python s61_langchain.py` |
| 6.2 | langgraph 1.2.18 | `.venv-frameworks/bin/python s62_langgraph.py` |
| 6.3 | crewai 1.15.30 | `.venv-crew/bin/python s63_crewai.py` |
| 6.4 | deepagents 0.7.32；显式 TodoListMiddleware | `.venv-frameworks/bin/python s64_deepagents.py` |
| 6.5 | Python 标准库；Dify API v1 | `python3.11 s65_dify.py` |
| 6.6 | Python 标准库；Docker n8n 2.44.7 | `python3.11 s66_n8n.py` |
| 6.7 | graphrag 3.3.0 | `.venv-graph/bin/python s67_graphrag.py` |

6.6 先启动 Docker 并执行 `docker pull docker.n8n.io/n8nio/n8n:2.44.7`。各入口实跑 stdout 保存在 expected/；耗时、第三方 warning 和启动日志不作为固定输出。没有隐藏的 API 密钥前置条件。

## 练习与验收

- 6.1 两个固定问题分别经过 weather、calculate，两次工具结果与 tool_call_id 连接正确。天气是教学数据；支持北京/上海，不是实时服务。更换问题需要修改固定模型脚本，或自行替换支持工具调用的模型。
- 6.2 第一次检索故意为空，第二次命中或拒答；checkpoint 停在 answer 前，再以同一个 thread_id 用 invoke(None) 恢复。InMemorySaver 不跨进程持久化。
- 6.3 研究→写作→编辑，实际传递 Task.context。`s63_crewai.py --timings` 可查看每个角色输出及本机任务耗时（包括框架开销、不是模型推理性能）；移除编辑时仍保留草稿中的无依据承诺。固定对照样本不证明多角色必然更优。CrewAI 会初始化用户配置/凭据目录以及 .runtime/crew；遥测与 tracing 已关闭。近似 token 计数 warning 不代表产生真实模型费用。
- 6.4 真正执行 8 次工具调用，先读缺失文件、列目录、读取三份资料，再写状态文件 /summary.md。TodoListMiddleware 是显式加入的。StateBackend 文件只保存在图状态，不写宿主文件，不跨进程保留。
- 6.5 见 DIFY.md：5 条 FAQ、平台节点绑定、3 个问题、应用发布与 API 客户端。
- 6.6 见 N8N.md：离线实际引擎验收与可导入的在线 webhook 工作流。
- 6.7 见 GRAPHRAG.md：5 篇材料、真实 index/query 命令、2 个全局/2 个局部问题及 basic 基线比较。

## 验证

在本目录运行：
```sh
.venv-frameworks/bin/python -m unittest discover -s tests -p test_frameworks.py -v
.venv-crew/bin/python -m unittest discover -s tests -p test_crew.py -v
python3.11 -m unittest discover -s tests -p test_platforms.py -v
python3.11 s66_n8n.py
.venv-graph/bin/python s67_graphrag.py
```
不要用单一环境无差别 discover 所有测试。前 3 条合计 15 项；后 2 条分别真正执行 n8n 工作流和 GraphRAG CLI。详细范围与未完成的在线验收见 VALIDATION.md。

常见问题：No module named → 使用对应环境与完整锁文件；旧 API 导入错误 → 不要混用教程旧代码；GraphRecursionError → 检查脚本和循环分支，不能只无限增大上限；PermissionError → 检查解压目录和 CrewAI 用户配置目录权限，不要以管理员身份长期运行学习代码。
