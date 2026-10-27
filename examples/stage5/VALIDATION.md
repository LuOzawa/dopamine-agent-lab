# 验证记录

日期：2026-10-27。环境：macOS，CPython 3.11.15；第三方依赖见 requirements-lock.txt。

- 7 个实验入口均执行过离线路径；禁用 site-packages 后仍能运行。
- 11 组离线命令输出保存在 expected/；输出中不包含耗时等易变字段。
- 标准库行为测试覆盖工具校验、路径限制、错误恢复、轮次/工具预算、解析修复、SQLite 与 RAG 缓存。
- 安装固定 SDK 后，通过 httpx.MockTransport 检查真实 SDK 的 Responses 请求、call_id 工具回传、reasoning 输出保留，以及 embeddings 解析与引用拒答。
- RAG 固定教学集 5/5 通过；包括 1 道资料外问题。该结果仅描述随包的 3 篇资料。
- 未发送真实模型 API 请求；模型可用性、账号权限、真实输出质量、线上费用与延迟仍需用户配置密钥后验证。
- Python 3.12 与 Windows 未执行运行验证；文档提供了对应启动方式，不宣称已在这些环境通过。

复跑：进入本目录后执行 `python -m unittest discover -s tests -v`。缺少 SDK 时，契约测试会显示 skipped；安装 requirements-lock.txt 后应没有跳过项。
