# 验证记录 · 2026-10-27

环境：macOS Apple Silicon，Python 3.11.15；三个独立虚拟环境；Docker Server 29.5.3，n8n 2.44.7。版本全集位于 requirements/*-lock.txt；这是实测复现基线，不是最新版承诺。

| 范围 | 结果 | 能证明什么 |
| --- | --- | --- |
| LangChain | 两问题实跑 + 工具/消息测试通过 | 真正 create_agent 循环、结果关联与算式拒绝非法输入 |
| LangGraph | 成功/拒答实跑 + checkpoint/线程隔离测试通过 | 两次检索上限、暂停后恢复；不证明跨进程持久化 |
| CrewAI | 三角色及去掉编辑两种配置通过 | 真实顺序任务与上下文传递；固定响应不证明写作质量 |
| Deep Agents | 8 次真实工具调用通过 | 缺文件→列目录→读文件→写摘要，待办完成；不证明自主规划 |
| Dify | 3 个样本回放及请求/响应/错误契约测试通过 | 客户端处理；未创建或发布在线 Chatflow |
| n8n | 断网临时容器中真实执行，3/3 路由通过 | 合法/损坏/缺字段 JSON 的分支行为；在线 webhook 与模型未端到端验收 |
| GraphRAG | 官方 init 与 index --dry-run --skip-validation 通过 | 配置和输入准备；没有真实索引、查询质量或费用结论 |

行为与契约测试共 15 项（frameworks 5、crew 2、platforms 8）；七个入口的标准输出由 tools/capture_stage6_outputs.py 收集。没有调用付费模型，也没有发送通知。

实际发现并解决：Deep Agents 0.7.32 默认工具不含 write_todos，需要显式 TodoListMiddleware；FileData.content 当前为字符串，不能按旧版行列表 join。CrewAI 导入时会访问用户配置目录，关闭 tracing 也不会免除目录初始化。GraphRAG 新版使用 completion_models/embedding_models；LiteLLM 默认可能获取远端价格表，离线检查显式切换本地表。

可能出现且不影响当前验收的第三方日志：CrewAI 近似 token 计数及内部弃用 warning；n8n 缺少 Python runner（本例只使用 JS runner）。这些日志没有作为模型输出收录。

交付检查已通过：HTML 嵌入源码与文件一致；40 文件下载包排除密钥/缓存；独立解压后 7 个入口输出与 expected 一致；14 个页面的本地链接、锚点和 47 个章节保持完整；搜索/进度/移动目录的 13 项 DOM 回归通过；生成器重复运行不改变 HTML。本轮没有浏览器视觉截图验证；未声称 Windows/Linux 安装已实测。
