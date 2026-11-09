# 6.6 n8n 2.44.7

Python 启动器只用标准库；安装并启动 Docker Desktop，然后运行：
```sh
docker pull docker.n8n.io/n8nio/n8n:2.44.7
python s66_n8n.py
```
实测镜像 digest：`sha256:942bc274709f27f99f7c6024a785d8e8f75ac06838cabcba448abb8d9127ec7b`。可使用 `docker.n8n.io/n8nio/n8n@sha256:…` 固定同一镜像。版本标签可跨平台拉取；本次在 macOS Apple Silicon / Docker Server 29.5.3 运行。

`n8n/offline.json` 在真实 n8n 引擎中执行 Manual Trigger → Fixture → Validate → IF → Success/Fallback。三条样本为合法 JSON、损坏 JSON、缺少 summary。Validate 不会因 JSON.parse 报错终止整个任务，IF 选择友好兜底。容器没有网络，资料只读挂载，数据库不持久化，不发送通知。

## Webhook 与真实模型

`n8n/webhook.json` 是可导入的在线版本：Webhook → Model（HTTP Request）→ Validate → IF → Reply。Validate/IF 与离线版本完全相同。在线版已做结构检查，尚未在已发布 webhook 上端到端验证。

1. 在 n8n 2.44.7 的编辑器 Import from File，导入 webhook.json。
2. Model 节点选择 Header Auth 凭据；Header 名为 `Authorization`，值为 `Bearer 你的模型密钥`。凭据保存在 n8n 凭据管理器，不写进 JSON。模型默认 `gpt-5.4-mini-2026-03-17`，可换为账号有权限且支持 Responses 的模型。
3. 点击 Webhook 的 Listen for test event。复制节点显示的 Test URL（仅测试监听期间有效），以 JSON 发送 `{"text":"学习站提供分阶段课程和本地进度。"}`。
```sh
curl -X POST 'http://localhost:5678/webhook-test/stage6-summary' \
  -H 'Content-Type: application/json' \
  -d '{"text":"学习站提供分阶段课程和本地进度。"}'
```
4. 正常应返回 `ok:true`、非空 summary、`route:"success"`；Model 节点请求失败、非 JSON 或缺字段时返回 `ok:false`、友好提示及 `route:"fallback"`。响应措辞不固定。检查执行记录确认失败发生的位置。
5. 需要长期使用才发布，并使用 Production URL；对外暴露前给 Webhook 配置认证。示例只回应请求，不接通知服务。

默认最多一次模型 HTTP 请求，30 秒超时，256 输出 tokens；这不是费用上限。在线模式会把输入发给模型服务。当前 prompt 要求 JSON 但不保证模型遵守，所以仍保留验证与兜底。

## 常见报错

- Docker daemon 无法连接：启动 Docker Desktop；确认当前用户可访问 Docker。
- Mounts denied：允许 Docker 访问解压目录；完整解压，不要只复制启动器。
- 镜像不存在：先 pull 固定版本；离线容器不负责下载模型。
- 120 秒超时：检查 Docker 资源和启动日志；不要把超时改成无限。
- 401：Model 节点没有绑定 Header Auth 或密钥无效。工作流仍应进入 fallback。
- Webhook 404：测试 URL 需要监听；生产 URL 需要发布。
- 编辑器节点类型不支持：确认 n8n 2.44.7，旧版本不在本次验证范围。

官方 CLI：https://docs.n8n.io/hosting/cli-commands/
