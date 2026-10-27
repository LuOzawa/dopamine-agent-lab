# 6.5 Dify：从知识库到已发布 Chatflow

客户端仅依赖 Python 3.11 标准库，契约为 Dify API v1（核对日期 2026-10-27）。Dify Cloud 持续更新，无可锁定的云端版本；本例不声称已验证某个自托管版本。离线回放证明响应处理可运行，不证明平台检索正确。

1. 创建知识库，上传 `data/faq.md`。按标题分段，确保 FAQ 2 和 FAQ 3 分成两个 chunk。选择你有权限的 embedding 模型并等待索引完成。
2. 新建 **Chatflow**，连接 Start → Knowledge Retrieval → LLM → Answer。检索 query 绑定 Start 的用户问题，选择上述知识库，Top K 设为 3（阈值按实际结果调节）。
3. LLM 的 Context 绑定检索节点 result，用户输入绑定用户问题。系统提示词：`只根据提供的上下文回答。上下文没有答案时说“资料不足”。不要使用外部知识补全。` 在 Answer 节点绑定 LLM 的 text。
4. 启用引用与归属显示。在调试器运行下面 3 个问题，查看命中的 chunk，再发布应用，从该应用的 API Access 获取 API key。
5. 终端设置 DIFY_API_KEY（不要写进 HTML/工作流）；Cloud 使用 `https://api.dify.ai/v1`，自托管使用自己的 API 基地址。脚本不自动读取 .env。

macOS / Linux（隐藏输入；变量仅在当前 shell 有效）：
```sh
read -s DIFY_API_KEY
export DIFY_API_KEY
export DIFY_BASE_URL=https://api.dify.ai/v1
python s65_dify.py --live --query "如何查找课程？"
python s65_dify.py --live --query "进度如何保存，换设备后还能继续吗？"
python s65_dify.py --live --query "明天北京会下雨吗？"
unset DIFY_API_KEY
```

PowerShell 可通过 `$env:DIFY_BASE_URL='https://api.dify.ai/v1'` 设置地址，使用终端安全输入将密钥存入 `$env:DIFY_API_KEY`；结束后 `Remove-Item Env:DIFY_API_KEY`。不要把密钥粘贴进代码或截图。

验收：第一个问题回答查找方法；第二个同时覆盖 FAQ 2、3（跨段综合，而非多个文档）；第三个明确拒答。前两个 metadata.retriever_resources 应有 faq.md；引用的存在不等于语义正确，需核对 chunk 和答案。云端实际措辞与分数会变化。若要做跨文档检索，将 FAQ 2、3 分别另存文件上传，再重复第二问。

常见报错：401 检查应用密钥；404 检查 /v1/chat-messages 路径和已发布应用；400 检查 inputs 必填变量及 Chatflow 类型；429 检查额度；返回空来源时检查索引、检索绑定与引用设置；无关问题仍回答时检查上下文限制和调试轨迹。

官方契约：https://docs.dify.ai/en/api-reference/chat-messages/send-chat-message
