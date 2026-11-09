# 第 5 阶段：可运行实验

默认离线，七节都只需 Python 标准库。离线模型为固定脚本驱动器，不是大模型；RAG 离线版使用字符二元组词频向量和原文摘录，不具备语义 embedding 能力。天气为固定教学数据，即使使用 `--live` 也不是实时天气。

## 环境与安装

验证日期：2026-10-27。离线运行与本地模拟 HTTP 契约测试已在 **Python 3.11.15** 验证；没有发送真实模型 API 请求。建议使用 Python 3.11；Python 3.12 可尝试，但未在本次环境实测。

直接依赖基线：`openai==2.29.0`、`python-dotenv==1.2.2`，不是“当前最新版”。`requirements-lock.txt` 固定本次安装的全部 17 个包，`requirements.txt` 只固定两个直接依赖。SQLite 来自 Python 标准库。

先在终端进入本目录；从学习站根目录进入可用：

```sh
cd examples/stage5
```

macOS / Linux：

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python --version
python s51_setup.py
```

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe s51_setup.py
```

Windows 无需修改脚本执行策略；下文的 `python` 均可替换成 `.\.venv\Scripts\python.exe`。

只有真实 API 模式和 SDK 契约测试需要安装第三方依赖：

```sh
python -m pip install -r requirements-lock.txt
```

复制 `.env.example` 为 `.env`（macOS/Linux：`cp .env.example .env`；PowerShell：`Copy-Item .env.example .env`），用编辑器填入 `OPENAI_API_KEY`。如果已经存在 `.env`，直接编辑，不要覆盖。默认模型为 `gpt-5.4-mini-2026-03-17`，可在 `.env` 换成账号可用、支持 Responses 和 function calling 的模型。示例固定官方端点，不读取 `OPENAI_BASE_URL`。

`--live` 会将任务、工具结果或 RAG 资料发送给 OpenAI 并产生 API 费用；先用仓库内的教学资料验证。每次请求超时 30 秒，不自动重试，Agent 默认最多 6 轮 / 8 次工具调用，单次输出最多 2048 tokens。该限制不是美元预算，也不保证网络异常时绝不重复计费。

## 七个实验

所有命令均在本目录运行；保持 `lab/`、`data/` 和脚本同级，不能只复制一个入口脚本。

| 小节 | 离线命令 | 应观察到的结果 |
|---|---|---|
| 5.1 环境 | `python s51_setup.py` | `pong`，明确标记固定响应 |
| 5.2 工具 | `python s52_tools.py --invalid` | 空城市报错后修复，天气 22°C、算式 30，4 轮结束 |
| 5.3 记忆 | `python s53_memory.py` | 内存库写入 → 过期不再读取 → 删除，无持久数据 |
| 5.4 Agent | `python s54_agent.py` | missing.md 失败 → 列目录 → 读取 setup.md → 完成 |
| 5.5 项目化 | `python -m lab --dry-run` | 只打印静态任务与允许工具，不初始化模型、不执行工具、不写文件 |
| 5.6 停机 | `python s56_guardrails.py` | 第 2 轮检测重复，实际只执行 1 次工具 |
| 5.7 RAG | `python s57_rag.py --eval` | 5 道固定题通过，含 1 道资料外拒答 |

`python -m lab` 可实际执行离线问答演示。离线问答固定读取 setup.md，不理解任意问题；使用自定义问题时加 `--live`。

真实调用：

```sh
python s51_setup.py --live
python s52_tools.py --live
python s54_agent.py --live
python -m lab --live --question "读取 setup.md，说明密钥配置方式。"
python s56_guardrails.py --live
python s57_rag.py --live --question "API 密钥存放在哪里？"
python s57_rag.py --live --eval
```

5.3 是本地 SQLite 实验，不需要 `--live`。API 的措辞、调用轮次与费用随模型变化；本目录 `expected/` 是已执行的**离线**输出，不是对真实 API 的结果保证。

### 5.3 持久记忆

```sh
python s53_memory.py set --id language --content "回答用中文" --confirmed
python s53_memory.py list
python s53_memory.py set --id language --content "回答用英文" --confirmed
python s53_memory.py delete --id language
```

数据保存在 `.runtime/memory.sqlite3`，按 id 更新，默认 30 天过期，可用 `--ttl-days` 改成 1–365 天。过期只影响读取，不会物理清除旧行；`delete` 删除指定 id。它是单用户教学存储，没有账户隔离、加密或历史审计。

### 5.6 故障注入

```sh
python s56_guardrails.py --scenario malformed
python s56_guardrails.py --scenario bad-json
python s56_guardrails.py --scenario docs --max-turns 1
python s56_guardrails.py --scenario docs --max-calls 1
```

分别验证：一次 JSON 错误后恢复、第二次错误即停止、轮次预算停止、工具次数预算停止。输出包含已成功执行的工具、未完成任务和下一步建议。`tokens=0` 仅表示离线驱动器没有调用模型。真实模式不保证复现人工注入的故障；`--scenario` 只控制离线驱动器。动作指纹只检测连续重复，交替循环由轮次/工具预算兜底。

### 5.7 RAG 与缓存

随包附带 3 篇原创教学 Markdown，按段落切分；长段落每块 240 字、重叠 40 字。离线词频与真实 embedding 各自保存 `.runtime/rag-offline.json` / `rag-live.json`。内容、切分配置或 embedding 模型变化会重建索引；缓存命中不再重复嵌入文档，但真实模式每次提问仍会嵌入查询。

```sh
python s57_rag.py --question "API 密钥存放在哪里？"
python s57_rag.py --question "火星最高的山峰叫什么？"
python s57_rag.py --question "如何保存学习进度？" --threshold 0.2
```

首次显示 `index=built`，后续显示 `index=cache`。离线默认阈值 0.12、真实默认阈值 0.35，都是教学起点，应按自己的语料评估调整。检索最多返回 2 个片段；引用编号越界或缺失时拒绝提供无法核对的答案。编号校验不能证明答案语义正确，必须回查引用原文。真实模式的固定测试也可能失败；结果仅检查预设来源、关键词与拒答，不是通用质量评分。

## 回归测试

```sh
python -m unittest discover -s tests -v
```

不安装第三方包也可执行标准库行为测试；安装锁定依赖后额外运行真实 SDK + `httpx.MockTransport` 的契约测试。契约测试只在内存中模拟 HTTP 响应，不访问网络、不读取真实密钥、不产生 API 费用。

覆盖计算器拒绝代码执行、参数校验、路径边界、工具错误恢复、预算终止、记忆持久化/过期/删除、RAG 缓存失效、5 题检索与引用、真实 SDK 的工具结果回传和 embedding 响应解析。

## 常见报错

| 错误 / 现象 | 处理 |
|---|---|
| `python3.11` 或 `py -3.11` 找不到 | 先安装 Python 3.11；不要直接使用系统旧版 Python |
| `No module named lab` / 找不到脚本 | 进入 `examples/stage5`，保持整个示例目录完整 |
| `No module named openai` / `dotenv` | 用当前解释器执行 `python -m pip install -r requirements-lock.txt` |
| 缺少 `OPENAI_API_KEY` | 编辑本目录 `.env`；离线运行则去掉 `--live` |
| 401 / AuthenticationError | 检查密钥是否有效、是否来自正确项目 |
| 403 / 404 | 检查项目权限与 `OPENAI_MODEL` 是否可用 |
| 429 | 检查额度与速率限制，稍后重试 |
| 超时或连接失败 | 检查网络、代理及证书，不要禁用 TLS 验证 |
| `permission_denied` | 文件必须在 `data/docs` 内，工具必须在白名单内 |
| `repeated_action` / `turn_limit` / `tool_limit` | 这是预期停机，先检查已完成/未完成项再调整任务 |
| 缓存损坏或维度不一致 | 删除本实验 `.runtime/rag-offline.json` 或 `rag-live.json` 后重建；不要删除记忆数据库 |
| RAG 没有命中 | 查看片段和分数，补充资料或校准阈值；不要把强行回答当作成功 |

## 官方依据

- [Responses 快速开始](https://developers.openai.com/api/docs/quickstart)
- [函数调用与结果回传](https://developers.openai.com/api/docs/guides/function-calling)
- [Embedding 接口](https://developers.openai.com/api/docs/guides/embeddings)
- [默认模型与快照](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
- [OpenAI Python SDK 2.29.0](https://pypi.org/project/openai/2.29.0/)
- [python-dotenv 1.2.2](https://pypi.org/project/python-dotenv/1.2.2/)

以上接口与版本信息核对于 2026-10-27；官方文档存在不代表当前账号有访问权限。真实 API 端到端调用尚未验证。
