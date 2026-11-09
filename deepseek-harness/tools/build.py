#!/usr/bin/env python3
"""生成 DeepSeek Harness 学习手册的静态页面与搜索索引。

用法：python3 tools/build.py
输出：index / stage-1..6 / contents / search / audit / about + assets/search-index.*
"""
import html
import json
import re
import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://www.runoob.com/deepseek-harness/"
# Existing audit snapshot, not the date on which HTML happens to be rebuilt.
AUDIT_DATE = "2026-10"

STAGES = [
    dict(n=1, title="认识与安装", en="Orientation", lede="先确认它解决什么问题，再选一条安装路线跑通。不写插件，但决定后面顺不顺。", hours="1.5"),
    dict(n=2, title="配置与形态", en="Configuration", lede="模型、Python SDK、插件安装、自动化、多模态与四种运行模式。", hours="2.5"),
    dict(n=3, title="插件基础", en="Plugin Basics", lede="从 apply(ctx) 到生命周期：写出可加载、可清理、可配置的插件。", hours="3.5"),
    dict(n=4, title="服务、隔离与事件", en="Services & Events", lede="插件之间如何协作：服务、作用域、事件分发与能力三角色。", hours="2"),
    dict(n=5, title="实战与发布", en="Build & Ship", lede="把能力拆成三角色，接任意模型，打成可安装、可分发的组合包。", hours="3"),
    dict(n=6, title="运行与生产", en="Runtime & Safety", lede="工具流水线、沙箱与审批、会话日志、防御性编程与事故复盘。", hours="2.5"),
]

L = []

def add(**kw):
    L.append(kw)

# ── 阶段 1 ────────────────────────────────────────────────────────────────
add(id="s1-1", stage=1, num="1.1", title="Agent = Model + Harness", tag="定位", dur="约 25 分钟",
    src="deepseek-harness-intro.html",
    goal="用一句话解释 dsh 的定位，并说出「一切皆插件」在运行时到底意味着什么。",
    pre="无。知道 API Key 与命令行即可。",
    points=[
        "DeepSeek Harness（dsh）是 DeepSeek 开源的 Agent Harness，MIT 许可、TypeScript 编写，目前是 0.2.x 预览版；它不训练模型，而是组织模型运行的环境。",
        "Cordis 内核只负责插件的加载、卸载与依赖管理；模型、工具、会话、沙箱、存储、循环、调度、UI 都由插件提供。",
        "官方公式是 Agent = Model + Harness；四种运行模式只是四组预设插件，不是能力等级。",
        "可观测性是核心差异：模型看到的系统提示、思维链、工具调用与结果都写入仅追加会话日志，历史从日志派生，可回放与分叉。",
        "模型无关：DeepSeek 官方端点、已收录的目录提供方、自定义 OpenAI 兼容端点都可以接入。",
    ],
    task="画一张「模型 / Harness / 工作区」三层图，在 Harness 层列出至少 6 个可替换部件（如工具、会话、沙箱、存储、循环、UI），并圈出你最想替换的一个，写一句原因。",
    qa=[
        ("它和 LangChain 这类框架有什么区别？", "LangChain 是帮助「构建」Agent 的库；dsh 是「运行」Agent 的完整 Harness，连会话、沙箱、审批、UI、调度都做成可替换插件。前者回答怎么搭，后者回答怎么稳定运行和替换能力。"),
        ("预览版意味着什么？", "0.x 版本可能有破坏兼容性的变更。学习时跟文档走，真正部署要锁定版本、保留配置与插件清单，并在升级前看迁移说明。"),
    ],
    status="ok", impact="概念定位", sev="低", prio="—",
    note="与 npm 0.2.1-rc.5、PyPI 0.2.1rc2 的预览状态一致；MIT 许可已在 npm 元数据核对。")

add(id="s1-2", stage=1, num="1.2", title="安装：四条路线怎么选", tag="安装", dur="约 30 分钟",
    src="deepseek-harness-install.html",
    goal="根据操作系统与技术栈选一条安装路线，并完成一次可验证的启动。",
    pre="会用终端；npm/源码路线的 Node.js 版本要求待核实，以所选 dsh 版本的官方安装文档为准。先用 <code>node -v</code> 查看本机版本。",
    points=[
        "桌面版：Windows 64 位、macOS Apple 芯片，免装 Node，适合日常办公与文件处理。",
        "npm：全局安装后用 <code>dsh web</code>，或直接 <code>npx @deepseek-ai/dsh web</code>；默认地址 <code>http://127.0.0.1:3080</code>。",
        "源码：准备 Git、pnpm 与符合官方安装文档要求的 Node.js；教程所写「Node 24.9+」待核实。依次执行 <code>pnpm install</code>、<code>pnpm run build</code>、<code>pnpm dsh web</code>。",
        "Python SDK：Python 3.10+，自带运行时，不需要系统 Node；适合把 Agent 接进 Python 程序。",
        "预览版阶段，安装包、命令与界面都可能变化；生产使用要锁定版本，不要把「最新」当默认。",
    ],
    task="做一张路线表：操作系统 / 技术栈 / 是否需要 Node / 启动命令 / 验证点。只选一条真正执行，并记录版本号与失败信息。",
    qa=[
        ("Node 22 还能用吗？", "待核实：教程声称需要 Node.js 24.9+、不再支持 Node 22，但现有审计未能独立确认。先用 node -v 查看版本，再查所选 dsh 版本的官方安装文档；不要仅凭教程或一次启动成功判断兼容性。"),
        ("桌面版和 Web UI 是两套东西吗？", "是同一产品的不同入口：桌面版是本地应用窗口，Web UI 由命令启动后用浏览器访问。核心能力可能接近，但 Node 依赖、插件入口与后台行为不同。"),
    ],
    status="todo", impact="版本要求", sev="中", prio="P2",
    note="npm 包存在（0.2.1-rc.5），但 npm 元数据未声明 engines；Node 24.9+ 与「Node 22 不再支持」需以官方安装页为准。")

add(id="s1-3", stage=1, num="1.3", title="桌面版：先用只读任务验收", tag="上手", dur="约 25 分钟",
    src="deepseek-harness-desktop.html",
    goal="用桌面版完成一次只读工作区分析，并检查它实际读了哪些文件。",
    pre="完成 1.2；准备一个专用测试目录。",
    points=[
        "安装后先配置模型，再选择工作区；第一次不要用生产目录、密钥目录或含隐私的文件夹。",
        "首个任务只读：分析目录结构、说明文件用途，明确禁止修改、删除与安装。",
        "文件编辑、命令执行与后台任务可能改变本地数据；能力范围取决于当前版本与已安装插件。",
        "桌面版提供插件入口与工作区管理，但具体审批行为以当前版本为准。",
        "安装包要核对来源与签名；不要为了安装而关闭系统安全防护。",
    ],
    task="在测试目录里让桌面版分析目录结构，记录三件事：它读了哪些文件、有没有越界、有没有出现审批提示。再故意要求修改一个文件，观察权限边界。",
    qa=[
        ("为什么第一次不能用生产目录？", "Agent 可能执行命令或改文件，错误不可逆；测试目录能把损失限制在可丢弃的范围内，也方便对照它实际读了什么。"),
        ("桌面版能代替 Web UI 吗？", "对日常任务通常可以；但插件开发、查看终端日志、调试配置树仍更适合 Web UI / 源码方式。两者是入口差异，不是能力等级。"),
    ],
    status="ok", impact="产品使用", sev="低", prio="—",
    note="平台与安装包信息来自教程；具体界面与审批行为会随预览版变化，以官网为准。")

add(id="s1-4", stage=1, num="1.4", title="第一次 Web UI：从启动到只读任务", tag="上手", dur="约 30 分钟",
    src="deepseek-harness-start.html",
    goal="独立完成启动、模型配置、工作区选择与首条只读任务，并能定位常见失败。",
    pre="完成 1.2；准备 DeepSeek 账号或 API Key。",
    points=[
        "启动：<code>npx @deepseek-ai/dsh@latest web</code>；端口冲突用 <code>--port 8080</code>，或 <code>--port 0</code> 让系统选空闲端口。",
        "首次要登录或填 API Key；全新的 Web UI 不会自动选中工作区，未选中时输入框不可用。",
        "预设（标准 / PTC / 极简 / 创造）决定插件组合；权限模式（只读 / 工作区写 / 完全 / 自动审查）决定文件与命令边界，两者独立。",
        "第一条任务先只读，并要求它说明实际读取了哪个文件；去工具记录里核对路径，而不是只看回答。",
        "页面能打开只说明本地服务成功；401、无响应、无法发送分别对应凭据、模型、工作区三类问题。",
    ],
    task="跑一条只读任务：「读取当前工作区的 README.md，概括项目用途，只读，不创建/修改/删除文件，并说明实际读取的路径。」记录四个检查点：页面、工作区、模型、工具记录。",
    qa=[
        ("为什么输入框不可用？", "最常见是没有选中工作区，其次是模型未配置或凭据无效。先看工作区选择器与模型设置，不要反复重装。"),
        ("只读提示词能保证不写文件吗？", "不能。提示词是任务约束，真正的边界由权限模式与沙箱策略决定；验证时要看工具记录和实际文件状态。"),
    ],
    status="ok", impact="上手流程", sev="低", prio="—",
    note="端口、工作区与权限说明与教程一致；具体 UI 文案可能随版本变化。")

# ── 阶段 2 ────────────────────────────────────────────────────────────────
add(id="s2-1", stage=2, num="2.1", title="模型配置：官方、目录与自定义端点", tag="配置", dur="约 35 分钟",
    src="deepseek-harness-model-providers.html",
    goal="配好官方 + 一个自定义提供方，并说清密钥存在哪里、Provider ID 为什么不能改。",
    pre="完成 1.4；有一个可用的模型端点。",
    points=[
        "三类提供方：DeepSeek 官方、已安装目录（Anthropic、OpenAI、Kimi、GLM 等）、自定义 OpenAI 兼容端点。",
        "密钥是只写的，保存在 <code>$DSH_HOME/.credentials.yaml</code>；配置文件只保留凭据引用。",
        "自定义提供方要填 Provider ID（永久）、baseURL、协议（<code>openai-completions</code> / <code>openai-responses</code> / <code>anthropic-messages</code>）与至少一个模型。",
        "模型目录可以跟随发布列表，也可以手动维护；自定义视觉模型必须显式声明图片输入，否则发图会在发送前被拒绝。",
        "推理等级由适配器/目录声明；自定义网关注意 <code>thinkingFormat</code>、<code>supportsDeveloperRole</code>、<code>maxTokensField</code> 等兼容项。",
    ],
    task="配置官方 + 一个自定义提供方。记录：协议、baseURL、模型名、Provider ID。然后故意填错一次 baseURL，观察错误发生在保存、请求还是模型选择阶段。",
    qa=[
        ("Provider ID 为什么不能改？", "它会被请求、已保存会话、模型默认值与凭据引用使用；改名会让旧记录找不到提供方。需要改名时，新增一个提供方并删除旧的。"),
        ("密钥会写进配置文件吗？", "不会。真实密钥存 <code>.credentials.yaml</code>，配置里是引用；环境变量与已存凭据同名时，已存凭据优先。"),
    ],
    status="ok", impact="配置", sev="低", prio="—",
    note="提供方类型与存储路径来自教程；模型列表与可用模型以当前端点返回为准。")

add(id="s2-2", stage=2, num="2.2", title="Python SDK：把 Agent 放进程序", tag="集成", dur="约 40 分钟",
    src="deepseek-harness-python-sdk.html",
    goal="用 SDK 在 Python 里跑一次任务，并读懂 workspace 与 dsh_home 的隔离。",
    pre="Python 3.10+、Git、一个隔离工作区。",
    points=[
        "安装：<code>python -m pip install deepseek-harness-sdk</code>；SDK 自带运行时，不需要系统 Node.js。",
        "<code>DeepSeekHarness</code> 是上下文管理器：进入时延迟启动内置运行时，退出时释放；同一个 harness 可以多次 <code>run</code>。",
        "<code>workspace</code> 与 <code>dsh_home</code> 必须是绝对路径；SDK 不会静默读取 <code>~/.dsh</code>。",
        "复用同一个 session id 会保留该会话的 Bash 进程，包括工作目录、环境变量与 shell 函数。",
        "日志落在 <code>$dsh_home/sessions/</code> 的 JSONL；profile 与插件也保存在 dsh_home 内。",
    ],
    task="跑通仓库的 minimal.py，或写一个 20 行包装。然后检查：生成的 profile 名称、JSONL 路径、第一次与第二次 run 的 Bash 工作目录是否延续。",
    qa=[
        ("为什么要隔离 dsh_home？", "它保存 profile、插件与会话日志，属于可写状态；用专用目录能避免污染日常配置，也方便测试后整个删除。"),
        ("session 复用有什么风险？", "上一次的 cd、export 与 shell 函数会延续，可能让下一次调用在错误目录或错误凭据下运行。需要干净环境时换 session id。"),
    ],
    status="ok", impact="SDK 集成", sev="低", prio="—",
    note="PyPI 包存在（0.2.1rc2，requires Python >=3.10）；API 细节以 <code>deepseek_harness</code> 当前类型为准。")

add(id="s2-3", stage=2, num="2.3", title="插件：查找、安装、验证", tag="插件", dur="约 30 分钟",
    src="deepseek-harness-plugins.html",
    goal="安装一个插件，并用四个检查点验证它真的生效，而不是只看到「安装成功」。",
    pre="完成 1.4；知道 profile 与 bundle 的概念。",
    points=[
        "基础能力已由当前 profile 提供，不需要为首次任务重复安装文件、Shell、模型接入。",
        "发现页的索引校验只证明格式有效，不代表官方审核了作者、代码或安全性；安装前核对来源、版本、兼容性。",
        "CLI：<code>dsh plugin --profile web add 包名@版本</code>；只有声明 <code>dsh.bundle</code> 的包才贡献配置层。",
        "四个验证点：兼容性、配置加载（dump-config）、依赖就绪、实际能力（工具被调用 / UI 完成任务）。",
        "安装成功不等于已加载；普通依赖可以安装成功，但不会激活任何能力。",
    ],
    task="安装或开发一个 hello 插件，逐项通过四个验证点。然后故意安装一个没有 <code>dsh.bundle</code> 的普通包，确认它只是依赖、没有层标记。",
    qa=[
        ("发现页能刷新就安全吗？", "不是。索引源只提供标题、作者、版本等元数据；代码是否可信要自己看仓库、权限与构建脚本。"),
        ("安装后 UI 没入口，先查什么？", "先看 dump-config 是否包含该层，再看依赖是否就绪（是否停在 PENDING），最后才看 UI。安装成功不代表加载成功。"),
    ],
    status="ok", impact="插件管理", sev="低", prio="—",
    note="安装命令与验证思路与教程一致；索引源与插件市场状态会变化。")

add(id="s2-4", stage=2, num="2.4", title="自动化任务：会话级提醒", tag="自动化", dur="约 30 分钟",
    src="deepseek-harness-schedule.html",
    goal="创建一个定时提醒，并说清投递语义、时区与不支持的操作。",
    pre="标准 / PTC / 创造模式；模型已配置。",
    points=[
        "在会话里用一句话创建；模型调用 <code>schedule_create</code> / <code>schedule_list</code> / <code>schedule_update</code> / <code>schedule_delete</code> 四个工具。",
        "六类规则：After、At、Every、Daily、Weekly、cron；涉及本地时间的规则要带 IANA 时区。",
        "投递总是回到创建它的会话，不新建会话；宿主关闭时调度停止，重启后补投逾期的一次性提醒或最近一次重复任务。",
        "没有暂停开关；删除会移除历史，但不会删除原对话；投递不保证恰好一次。",
        "极简模式没有这些工具与时钟上下文；子代理也被 deny，无法创建提醒。",
    ],
    task="创建一个「每天 23:00 提醒我查看天气」的任务，核对频率与时区；修改一次时间；再删除。记录页面上「已投递」与「已完成」的区别。",
    qa=[
        ("为什么模型需要当前时间？", "模型本身不知道「现在几点」，没有时钟上下文就无法把「每天晚上 11 点」换算成正确规则；时区也要显式提供。"),
        ("能把它当 cron 用吗？", "不建议。它绑定会话、没有外部通知渠道、不保证执行成功；对外通知类任务应把它当触发器，让 Agent 先检查再执行。"),
    ],
    status="ok", impact="功能边界", sev="低", prio="—",
    note="调度规则与投递语义来自教程；具体保留窗口与 UI 以当前版本为准。")

add(id="s2-5", stage=2, num="2.5", title="多模态：图片输入与视觉模型", tag="多模态", dur="约 30 分钟",
    src="deepseek-harness-modality.html",
    goal="用视觉模型读一张图表，并知道三种图片传法与输入类型声明。",
    pre="完成 2.1；有一个支持视觉的模型。",
    points=[
        "图片先被视觉编码器切成 patch 并转成向量，再与文本 token 拼成同一序列；图片会消耗 token。",
        "三种传法：base64 内联、外部 URL、Files API；分别对应「一次性小图 / 已有图床 / 多次复用」。",
        "三种 API 风格：Chat Completions、Anthropic Messages、OpenAI Responses；图文混合输入都支持。",
        "自定义提供方的模型默认按纯文本处理，必须显式勾选图片输入，否则附加图片会在发送前被拒绝。",
        "多模态不是 OCR 替代品；金额、坐标、表格逐格还原等高风险读数要人工复核。",
    ],
    task="传一张带坐标轴的图表，让它提取 3 个数据点，再追问「你最不确定的读数是哪一个，为什么」。对照你自己读图的结果，记录偏差来源。",
    qa=[
        ("为什么一定要声明输入类型？", "没有环节能询问端点接受哪些模态，dsh 采取「先声明后使用」；未声明的模型收到图片会在发送前被拒绝。"),
        ("什么时候该用专用 OCR？", "需要精确坐标、逐格还原表格、票据字段抽取时，专用文档解析或 OCR 更稳定、更便宜，也更容易审计。"),
    ],
    status="todo", impact="模型与计费", sev="中", prio="P2",
    note="视觉模型名、单图 token 上限与 benchmark 数字无法独立确证；以 DeepSeek 官方模型页与 API 文档为准。")

add(id="s2-6", stage=2, num="2.6", title="四种运行模式：标准 / PTC / 极简 / 创造", tag="模式", dur="约 30 分钟",
    src="deepseek-harness-modes.html",
    goal="为四类任务选择模式，并解释切换模式改变的是插件组合，不是模型权限。",
    pre="完成 1.4。",
    points=[
        "模式 = 一组预设插件，不是能力等级：标准干活、PTC 编排、极简测量、创造改造。",
        "PTC 把工具收拢为 <code>run_code</code>，模型写一段 TypeScript 程序组合调用；只读调用可并行（教程所称「默认 10 路」待核实，以所用版本为准），写操作按提交顺序。",
        "极简模式只保留持久 bash 与 <code>str_replace_editor</code>，用于评测模型、复现问题，不是低配电脑的轻量版。",
        "创造模式继承标准能力，并增加运行时检查、内存中试验插件与 preset 创作指引。",
        "切换预设不改变文件权限；权限与沙箱是另一套策略，必须单独设置。",
    ],
    task="为四个任务各选一种模式并写一句理由 + 一个风险：修一个 bug、批量重构 20 个文件、比较两个模型的编码能力、给团队做一套自定义预设。",
    qa=[
        ("PTC 省的是什么？", "省上下文：多步工具调用的中间结果留在程序里，只有返回值与日志回到对话；代价是模型要会写程序，调试也更复杂。"),
        ("极简模式适合日常吗？", "不适合。它是刻意做减法的评测环境，只保留两个工具；日常任务用标准模式，需要编排时再上 PTC。"),
    ],
    status="todo", impact="发布信息", sev="低", prio="P2",
    note="「2026 年 8 月开源」等时间与 PTC 并行上限来自教程，未在公开元数据中确证；以官方发布说明为准。")

# ── 阶段 3 ────────────────────────────────────────────────────────────────
add(id="s3-1", stage=3, num="3.1", title="第一个插件：apply(ctx) 与三种形态", tag="插件", dur="约 35 分钟",
    src="deepseek-harness-first-plugin.html",
    goal="写出最小插件，理解 ctx 的作用，并避开 default export 丢 inject 的坑。",
    pre="源码安装完成；会 TypeScript 基础。",
    points=[
        "插件导出 <code>name</code> 与 <code>apply(ctx)</code>；框架加载时调用 apply，ctx 既是注册入口也是资源账本。",
        "三种形态：函数、对象、Service 子类；大多数插件用函数形式，需要提供服务时用类形式。",
        "对象形态不要再写 <code>export default apply</code>：Loader 会取 default 裸函数，命名空间上的 inject 会整个丢失（官方复盘 0001）。",
        "本地开发时插件路径必须是绝对路径；相对路径不会被 Loader 按预期解析。",
        "apply 里不要做长时间阻塞；重活应注册成工具或后台任务。",
    ],
    task="写一个 hello-plugin，加载时打印日志；再改成对象形态并声明 <code>inject: ['tools']</code>，用 dump-config 或日志确认 inject 没有丢。",
    qa=[
        ("ctx 到底是什么？", "框架传给插件的上下文对象：你通过它注册事件、工具、服务，它也记录这些注册，卸载时按作用域清理。"),
        ("为什么 default export 会丢 inject？", "Loader 优先取模块的 default 导出；如果 default 是裸函数，命名空间上声明的 name/inject 不会被一起取走，插件就在空依赖下启动。"),
    ],
    status="ok", impact="插件基础", sev="低", prio="—",
    note="与教程及官方事故复盘 0001 的描述一致。")

add(id="s3-2", stage=3, num="3.2", title="加载本地插件：cordis.yml + --patch", tag="插件", dur="约 30 分钟",
    src="deepseek-harness-load-plugin.html",
    goal="用 patch overlay 把本地插件加载进 Web UI，并解释 profile 与 patch 的分工。",
    pre="完成 3.1；有源码仓库。",
    points=[
        "<code>cordis.yml</code> 是 patch overlay；<code>insert</code> 用于插入插件行。",
        "<code>name</code> 写绝对路径；patch 文件只贡献配置，不改变 Loader 解析模块路径的 profile 目录。",
        "启动：<code>pnpm dsh web --patch ./scratch-plugin/cordis.yml</code>。",
        "profile 决定应用由哪些组合包组成；patch 只是在启动时叠加的一层。",
        "交付给别人时改用组合包（bundle），不要让用户手改绝对路径。",
    ],
    task="加载 hello 插件，确认三件事：终端出现加载日志、插件列表能看到它、dump-config 里有对应层。然后把插件路径改成相对路径，观察失败。",
    qa=[
        ("为什么必须是绝对路径？", "Loader 解析模块时以 profile 目录为基准，相对路径会指到错误位置；patch 本身不会改变这个基准。"),
        ("--patch 和 bundle 怎么选？", "本地开发调试用 --patch；要分发给别人、需要版本与依赖管理时用 bundle。"),
    ],
    status="ok", impact="插件加载", sev="低", prio="—",
    note="路径与 patch 行为来自教程；不同版本的 Loader 报错文案可能不同。")

add(id="s3-3", stage=3, num="3.3", title="自动清理：ctx.effect 与资源账本", tag="生命周期", dur="约 30 分钟",
    src="deepseek-harness-effects.html",
    goal="用 ctx.effect 管理定时器等外部资源，并验证插件卸载后资源真的停止。",
    pre="完成 3.1 / 3.2。",
    points=[
        "通过 ctx 注册的监听、工具、LLM 适配器会自动撤销；卸载时按注册顺序的逆序清理。",
        "定时器、网络连接等不在自动列表里的资源，用 <code>ctx.effect(() =&gt; disposer)</code> 显式清理。",
        "异步 disposer 会并发执行，不保证逐个完成；有顺序依赖的清理步骤要放进同一个 effect，由它串行等待。",
        "先注册后清理：后注册的资源先被清理。",
        "资源泄漏的典型症状是重复监听、重复注册、卸载后仍有输出。",
    ],
    task="写一个每 5 秒打印心跳的插件，加载后卸载；观察 15 秒内是否还有输出。再把定时器改成不返回 disposer，复现泄漏。",
    qa=[
        ("通过 ctx 注册的定时器还要手动 clearInterval 吗？", "如果定时器是通过 <code>ctx.effect</code> 创建并返回 disposer，不需要；直接使用 Node API 创建而不交给 ctx 的，框架不一定能追踪。"),
        ("为什么清理顺序重要？", "后注册的资源可能依赖先注册的资源；逆序清理能先拆掉上层依赖，再释放底层资源。"),
    ],
    status="ok", impact="插件资源", sev="低", prio="—",
    note="清理机制与异步处置器行为来自教程；具体 disposer 调度以 Cordis 当前实现为准。")

add(id="s3-4", stage=3, num="3.4", title="声明依赖：inject 与可选服务", tag="依赖", dur="约 30 分钟",
    src="deepseek-harness-inject.html",
    goal="区分必需依赖与可选依赖，并解释服务消失后插件为什么会自动重载。",
    pre="完成 3.1。",
    points=[
        "<code>export const inject = ['tools']</code> 声明必需依赖；服务未就绪时 Fiber 停在 PENDING，不执行 apply。",
        "可选依赖不写 inject，在使用处用 <code>ctx.get('metrics')</code> 查询，可能得到 undefined。",
        "运行中必需服务消失 → 依赖它的插件自动 dispose；服务回来 → 自动重新加载。",
        "自动重载不等于恢复运行时数据；需要保留的状态要外置。",
        "内置服务：<code>ctx.tools</code>（工具）、<code>ctx.llm</code>（模型）、<code>ctx.agents</code>（子智能体）。",
    ],
    task="给插件加一个可选的 metrics 依赖：没有服务时正常加载并跳过记录；有服务时调用 <code>record</code>。再用 dump-config 确认依赖声明。",
    qa=[
        ("PENDING 是错误吗？", "不是。它表示插件已声明但依赖未就绪；依赖一直不来就一直等。若配置错误则会进入 FAILED，两者要分开看。"),
        ("自动重载会保留内存状态吗？", "不会。重载创建新的 Fiber，旧注册被清理；需要延续的状态放数据库、文件或外部服务。"),
    ],
    status="ok", impact="依赖机制", sev="低", prio="—",
    note="必需/可选依赖与服务消失行为与教程一致。")

add(id="s3-5", stage=3, num="3.5", title="第一个工具：defineTool", tag="工具", dur="约 35 分钟",
    src="deepseek-harness-define-tool.html",
    goal="用 defineTool 定义 greet 工具，让模型真正调用，并理解 schema 如何进入提示词。",
    pre="完成 3.4；tools 服务可用。",
    points=[
        "字段：<code>name</code>、<code>description</code>、<code>parameters</code>、<code>output.schema</code>、<code>output.render</code>、<code>execute</code>。",
        "schema 会自动组装进模型提示词；description 决定模型「什么时候选它」，parameters 决定「怎么填」。",
        "execute 返回规范值；render 把规范值转成模型可见内容，两者解耦，同一规范值可以有不同渲染。",
        "参数在进入策略前已被冻结；工具层不要再改写参数，历史、审计与执行必须一致。",
        "高风险工具要配权限门禁或审批，不要只靠 description 里写「请小心」。",
    ],
    task="写一个 <code>word_count</code> 工具：输入文本，返回字符数与词数；测试空串、超长文本、缺参数三种情况，记录错误是否可读。",
    qa=[
        ("规范值和渲染内容有什么区别？", "规范值是 execute 返回、output.schema 声明的结构化值；渲染内容是模型看到的形式。前者用于校验与审计，后者用于展示。"),
        ("模型怎么知道要调用 greet？", "name、description、parameters、output 会自动进入提示词；模型根据这些信息判断是否调用、传什么参数。"),
    ],
    status="ok", impact="工具开发", sev="低", prio="—",
    note="defineTool 字段与行为来自教程；复杂 schema 能力以 <code>@deepseek-ai/dsh-tools</code> 类型为准。")

add(id="s3-6", stage=3, num="3.6", title="插件配置：Config 与 Schemastery", tag="配置", dur="约 30 分钟",
    src="deepseek-harness-plugin-config.html",
    goal="用 Config 接口 + 同名 schema 接收配置，并让非法配置在加载时失败。",
    pre="完成 3.5。",
    points=[
        "导出同名 <code>Config</code> 接口与 Schemastery schema；默认值写在 schema 字段上。",
        "<code>apply(ctx, config)</code> 的第二个参数就是校验后的配置。",
        "必填、枚举、范围等约束在 schema 表达；非法配置会让插件加载失败并给出明确错误。",
        "原则：凡是不同部署可能取不同值的参数，都定义成配置字段，不要硬编码。",
        "配置变更会触发 HMR；重载会清理旧注册，注意别把运行时状态只放在内存。",
    ],
    task="给 greet 加 <code>greeting</code> 与 <code>maxRetries</code> 两个配置：测默认值、cordis.yml 覆盖、非法类型三组，确认错误发生在加载时。",
    qa=[
        ("为什么不能导出普通对象作为 Config？", "Cordis 要求 Standard Schema 接口，普通对象没有校验与默认值能力，加载时不会按预期处理。"),
        ("HMR 会保留插件状态吗？", "不会自动保留。热替换会卸载旧实例、加载新实例；需要延续的状态要外置或显式持久化。"),
    ],
    status="ok", impact="配置", sev="低", prio="—",
    note="Config/schema 约定与 HMR 行为来自教程。")

add(id="s3-7", stage=3, num="3.7", title="生命周期：Fiber 状态机", tag="生命周期", dur="约 35 分钟",
    src="deepseek-harness-lifecycle.html",
    goal="说出 Fiber 的状态流转，并能用状态区分「缺依赖」与「加载失败」。",
    pre="完成 3.4。",
    points=[
        "状态：PENDING → LOADING → ACTIVE → UNLOADING → DISPOSED；初始化异常进入 FAILED。",
        "一个插件模块可以有多个 Fiber：同一插件在不同上下文中加载，各自有独立生命周期。",
        "Fiber 保存校验后的配置、服务依赖与注册资源；卸载时执行清理。",
        "依赖未满足停在 PENDING；配置/初始化错误进入 FAILED，不能都当成缺依赖。",
        "自动重载是新 Fiber，不是恢复旧内存。",
    ],
    task="在插件里打印 <code>ctx.fiber.state</code>。分别制造「缺依赖」与「配置类型错误」，记录两次状态与日志差异。",
    qa=[
        ("PENDING 和 FAILED 怎么区分？", "PENDING 是等待依赖，通常日志安静；FAILED 是初始化或配置校验抛错，会有明确错误。先看错误信息，不要盲目加依赖。"),
        ("卸载时资源按什么顺序清理？", "按注册顺序的逆序撤销；异步 disposer 并发执行，有顺序要求的清理要放进同一个 effect。"),
    ],
    status="ok", impact="生命周期", sev="低", prio="—",
    note="状态机与清理顺序来自教程；Cordis 后续版本可能增加状态。")

add(id="s3-8", stage=3, num="3.8", title="依赖驱动加载与嵌套上下文", tag="依赖", dur="约 30 分钟",
    src="deepseek-harness-nested-reload.html",
    goal="用依赖表达加载顺序，用 ctx.plugin 创建子插件，并验证子插件随父卸载。",
    pre="完成 3.7。",
    points=[
        "加载顺序由服务依赖决定，不需要手写 setTimeout 或启动编排。",
        "服务替换会触发依赖插件自动重载；旧监听、工具、适配器不会残留。",
        "<code>ctx.plugin(child)</code> 创建子 Fiber：继承父上下文，但有独立生命周期。",
        "子插件随父插件卸载；适合按功能分组，不要用它逃避依赖声明。",
        "自动重载防止调用已不存在的服务，也会让旧状态丢失。",
    ],
    task="写一个父插件，在 apply 里 <code>ctx.plugin(child)</code> 注册子插件；子插件注册一个工具。卸载父插件后，确认工具消失、子 Fiber 也 disposed。",
    qa=[
        ("依赖驱动加载解决了什么？", "它把「谁先启动」从人工编排变成声明式依赖：服务就绪才加载，服务消失就卸载，服务回来再重载。"),
        ("子插件能独立卸载吗？", "子 Fiber 有独立生命周期，可以由父上下文管理；父插件卸载时子插件一定被处置。"),
    ],
    status="ok", impact="加载机制", sev="低", prio="—",
    note="依赖驱动与子上下文行为来自教程；重载语义以 Cordis 当前实现为准。")

# ── 阶段 4 ────────────────────────────────────────────────────────────────
add(id="s4-1", stage=4, num="4.1", title="服务与依赖：Service 基类", tag="服务", dur="约 35 分钟",
    src="deepseek-harness-services.html",
    goal="用 Service 基类提供命名服务，让消费方通过 inject 获得完整类型提示。",
    pre="完成 3.7。",
    points=[
        "服务是挂在 ctx 上的命名能力；<code>super(ctx, 'metrics')</code> 把它注册为 <code>ctx.metrics</code>。",
        "消费方声明 <code>inject: ['metrics']</code>，apply 执行时服务已就绪。",
        "用 <code>declare module '@deepseek-ai/cordis'</code> 合并 Context 类型，获得自动补全与编译期检查。",
        "必需依赖用 inject；可选依赖用 <code>ctx.get()</code>，可能返回 undefined。",
        "服务消失时依赖者自动 dispose，服务回来时自动重载。",
    ],
    task="写一个 MetricsService，提供 <code>record(event, value)</code>；再写一个消费插件注入它。分别测「服务存在 / 不存在」两种加载结果。",
    qa=[
        ("服务名由什么决定？", "由 <code>super(ctx, 'metrics')</code> 的第二个参数决定；它同时决定 ctx 上的键与 inject 的名字。"),
        ("类型提示是怎么来的？", "TypeScript 声明合并：在模块声明里给 Context 补上 <code>metrics: MetricsService</code>，编译期就能检查拼写与类型。"),
    ],
    status="ok", impact="服务机制", sev="低", prio="—",
    note="Service 基类与声明合并来自教程；内置服务清单以仓库生成文档为准。")

add(id="s4-2", stage=4, num="4.2", title="服务隔离、scope 与工具过滤", tag="隔离", dur="约 35 分钟",
    src="deepseek-harness-isolation-scope.html",
    goal="用 isolate 让不同插件组看到不同服务实例，并区分 scope、shadowing 与 restriction。",
    pre="完成 4.1。",
    points=[
        "<code>isolate: { shell: true }</code> 配合 group 插件，让不同组各自实例化同一个服务。",
        "scope 按 agent 划分，扁平两层；一个活跃 agent 就是其自身 scope 的 key。",
        "带作用域的注册不会继承给 subagent；父子关系用 lineage 数据表达，不影响可见性。",
        "shadowing：同 scope 内用同名项替换全局工具/片段，其它 agent 仍看到全局版本。",
        "restriction：<code>tools.restrict</code> 让某个 scope 完全看不见某些全局工具，调用也会被拒绝。",
    ],
    task="配两个 group，各自隔离 shell 并设置不同 timeout（5s / 60s）；跑一条会超时的命令，确认两组互不影响。再给一个 scope 加工具 restriction，验证工具不可见。",
    qa=[
        ("isolate 和 scope 是一回事吗？", "不是。isolate 让同一服务按插件组实例化；scope 是按 agent 划分注册与可见性的单位。"),
        ("restriction 与「调用时拒绝」有什么区别？", "restriction 让工具不进入提示词、调用也无法匹配，相当于不存在；调用时拒绝仍会让模型看到工具并尝试。"),
    ],
    status="ok", impact="多 Agent 隔离", sev="中", prio="—",
    note="隔离与 scope 语义来自教程；lineage 字段与 restriction 行为以当前版本为准。")

add(id="s4-3", stage=4, num="4.3", title="事件系统：五种分发模式", tag="事件", dur="约 35 分钟",
    src="deepseek-harness-events.html",
    goal="为通知、决策、初始化、处理链、扇出五类场景选对分发模式，并区分两套事件。",
    pre="完成 3.1。",
    points=[
        "emit 广播、bail 短路、serial 顺序、waterfall 流水线、parallel 并行；每个事件只有一种分发模式。",
        "waterfall 监听器必须调用 <code>next()</code> 委托；不调用就是故意短路，可用于拦截或网关。",
        "<code>ctx.on</code> 注册的监听器随插件卸载自动移除。",
        "Cordis 事件（如 <code>tools/result</code>）是实时分发；<code>turn/*</code>、<code>tool/call</code> 等是持久化会话事件。",
        "观察持久化事件要监听 <code>session/event</code> 并检查 <code>event.type</code>，不要按同名 Cordis 事件监听。",
    ],
    task="写一个 tool-logger：监听 <code>tools/result</code>，打印工具名、参数与结果前 100 字符。再写一个 bail 检查，命中条件时返回拒绝。",
    qa=[
        ("bail 和 serial 的区别？", "bail 是决策：第一个有效返回值胜出并停止；serial 是按顺序执行并等待，遇到有效返回值也会终止。两者都用于「谁先表态谁生效」。"),
        ("turn/start 应该怎么监听？", "它是持久化会话事件，不是 Cordis 事件；监听 <code>session/event</code>，判断 <code>event.type === 'turn/start'</code>。"),
    ],
    status="add", impact="事件语义", sev="低", prio="P2",
    note="教程自己指出官方文档把 waterfall 标为「不 await」，但示例普遍 await；建议补充一段明确的版本差异说明。")

add(id="s4-4", stage=4, num="4.4", title="能力三角色：Definition / Provider / Consumer", tag="架构", dur="约 35 分钟",
    src="deepseek-harness-capability-seams.html",
    goal="用三角色拆一个能力，并解释为什么换 Provider 不需要改 Consumer。",
    pre="完成 4.1。",
    points=[
        "Definition：接口 + Request/Result 类型，例如 <code>dsh-shell</code> 注册 <code>ctx.shell</code>。",
        "Provider：真正实现能力，针对一种运行环境，例如 <code>dsh-bash-local</code>、<code>dsh-bash-sandbox</code>。",
        "Consumer：把能力包装成模型可调用的工具，例如 <code>dsh-tool-bash</code>。",
        "三者可以同包也可以分包；判断标准是这些角色是否需要独立演进或替换。",
        "Provider 与 Consumer 互不依赖，都只依赖 Definition；所以换实现时接口与工具不用动。",
    ],
    task="选 <code>ctx.fs</code> 或 <code>ctx.llm</code>，列出 Definition / Provider / Consumer 对应的包，并画一张依赖箭头图（只允许指向 Definition）。",
    qa=[
        ("为什么单一角色不是 seam？", "seam 是「可替换的完整能力」：只有接口没有实现不能工作，只有实现没有工具模型调不到；三角色合起来才是接缝。"),
        ("换 Provider 要改什么？", "只改配置里加载的 Provider 包；Definition 与 Consumer 保持不变。前提是 Provider 遵守同一个接口。"),
    ],
    status="ok", impact="架构", sev="低", prio="—",
    note="三角色划分与 Bash 示例来自教程；具体包名以当前仓库为准。")

# ── 阶段 5 ────────────────────────────────────────────────────────────────
add(id="s5-1", stage=5, num="5.1", title="实战：写一个可替换的能力", tag="实战", dur="约 50 分钟",
    src="deepseek-harness-build-capability.html",
    goal="按 Definition → Provider → Consumer 实现 myCap，并在 cordis.yml 中组合加载。",
    pre="完成 4.4 与 3.5。",
    points=[
        "Definition：抽象类继承 Service，声明 <code>execute(request)</code> 与 Request/Result 类型。",
        "Provider：继承抽象类实现 execute，通过 <code>ctx.plugin(MyCapLocal)</code> 注册实现。",
        "Consumer：用 <code>defineTool</code> 暴露工具，<code>inject: ['tools', 'myCap']</code>。",
        "组合：cordis.yml 同时加载 Provider 与 Consumer；模型只认识工具名，不认识服务。",
        "数据流：模型 → Consumer → Definition → Provider；换 Provider 时前两层不动。",
    ],
    task="实现一个把输入转大写的 myCap：三个包、一个工具、一次真实调用。然后写第二个 Provider（例如加前缀），只改 cordis.yml 完成替换。",
    qa=[
        ("为什么 Consumer 不直接 import Provider？", "直接依赖实现会让替换 Provider 时被迫改 Consumer；依赖 Definition 才能保持接口稳定。"),
        ("Provider 注册为什么用 ctx.plugin？", "它把实现类作为一个子插件加载，服务注册与清理都纳入 Fiber 生命周期。"),
    ],
    status="ok", impact="能力拆分", sev="低", prio="—",
    note="代码骨架与包结构来自教程；类型导入路径以当前仓库为准。")

add(id="s5-2", stage=5, num="5.2", title="LLM 适配器：接入任意模型", tag="模型", dur="约 45 分钟",
    src="deepseek-harness-llm-adapter.html",
    goal="实现最小 LlmAdapter，把自定义端点接入 dsh，并知道哪些字段不能静默丢弃。",
    pre="完成 4.1；了解流式 API。",
    points=[
        "继承 <code>LlmAdapter</code>，实现 <code>async *stream(options)</code>，逐片产出 StreamChunk。",
        "<code>GenerateOptions</code> 包含 provider、model、messages、system、tools、reasoning、signal 等字段。",
        "用 <code>ctx.llm.registerAdapter(['my-provider'], adapter)</code> 绑定路由。",
        "不支持的字段要抛带稳定 code 的 <code>LlmError</code>，不能静默丢弃，否则模型会拿到残缺结果。",
        "可选覆写 <code>listModels()</code> / <code>resolveModel()</code>，提供模型与 reasoning 元数据。",
    ],
    task="写一个 mock adapter：不调用真实 API，产出固定文本 + usage + finish。注册到 <code>my-provider</code>，在会话里选它并跑一次。再故意不实现 tools 字段，确认会报错而不是静默忽略。",
    qa=[
        ("agent-loop 依赖适配器的什么？", "它只消费提供方无关的流式生成服务与 StreamChunk 协议，不关心底层是哪家 API。"),
        ("为什么要保留 <code>signal</code>？", "取消与资源释放要靠它完全停稳；不传 signal 会让中止后仍有请求或进程残留。"),
    ],
    status="ok", impact="模型接入", sev="中", prio="—",
    note="适配器骨架与字段表来自教程；具体类型以 <code>@deepseek-ai/dsh-llm</code> 为准。")

add(id="s5-3", stage=5, num="5.3", title="StreamChunk 协议与错误处理", tag="协议", dur="约 40 分钟",
    src="deepseek-harness-stream-chunk.html",
    goal="按协议产出分片，并用 LlmError 表达传输与协议故障。",
    pre="完成 5.2。",
    points=[
        "顺序：block-start → delta → block-end → usage → finish；文本与工具调用各走一遍。",
        "index 从 0 递增；text-delta 与 tool-call-delta 都要带所属块 index，块之间不要交叉。",
        "五条硬规则：start/end 成对、index 递增、argumentsDelta 是原始 JSON 增量、usage 在 finish 前、finish 必须最后。",
        "错误用带稳定 code 的 <code>LlmError</code>；每个 HTTP 请求合并 <code>attributionHeaders()</code>，并把 <code>options.signal</code> 传给 fetch。",
        "取消要完全停稳：不能只发 abort 就返回，要等待资源释放。",
    ],
    task="用 <code>exampleChunks</code> 写一个 mock stream，让消费方解析出文本与工具调用；再故意在 finish 后追加一个 chunk，确认消费方报错。",
    qa=[
        ("finish 之后还能发 chunk 吗？", "不能。finish 必须是最后一个分片，之后任何分片都会破坏协议。"),
        ("为什么 usage 必须在 finish 前？", "usage 是本次生成的用量事实，finish 是结束信号；先报告用量再结束，消费方才能完整记账。"),
    ],
    status="ok", impact="协议", sev="中", prio="—",
    note="五条规则与错误处理来自教程；分片字段以 <code>@deepseek-ai/dsh-llm</code> 类型为准。")

add(id="s5-4", stage=5, num="5.4", title="组合包 bundle 与 profile", tag="分发", dur="约 35 分钟",
    src="deepseek-harness-bundle-profile.html",
    goal="区分 bundle 与 profile，并做出一个可安装的组合包。",
    pre="完成 3.2。",
    points=[
        "bundle 是附带配置层的 npm 包，manifest 声明 <code>dsh.bundle.patch</code>，回答「贡献什么」。",
        "profile 是 <code>$DSH_HOME/profiles/&lt;name&gt;</code> 下的启动配置，manifest 声明 <code>dsh.profile.bundles</code>，回答「由哪些 bundle 按什么顺序组成」。",
        "没有东西同时是两者；profile 由 <code>dsh plugin</code> 创建维护，不需要手写。",
        "bundle 的 patch 用包名引用插件，安装后由 Node 模块解析找到；用相对源码路径只适合本地 --patch。",
        "没有 <code>dsh.bundle</code> 声明的包仍然能安装，但只是普通依赖，不激活任何层。",
    ],
    task="做 hello-plugin bundle：package.json 声明 dsh.bundle、cordis.patch.yml 用包名、index.js 导出 apply。装进 demo profile，dump-config 看到 <code># == dsh-hello-plugin</code> 层。",
    qa=[
        ("bundle 与 profile 的 manifest 分别是什么？", "bundle 用 <code>dsh.bundle.patch</code> 声明贡献的 patch 文件；profile 用 <code>dsh.profile.bundles</code> 声明有序的 bundle 列表。"),
        ("为什么 patch 里用包名？", "安装后 pnpm 把包链接到 node_modules，Node 的模块解析能按包名找到代码；源码路径只适用于本地 overlay。"),
    ],
    status="ok", impact="打包", sev="低", prio="—",
    note="manifest 键与目录结构来自教程；字段以当前 dsh CLI 为准。")

add(id="s5-5", stage=5, num="5.5", title="安装插件与配置加载顺序", tag="配置", dur="约 35 分钟",
    src="deepseek-harness-install-load-order.html",
    goal="说清四层配置叠加顺序，并用 dump-config 验证某一层来自哪里。",
    pre="完成 5.4。",
    points=[
        "顺序：profile 的 bundles 列表 → profile 的 cordis.patch.yml → home 级 patch → 每个 <code>--patch</code> overlay。",
        "后应用的层按行胜出；patch 按 id 整行替换整个 config，不是深度合并。",
        "覆盖一行时必须重述该行需要的所有键，否则丢掉未写的键。",
        "<code>dsh plugin --profile demo add/remove</code> 管理依赖与 bundles；<code>--dump-config</code> 打印叠加后的完整配置树。",
        "用户可以在自己的 profile patch 里覆盖你的行，不需要改你的包。",
    ],
    task="把 hello 装进 demo，dump-config 找到层标记；再在 profile patch 里覆盖同一行的某个键，确认整行替换的效果（未写的键丢失）。",
    qa=[
        ("为什么是整行替换而不是深度合并？", "整行替换让「最终生效值」可预测、可审计；深度合并会让某个键来自哪一层变得难以追踪。代价是必须重述所有键。"),
        ("怎么确认配置真的生效？", "用 <code>dsh --profile demo --dump-config</code> 看最终树与层标记，再启动验证实际能力；不要只看安装命令成功。"),
    ],
    status="ok", impact="配置", sev="中", prio="—",
    note="四层顺序与按行替换来自教程；具体输出格式以当前 CLI 为准。")

add(id="s5-6", stage=5, num="5.6", title="发布插件：npm、tarball 与 Git", tag="发布", dur="约 35 分钟",
    src="deepseek-harness-publish.html",
    goal="选对三种分发方式，并避免 Git 安装的构建授权坑。",
    pre="完成 5.4 / 5.5。",
    points=[
        "npm 与 tarball 分发预构建产物，用户安装时不需要构建授权。",
        "Git 安装拉的是源码：作者要提供自包含的 <code>prepare</code>，用户要在 <code>pnpm-workspace.yaml</code> 里 <code>allowBuilds</code> 授权。",
        "构建脚本会在用户机器上执行，且不在 Agent 沙箱内；只给可信源码授权。",
        "Git 安装要锁 commit（<code>github:you/plugin#sha</code>），防止默认分支变化。",
        "发布前核对 <code>files</code>、<code>main</code>、<code>dsh.bundle</code>，确认用户拿到的是可加载的产物。",
    ],
    task="用 <code>pnpm pack</code> 打一个 tarball，在干净 profile 里安装并验证工具可调用；再对比 Git 安装第一次失败的提示，写出授权修复步骤。",
    qa=[
        ("为什么 Git 安装 TypeScript 包会失败？", "Git 拉的是源码，没有任何环节自动运行 build，TypeScript 包没有 lib/ 输出；作者要提供 prepare，用户要允许构建。"),
        ("哪种方式最适合普通用户？", "npm 或 tarball：分发预构建产物，用户零构建授权，安装路径最短。"),
    ],
    status="ok", impact="分发", sev="中", prio="—",
    note="三种方式与 allowBuilds 流程来自教程；pnpm 版本行为以官方文档为准。")

# ── 阶段 6 ────────────────────────────────────────────────────────────────
add(id="s6-1", stage=6, num="6.1", title="工具执行流水线与权限门禁", tag="运行时", dur="约 45 分钟",
    src="deepseek-harness-tool-pipeline.html",
    goal="说出一次工具调用的完整环节，并用 pre-execute / guard 做权限门禁。",
    pre="完成 3.5 与 4.3。",
    points=[
        "顺序：<code>tools/pre-execute</code> → 单调守卫 → <code>tools/execute</code> → <code>tools/post-execute</code> → finalizeContent → <code>tools/result</code>。",
        "pre-execute 返回 allow / deny / ask；参数不可改写，因为历史、审计、UI 与执行必须一致。",
        "guard 只能返回拒绝字符串或 undefined，没有 allow 分支；所以顺序无法把拒绝变回允许。",
        "execute 管超时/重试/指标；post-execute 管结果呈现；result 只观测冻结后的最终结果。",
        "选型记忆：能不能做 → pre；必须拒绝 → guard；怎么做 → execute；怎么呈现 → post。",
    ],
    task="写 permission-gate：命中 <code>fs_write</code> 或参数包含 <code>.env</code> 时 deny，否则 next()。验证被拒绝的调用返回可读错误，而工具主体没有执行。",
    qa=[
        ("guard 为什么没有 allow？", "它是不变式的最终防线，只允许缩减权限；如果能有 allow，后注册的监听器就能推翻前面的拒绝。"),
        ("post-execute 替换内容能当保密手段吗？", "不能。内容替换是展示策略，程序化值仍在；要隐藏必须替换规范值或阻止结果。"),
    ],
    status="ok", impact="权限", sev="高", prio="—",
    note="流水线顺序与决策类型来自教程；钩子 API 以当前 dsh-tools 类型为准。")

add(id="s6-2", stage=6, num="6.2", title="沙箱与审批：失败关闭", tag="安全", dur="约 45 分钟",
    src="deepseek-harness-sandbox-approval.html",
    goal="解释 sandbox 与 approval 的分工，并验证「无后端/无应答者 = 拒绝」。",
    pre="完成 6.1。",
    points=[
        "<code>ctx.sandbox.confine(argv, policy)</code> 包装确切 argv；模式：read-only、workspace-write、danger-full-access。",
        "只有前两种进沙箱；受限执行必然到达 confine，静默无隔离透传永远不合法。",
        "后端报告 enforcement: full / partial；要求绝对边界时，partial 应视为不够。",
        "无可用后端抛 <code>SANDBOX_UNAVAILABLE</code>，属于失败关闭，不是普通任务失败。",
        "approval 结果：allowed-once / rejected / cancelled / unavailable；缺应答者、异常、不合规都算 unavailable，一律拒绝；策略 ask / never。",
    ],
    task="在 read-only 下跑一条写入命令，记录拒绝路径；切到 workspace-write 再试。然后模拟审批无应答者，确认结果是拒绝而不是放行。",
    qa=[
        ("partial enforcement 怎么处理？", "要求绝对边界时按「不够」处理，拒绝执行或向上暴露差异；不能把部分管控当成完整边界。"),
        ("审批超时或异常会放行吗？", "不会。缺失、异常、不合规都产生 unavailable，调用方对 rejected / cancelled / unavailable 一律拒绝。"),
    ],
    status="ok", impact="安全边界", sev="高", prio="—",
    note="沙箱模式、enforcement 与审批结果来自教程；平台差异以官方安全文档为准。")

add(id="s6-3", stage=6, num="6.3", title="会话日志与轮次生命周期", tag="可观测", dur="约 45 分钟",
    src="deepseek-harness-session-turn.html",
    goal="解释「模型可见即已记录」，并从 JSONL 还原一次轮次。",
    pre="完成 5.3。",
    points=[
        "Session 是仅追加的 SessionEvent 日志，seq 单调递增；模型历史从日志派生，不单独存储。",
        "<code>deriveMessages()</code> 投影：user/assistant/tool/result 进入历史；assistant/chunk 与 turn/step 跳过。",
        "事件三域：会话事件（持久事实）、Agent 事件（实时控制）、能力事件（seam 策略）。",
        "turn 包含零个或多个 step；step = 一次模型请求 + 它调用的工具。",
        "空 assistant 消息不进历史，但保留 usage 事件；新增模型可见输入必须新增会话事件。",
    ],
    task="解析一段 JSONL：列出 turn/start、step/start、tool/call、tool/result 与最终 assistant/message；再用 <code>deriveMessages()</code> 的规则解释哪些事件不会进历史。",
    qa=[
        ("为什么历史不单独存？", "单独存储会出现两份真源，回放/分叉/检索容易不一致；从同一份事件日志派生，才能保证可重建。"),
        ("turn/start 与 agent/pre-step 有什么区别？", "turn/start 是持久化会话事件，记录轮次边界；agent/pre-step 是实时 Agent 事件，决定模型看到什么，可以改写或拒绝输入。"),
    ],
    status="ok", impact="可观测性", sev="高", prio="—",
    note="会话事件与投影规则来自教程；事件字段以当前 SessionEvent 类型为准。")

add(id="s6-4", stage=6, num="6.4", title="防御性编程：五个边界模式", tag="工程", dur="约 40 分钟",
    src="deeseek-harness-defensive-patterns.html",
    goal="应用五个防御模式，避免一个边界情况拖垮整个 Agent。",
    pre="完成 3.3 与 6.1。",
    points=[
        "正交结果：timedOut、signal、exitCode 独立上报；进程可能超时后捕获 SIGTERM 并以 0 退出。",
        "dispose 要完全停稳：先移除监听，再发终止信号，等待退出，超时升级 SIGKILL。",
        "凭据擦除：启动子进程前移除匹配 <code>*KEY*</code>、<code>*SECRET*</code>、<code>*TOKEN*</code>、<code>*PASSWORD*</code> 的环境变量。",
        "临时文件放 0700 私有目录，随机文件名，用 <code>wx</code> / <code>0600</code> 独占创建。",
        "回调隔离：一个监听器抛错不能影响主流程或其它监听器；错误要单独捕获与上报。",
    ],
    task="给一个子进程封装加三个独立字段（timedOut / signal / exitCode），写三条断言：超时但 exitCode=0、被信号终止、正常退出。再故意让一个回调抛错，确认主流程继续。",
    qa=[
        ("为什么 exitCode=0 仍可能超时？", "进程可能捕获了终止信号并以 0 退出；只看退出码会把「被强杀但掩盖了」误判为成功。"),
        ("为什么清理要等待退出？", "只发信号就返回会留下孤儿进程；dispose 返回时必须保证进程已退出或被 SIGKILL。"),
    ],
    status="ok", impact="稳定性", sev="高", prio="—",
    note="五个模式与示例来自教程；原文标题拼写为「DeeSeek」，本站更正为 DeepSeek。")

add(id="s6-5", stage=6, num="6.5", title="事故复盘与工程文化", tag="工程", dur="约 35 分钟",
    src="deeseek-harness-postmortem.html",
    goal="用「四问」写一份复盘，并说明为什么 100% 覆盖率仍会漏掉集成 bug。",
    pre="完成 6.4；有项目经验。",
    points=[
        "四问：什么坏了、机制是什么、为什么每道安全网都没拦住、新增了什么防护。",
        "只写同时满足「隐蔽、系统性、重新发现代价高」的 bug；不是所有 bug 都值得复盘。",
        "四个真实案例：default export 丢 inject、<code>!!js</code> 配置误用、验收了替代服务器、Landlock 误分类。",
        "测试分层：单元、覆盖率、真实 API e2e、快照；行覆盖率证明执行过，不证明行为正确。",
        "验证外部世界，不信任 Agent 自述；文档纪律是「一个事实一个家」。",
    ],
    task="选一个你遇到的 bug，按四问写 300 字复盘；至少补一条可执行防护（测试、规则或类型约束），并说明它能拦住哪一类复发。",
    qa=[
        ("为什么 100% 覆盖率仍漏 bug？", "覆盖率只证明行被执行；如果测试都走 mock 或手动挂载，真实入口、真实 Loader、真实浏览器路径可能从未被覆盖。"),
        ("什么 bug 不值得写复盘？", "一次性的笔误、机制显而易见、且没有系统性逃逸原因的；写了也不会改变流程。"),
    ],
    status="ok", impact="工程文化", sev="中", prio="—",
    note="四问、四个案例与测试分层来自教程；原文标题拼写为「DeeSeek」，本站更正。")

# 实操独立于既有审计快照；日期表示文档对照时间，不表示已在真实端点运行。
EXAMPLE_DATE = "2026-11-05"
OFFICIAL = "https://github.com/deepseek-ai/deepseek-harness/blob/master/"
EXAMPLES = {
    "s1-2": dict(
        intro="首次体验采用官方 npm 启动路线。在终端逐行运行；首次运行会下载软件包。Node 版本仍按所选版本的官方要求确认。",
        steps=["先检查 Node 与 npm 是否可用。", "启动后保留终端，按终端显示的地址打开 Web UI；结束时按 Ctrl+C。", "记录实际安装版本；需要复现或部署时显式指定已核实的版本。"],
        blocks=[("终端 · 首次启动", "sh", "node -v\nnpm --version\nnpx @deepseek-ai/dsh web")],
        expected="前两行打印版本号；启动命令输出本地服务地址，默认端口为 3080。打开地址后应看到 Web UI。",
        errors=["找不到 node/npm：先安装符合官方要求的 Node.js，再重新打开终端。", "下载失败：检查终端的网络或 npm registry 配置，记录完整错误。", "地址无法打开：确认启动进程仍在运行，并使用终端实际输出的地址。"],
        source=OFFICIAL + "README.md#run"),
    "s1-4": dict(
        intro="Web UI 启动后，用一条可验证的只读任务检查工作区、模型与工具是否连通。",
        steps=["选择含 README.md 的测试工作区，配置并选择模型。", "将权限设置为只读，然后发送下面的任务。", "打开工具记录，核对读取路径与回答中的依据。"],
        blocks=[("发送给 Agent 的任务", "text", "请读取当前工作区的 README.md，概括项目用途。\n只读，不创建、修改或删除文件。\n请列出实际读取的路径，并给出支持结论的原文片段。\n如果文件不存在，请说明，不要猜测。")],
        expected="回答给出真实路径与可对照的摘要；工具记录包含读取操作。README.md 不存在时应明确报告。",
        errors=["无法发送：先检查工作区和模型是否已选择。", "认证失败：在模型设置中核对凭据。", "回答没有读取记录：追问工具证据，不能只凭自然语言回答判定成功。"],
        source=OFFICIAL + "docs/user/guide/providers.md"),
    "s2-1": dict(
        intro="下面是自定义文本模型的配置示例。先在隔离的测试 profile 中操作；gateway.example 和 your-model-id 都是占位值，必须替换。",
        steps=["从模型设置打开当前 profile 的配置文件，并先备份。", "把示例字段合并到现有 llm-pi-ai 配置；保留已有 providers 与其它字段，不要直接覆盖整份配置。", "让启动 dsh 的进程获得 STUDY_GATEWAY_KEY 环境变量，或通过模型设置保存凭据；密钥不写入示例。", "保存后选中 study-gateway 下的实际模型，发送一条简短文本请求。"],
        blocks=[("cordis.patch.yml · 提供方配置", "yaml", "- id: llm-pi-ai\n  config:\n    providers:\n      study-gateway:\n        api: openai-completions\n        baseURL: https://gateway.example/v1\n        apiKeyEnv: STUDY_GATEWAY_KEY\n        models:\n          - id: your-model-id\n            input: [text]")],
        expected="模型选择器中能选中配置的模型，且一次真实请求成功返回。能保存配置本身不代表连接成功。",
        errors=["MISSING_CREDENTIAL：检查启动进程是否获得环境变量，或重新保存凭据。", "UNKNOWN_MODEL：确认模型 ID 与端点提供的名称完全一致。", "连接或协议错误：替换示例地址，核对网关是否提供 Chat Completions 协议。"],
        source=OFFICIAL + "docs/user/guide/providers.md#image-input"),
    "s3-1": dict(
        intro="从已完成安装和构建的官方源码目录开始。这个插件只输出加载日志，不依赖模型或 API Key。",
        steps=["在源码根目录创建 scratch-plugin/src 目录。", "将下面的完整模块保存为 scratch-plugin/src/study-plugin.ts。", "接着按 3.2 的配置加载它；仅保存文件不会自动加载插件。"],
        blocks=[("scratch-plugin/src/study-plugin.ts", "ts", "export const name = 'study-plugin'\n\nexport function apply() {\n  console.log('[study-plugin] ready')\n}")],
        expected="完成 3.2 的加载后，终端出现 [study-plugin] ready。当前示例没有注册工具，工具列表不增加条目。",
        errors=["没有日志：先检查是否传入 3.2 的 patch 文件。", "模块无法解析：确认文件名与配置中的绝对路径一致。", "只有文件保存成功：继续完成加载步骤，再判断插件是否工作。"],
        source=OFFICIAL + "docs/user/develop/basic/index.md"),
    "s3-2": dict(
        intro="延续 3.1 的 study-plugin.ts。在官方源码根目录执行 pwd，取得实际绝对路径，并替换 YAML 中的 /absolute/path/to/deepseek-harness。",
        steps=["将第一段保存为 scratch-plugin/cordis.yml，替换绝对路径前缀。", "在已构建的源码根目录执行第二段命令。", "查看终端加载日志，再核对 Web UI。"],
        blocks=[("scratch-plugin/cordis.yml", "yaml", "- insert:\n    - id: study-hello\n      name: '/absolute/path/to/deepseek-harness/scratch-plugin/src/study-plugin.ts'"),
                ("终端 · 加载插件", "sh", "pnpm dsh web --patch ./scratch-plugin/cordis.yml")],
        expected="终端输出 [study-plugin] ready，Web UI 能打开；停止该次启动后，插件不会凭此 patch 自动加入其它启动配置。",
        errors=["模块不存在：确认替换了 /absolute/path/to/deepseek-harness，并检查文件确实存在。", "YAML 解析失败：使用空格缩进，不要混入 Tab。", "缺少构建产物：先在官方源码目录完成 pnpm install 和 pnpm run build。"],
        source=OFFICIAL + "docs/user/develop/basic/index.md#register-it-in-cordisyml"),
}

# ── 元数据与审计 ─────────────────────────────────────────────────────────
for i, x in enumerate(L, 1):
    x["index"] = i
    x["url"] = f"stage-{x['stage']}.html#{x['id']}"
    x["source_url"] = BASE + x["src"]

STAGE_LESSONS = {s["n"]: [x for x in L if x["stage"] == s["n"]] for s in STAGES}
TOTAL = len(L)

STATUS_LABEL = {"ok": "仍然成立", "old": "表述过时", "add": "建议补充", "todo": "存疑待核实"}

def esc(s):
    return html.escape(str(s), quote=True)

def example_html(x):
    example = EXAMPLES.get(x["id"])
    if not example:
        return ""
    blocks = []
    for i, (label, language, code) in enumerate(example["blocks"], 1):
        code_id = f'{x["id"]}-code-{i}'
        blocks.append(f'''<div class="code-example">
          <div class="code-head"><span id="{code_id}-label">{esc(label)}</span><button class="copy-btn" type="button" data-copy="{code_id}" aria-label="复制：{esc(label)}" hidden>复制代码</button></div>
          <pre tabindex="0" aria-labelledby="{code_id}-label"><code id="{code_id}" class="language-{language}">{esc(code)}</code></pre>
        </div>''')
    return f'''<section class="block practice" aria-labelledby="{x["id"]}-practice">
          <h3 id="{x["id"]}-practice">跟着做</h3>
          <p>{esc(example["intro"])}</p>
          <ol>{''.join(f'<li>{esc(step)}</li>' for step in example['steps'])}</ol>
          {''.join(blocks)}
          <h4>预期结果</h4><p>{esc(example["expected"])}</p>
          <details class="practice-errors"><summary>没有得到预期结果？</summary><ul>{''.join(f'<li>{esc(error)}</li>' for error in example['errors'])}</ul></details>
          <p class="example-source">文档对照：<time datetime="{EXAMPLE_DATE}">{EXAMPLE_DATE}</time> · <a href="{esc(example["source"])}" target="_blank" rel="noopener">官方示例与说明</a>。示例未在你的环境或真实模型端点运行。</p>
        </section>'''

def lesson_html(x, prev, nxt):
    points = "\n".join(f"<li>{p}</li>" for p in x["points"])
    qa = "\n".join(
        f'<details><summary>{q}</summary><div class="a">{a}</div></details>'
        for q, a in x["qa"]
    )
    if prev:
        prev_html = f'<a class="prev" href="{prev["url"]}"><span class="dir">上一节</span><span class="t">{esc(prev["num"] + " " + prev["title"])}</span></a>'
    else:
        prev_html = '<a class="prev" href="index.html"><span class="dir">起点</span><span class="t">阅读路径</span></a>'
    if nxt:
        next_html = f'<a class="next" href="{nxt["url"]}"><span class="dir">下一节</span><span class="t">{esc(nxt["num"] + " " + nxt["title"])}</span></a>'
    else:
        next_html = '<a class="next" href="audit.html"><span class="dir">完成</span><span class="t">内容审计</span></a>'
    return f'''      <article class="lesson" id="{x["id"]}" tabindex="-1">
        <div class="lesson-head">
          <span class="lesson-no">{x["num"]}</span>
          <h2>{x["title"]}</h2>
        </div>
        <div class="lesson-meta">
          <span>{x["dur"]}</span><span>{x["tag"]}</span>
          <a href="{x["source_url"]}" target="_blank" rel="noopener">原文 ↗</a>
          <a class="status {x["status"]}" href="audit.html#audit-{x["id"]}">{STATUS_LABEL[x["status"]]}</a>
        </div>
        <details class="lesson-audit"{' open' if x['status'] != 'ok' else ''}>
          <summary>审计依据 · <time datetime="{AUDIT_DATE}">{AUDIT_DATE}</time></summary>
          <p>{esc(x["note"])} <a href="audit.html#audit-{x["id"]}">查看本节审计记录</a></p>
        </details>
        <div class="block">
          <div class="label">学习目标</div>
          <p>{x["goal"]}</p>
        </div>
        <div class="block">
          <div class="label">前置知识</div>
          <p>{x["pre"]}</p>
        </div>
        <div class="block">
          <div class="label">核心要点</div>
          <ol>{points}</ol>
        </div>
        <div class="block task">
          <div class="label">动手任务</div>
          <p>{x["task"]}</p>
        </div>
        {example_html(x)}
        <div class="block check">
          <div class="label">自检</div>
          <div class="qa">{qa}</div>
        </div>
        <div class="lesson-foot">
          <button class="done-btn" type="button" data-done-id="{x["id"]}" aria-pressed="false">
            <span class="dot" aria-hidden="true"></span><span class="label-text">标记完成</span>
          </button>
          <span class="note" data-progress-note>进度保存在本机浏览器</span>
        </div>
        <nav class="chapter-nav" aria-label="章节翻页">
          {prev_html}
          {next_html}
        </nav>
      </article>'''

def toc_html(stage):
    items = "\n".join(
        f'<li><a href="#{x["id"]}"><span class="n">{x["num"]}</span><span>{x["title"]}</span></a></li>'
        for x in STAGE_LESSONS[stage]
    )
    return f'''<nav class="toc" aria-label="本阶段目录">
        <h2>本阶段目录</h2>
        <ol>{items}</ol>
        <p class="toc-note">完成一节就点小节底部「标记完成」，进度只存本机。</p>
      </nav>'''

def mobile_toc_html(stage):
    lessons = STAGE_LESSONS[stage]
    items = "\n".join(
        f'<li><a href="#{x["id"]}"><span class="n">{x["num"]}</span> <span>{esc(x["title"])}</span></a></li>'
        for x in lessons
    )
    first = lessons[0]
    return f'''<nav class="mobile-toc" aria-label="本章目录">
    <details>
      <summary><span>本章目录</span><span class="toc-current" data-toc-current>{first["num"]} {esc(first["title"])}</span></summary>
      <ol>{items}</ol>
    </details>
  </nav>'''

def header(active):
    def cur(k):
        return ' aria-current="page"' if active == k else ""
    return f'''<header class="topbar">
  <div class="topbar-in">
    <a class="brand" href="index.html" aria-label="DeepSeek Harness 学习手册首页">
      <span class="brand-mark" aria-hidden="true">H</span>
      <span class="brand-text">DeepSeek Harness<small>学习手册</small></span>
    </a>
    <nav class="topnav" aria-label="主导航">
      <a href="index.html"{cur("index")}>阅读路径</a>
      <a href="contents.html"{cur("contents")}>全部章节</a>
      <a href="search.html"{cur("search")}>搜索</a>
      <a href="audit.html" class="nav-secondary"{cur("audit")}>审计</a>
      <a href="about.html" class="nav-secondary"{cur("about")}>说明</a>
    </nav>
    <div class="mini-progress" title="总进度">
      <span class="mini-bar" aria-hidden="true"><i data-mini-bar></i></span>
      <span data-mini-text>0/{TOTAL}</span>
    </div>
  </div>
</header>'''

def footer():
    return f'''<footer class="footer">
  <div class="wrap">
    <div class="footer-in">
      <div>
        <p>蓝本：<a href="{BASE}deepseek-harness-tutorial.html" target="_blank" rel="noopener">runoob · DeepSeek Harness 教程</a>。本站为学习导读与审计，不复制原文全文；原文版权归原站点所有。</p>
        <p>代码 MIT；本站原创文字 CC BY-NC-SA 4.0（<a href="LICENSE">LICENSE</a> / <a href="LICENSE-CONTENT.md">LICENSE-CONTENT</a>）。审计时间 2026-10，产品处于预览版，信息以官方为准。</p>
      </div>
      <div>
        <h3>阅读</h3>
        <ul>
          <li><a href="index.html">阅读路径</a></li>
          <li><a href="contents.html">全部章节</a></li>
          <li><a href="search.html">全文搜索</a></li>
        </ul>
      </div>
      <div>
        <h3>文档</h3>
        <ul>
          <li><a href="audit.html">内容审计</a></li>
          <li><a href="about.html">来源、许可与维护</a></li>
          <li><a href="../ai-agent/index.html">返回 AI Agent 学习站</a></li>
        </ul>
      </div>
    </div>
    <div class="fine">离线可用 · 无外部请求 · 进度仅保存在本机</div>
  </div>
</footer>'''

def page(title, active, body, script=""):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | DeepSeek Harness 学习手册</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="page-{active or 'lesson'}">
<a class="skip" href="#main">跳到主要内容</a>
<div class="read-progress" aria-hidden="true"></div>
{header(active)}
<div class="storage-notice" data-storage-notice role="status" hidden></div>
{body}
{footer()}
{script}
<script src="assets/app.js"></script>
</body>
</html>'''

# ── 阶段页 ───────────────────────────────────────────────────────────────
for s in STAGES:
    items = STAGE_LESSONS[s["n"]]
    lessons = []
    for x in items:
        i = L.index(x)
        prev = L[i - 1] if i > 0 else None
        nxt = L[i + 1] if i < len(L) - 1 else None
        lessons.append(lesson_html(x, prev, nxt))
    lede = s["lede"]
    meta = f'{len(items)} 节 · 约 {s["hours"]} 小时 · 前置：{"无" if s["n"] == 1 else "阶段 " + str(s["n"] - 1)}'
    prev_href = "index.html" if s["n"] == 1 else f"stage-{s['n']-1}.html"
    prev_label = "阅读路径" if s["n"] == 1 else STAGES[s["n"] - 2]["title"]
    next_href = "audit.html" if s["n"] == len(STAGES) else f"stage-{s['n']+1}.html"
    next_label = "内容审计" if s["n"] == len(STAGES) else STAGES[s["n"]]["title"]
    body = f'''<main id="main">
  <div class="page-head">
    <div class="wrap">
      <div class="crumbs"><a href="index.html">阅读路径</a> / <span>阶段 {s["n"]}</span></div>
      <div class="kicker">Chapter {s["n"]:02d} · {s["en"]}</div>
      <h1>{s["title"]}</h1>
      <p class="lede">{lede}</p>
      <div class="meta-line"><span>{meta}</span><span>每节含目标 / 前置 / 要点 / 任务 / 自检</span></div>
      <div class="stage-progress">
        <span>本阶段进度</span>
        <span class="bar" aria-hidden="true"><i data-stage-bar="{s["n"]}"></i></span>
        <b data-stage-label="{s["n"]}">0 / {len(items)}</b>
      </div>
    </div>
  </div>
  {mobile_toc_html(s["n"])}
  <div class="wrap layout">
    {toc_html(s["n"])}
    <div>
      {"".join(lessons)}
      <nav class="pager" aria-label="阶段翻页">
        <a href="{prev_href}"><span class="dir">上一章</span><span class="t">{prev_label}</span></a>
        <a class="next" href="{next_href}"><span class="dir">下一章</span><span class="t">{next_label}</span></a>
      </nav>
    </div>
  </div>
</main>'''
    (ROOT / f"stage-{s['n']}.html").write_text(page(f"阶段 {s['n']} · {s['title']}", "", body), encoding="utf-8")

# ── 首页 ─────────────────────────────────────────────────────────────────
counts = {k: sum(1 for x in L if x["status"] == k) for k in STATUS_LABEL}
path_rows = "\n".join(
    f'''<a class="path-row" href="stage-{s["n"]}.html">
      <span class="path-no">{s["n"]:02d}</span>
      <span class="path-title">{s["title"]}<span class="sr-only">：{s["lede"]}，约 {s["hours"]} 小时</span></span>
      <span class="path-meta">{len(STAGE_LESSONS[s["n"]])} 节</span>
      <span class="path-arrow" aria-hidden="true">→</span>
    </a>''' for s in STAGES)
resume_json = json.dumps([dict(id=x['id'], num=x['num'], title=x['title'], url=x['url']) for x in L], ensure_ascii=False).replace('<', '\\u003c')
body = f'''<main id="main">
  <section class="cover">
    <div class="wrap cover-grid">
      <div class="cover-intro">
      <h1>从安装到插件，<br>读懂 Agent 的运行方式。</h1>
      <p class="deck">六章，{TOTAL} 节。每节都有目标、动手任务与自检。</p>
      <p class="cover-description">这是一份面向开发者的 DeepSeek Harness 学习手册，系统讲解从环境安装、配置与运行形态，到插件开发、服务与事件、实战与发布，以及面向生产的运行方法，帮助你循序渐进地掌握 Agent 的搭建与实践。</p>
      <div class="cover-actions">
        <a class="btn btn-primary" href="stage-1.html#s1-1" data-resume data-resume-compact aria-describedby="resume-note">开始阅读</a>
        <div class="cover-progress"><span>学习进度</span><div><b data-progress-count>0</b><span> / {TOTAL} 节</span></div></div>
      </div>
      <p class="resume-note sr-only" id="resume-note" data-resume-note>从第 1 节开始，也可以按下方路线选择章节。</p>
      <p class="cover-dates"><a href="audit.html">内容审计：{AUDIT_DATE}</a><span aria-hidden="true">｜</span><a href="about.html">示例与说明：{EXAMPLE_DATE}</a></p>
      <script type="application/json" id="resume-lessons">{resume_json}</script>
      </div>
      <nav class="cover-catalog" aria-labelledby="cover-catalog-title">
        <h2 id="cover-catalog-title">本册目录</h2>
        <div class="path-table">{path_rows}</div>
      </nav>
    </div>
  </section>

  <section class="section routes-section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>按你的目标，选一条路</h2>
        </div>
      </div>
      <div class="reading-routes">
        <div class="route">
          <h3><a href="stage-1.html#s1-2">快速上手 <span aria-hidden="true">→</span></a></h3>
          <p>用最短路径完成安装、配置与基本运行，尽快跑通一个 Agent。</p>
          <details><summary>查看路线</summary>
          <ul>
            <li><a href="stage-1.html#s1-2">1.2 安装</a> → <a href="stage-1.html#s1-4">1.4 Web UI</a></li>
            <li><a href="stage-2.html#s2-1">2.1 模型配置</a> → <a href="stage-2.html#s2-6">2.6 运行模式</a></li>
            <li>产出：一次只读任务 + 一份权限配置</li>
          </ul>
          </details>
        </div>
        <div class="route">
          <h3><a href="stage-3.html#s3-1">插件开发 <span aria-hidden="true">→</span></a></h3>
          <p>从示例进入插件开发，掌握插件结构、接口与调试方法。</p>
          <details><summary>查看路线</summary>
          <ul>
            <li><a href="stage-3.html#s3-1">3.1 第一个插件</a> → <a href="stage-3.html#s3-5">3.5 defineTool</a></li>
            <li><a href="stage-4.html#s4-4">4.4 能力三角色</a> → <a href="stage-5.html#s5-1">5.1 实战</a> → <a href="stage-5.html#s5-6">5.6 发布</a></li>
            <li>产出：一个可安装、可替换 Provider 的能力包</li>
          </ul>
          </details>
        </div>
        <div class="route">
          <h3><a href="stage-6.html#s6-1">生产与安全 <span aria-hidden="true">→</span></a></h3>
          <p>了解服务部署、隔离与事件机制，并关注运行中的安全与稳定性。</p>
          <details><summary>查看路线</summary>
          <ul>
            <li><a href="stage-6.html#s6-1">6.1 工具流水线</a> → <a href="stage-6.html#s6-2">6.2 沙箱与审批</a></li>
            <li><a href="stage-6.html#s6-3">6.3 会话日志</a> → <a href="stage-6.html#s6-4">6.4 防御性编程</a> → <a href="stage-6.html#s6-5">6.5 复盘</a></li>
            <li>产出：一张权限边界表 + 一份失败关闭检查单</li>
          </ul>
          </details>
        </div>
        <div class="route">
          <h3><a href="stage-4.html#s4-3">研究视角 <span aria-hidden="true">→</span></a></h3>
          <p>从原理、设计与扩展性出发，系统理解 Agent 的能力边界与实践方向。</p>
          <details><summary>查看路线</summary>
          <ul>
            <li><a href="stage-4.html#s4-3">4.3 事件系统</a> → <a href="stage-4.html#s4-2">4.2 隔离与 scope</a></li>
            <li><a href="stage-6.html#s6-3">6.3 会话日志</a> → <a href="stage-5.html#s5-4">5.4 bundle/profile</a></li>
            <li>产出：一份可复现的配置树 + 一次回放记录</li>
          </ul>
          </details>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>先看审计，再照抄命令</h2>
          <p>审计覆盖 {TOTAL} 节。整体与当前 0.2.x 预览版一致；具体版本、模型名与 benchmark 需要单独核实。</p>
        </div>
        <a class="btn btn sm" href="audit.html">完整台账</a>
      </div>
      <div class="audit-strip">
        <div class="ok"><b>{counts["ok"]}</b><span>仍然成立</span></div>
        <div class="old"><b>{counts["old"]}</b><span>表述过时</span></div>
        <div class="add"><b>{counts["add"]}</b><span>建议补充</span></div>
        <div class="todo"><b>{counts["todo"]}</b><span>存疑待核实</span></div>
      </div>
      <div class="callout warn" style="margin-top:24px">
        <p><b>最该先核实的三件事：</b>① Node.js 24.9+ 的硬性要求；② 视觉模型名与单图 token 上限；③「2026 年 8 月开源」等时间与 benchmark 数字。</p>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>怎么读这一站</h2>
        </div>
      </div>
      <div class="two-col">
        <div class="panel">
          <h3>每节五件事</h3>
          <p>先看目标和前置，判断要不要学；读要点；必须做动手任务；用自检两问验证；最后标记完成。</p>
          <p class="small muted">完成进度只写入本机 localStorage。</p>
        </div>
        <div class="panel">
          <h3>与原文的关系</h3>
          <p>本站不复制原文全文，只做导读、任务与审计；每节保留原文链接。遇到冲突，以官方文档与原文为准。</p>
          <p class="small muted">原文 34 个条目全部覆盖，0 漏章。</p>
        </div>
      </div>
    </div>
  </section>
</main>'''
(ROOT / "index.html").write_text(page("阅读路径", "index", body), encoding="utf-8")

# ── 全部章节 ─────────────────────────────────────────────────────────────
G1 = [x for x in L if x["stage"] <= 2]
G2 = [x for x in L if x["stage"] >= 3]

def chapter_row(x):
    return f'''<li class="chapter-row" data-lesson="{x["id"]}" data-title="{esc(x["title"])}">
      <span class="idx">{x["index"]:02d}</span>
      <a class="main" href="{x["url"]}">{x["title"]}</a>
      <span class="stage">阶段 {x["stage"]}</span>
      <a class="src" href="{x["source_url"]}" target="_blank" rel="noopener">原文 ↗</a>
      <span class="done-dot" aria-hidden="true"></span>
    </li>'''

body = f'''<main id="main" class="doc">
  <div class="kicker">Catalog · 对照原文左侧栏</div>
  <h1>全部章节</h1>
  <p class="lede">原文左侧栏是 2 个分组、{TOTAL + 1} 个链接（教程首页 + {TOTAL} 章）。本站全部收录，并标出每章在阅读路径中的阶段。</p>
  <div class="callout info">
    <p><b>顺序说明：</b>原文先讲使用与配置，再进入「DeepSeek Harness 开发」；本站按学习递进重排为 6 章，但这一页保留原文分组与顺序。想按学习路径读，用 <a href="index.html">阅读路径</a>。</p>
  </div>
  <div class="catalog-search">
    <label for="catalog-q">筛选章节</label>
    <input id="catalog-q" type="search" placeholder="例如：插件、沙箱、事件、SDK" autocomplete="off">
    <span class="catalog-count" id="catalog-count" aria-live="polite">{TOTAL + 1} 项</span>
  </div>
  <p class="catalog-empty" id="catalog-empty" hidden>没有匹配的章节。试试更短的关键词。</p>
  <div class="catalog">
    <section class="catalog-group" data-group="g1">
      <h2>使用与配置</h2>
      <p class="group-desc">原文首段，共 11 项：教程首页 + 简介、安装、桌面版、使用、模型、SDK、插件、自动化、多模态、模式。</p>
      <ol class="chapter-list">
        <li class="chapter-row">
          <span class="idx">00</span>
          <a class="main" href="index.html">DeepSeek Harness 教程（本站导读）</a>
          <span class="stage">首页</span>
          <a class="src" href="{BASE}deepseek-harness-tutorial.html" target="_blank" rel="noopener">原文 ↗</a>
          <span class="done-dot" aria-hidden="true"></span>
        </li>
        {"".join(chapter_row(x) for x in G1)}
      </ol>
    </section>
    <section class="catalog-group" data-group="g2">
      <h2>DeepSeek Harness 开发</h2>
      <p class="group-desc">原文分组「DeepSeek Harness 开发」，共 {len(G2)} 项：插件基础、服务与事件、实战、发布、运行与复盘。</p>
      <ol class="chapter-list">
        {"".join(chapter_row(x) for x in G2)}
      </ol>
    </section>
  </div>
  <div class="callout">
    <p><b>目录保真度：</b>{TOTAL}/{TOTAL} 章全部收录；原文分组与顺序保留在本页；学习路径另分 6 章。差异只在呈现顺序，不增删主题。</p>
  </div>
  <nav class="pager">
    <a href="index.html"><span class="dir">上一页</span><span class="t">阅读路径</span></a>
    <a class="next" href="search.html"><span class="dir">下一页</span><span class="t">全文搜索</span></a>
  </nav>
</main>'''
(ROOT / "contents.html").write_text(page("全部章节", "contents", body), encoding="utf-8")

# ── 审计 ─────────────────────────────────────────────────────────────────
top3 = [x for x in L if x["status"] != "ok"][:3]
rows = "\n".join(
    f'''<tr id="audit-{x["id"]}">
      <td>{x["index"]}</td>
      <td><a href="{x["source_url"]}" target="_blank" rel="noopener">{x["title"]}</a></td>
      <td><span class="status {x["status"]}">{STATUS_LABEL[x["status"]]}</span></td>
      <td>{x["impact"]}</td><td>{x["sev"]}</td>
      <td><span class="status {'p0' if x['prio']=='P0' else 'p1' if x['prio']=='P1' else 'p2'}">{x["prio"]}</span></td>
      <td>{x["note"]}</td>
    </tr>''' for x in L)

body = f'''<main id="main" class="doc">
  <div class="kicker">Audit Ledger · 2026-10</div>
  <h1>内容审计</h1>
  <p class="lede">对象：runoob DeepSeek Harness 教程的全部 {TOTAL} 个章节。状态、影响范围、严重程度、优先级与依据逐条列出；无法确证的内容标为「存疑待核实」。</p>

  <div class="callout info">
    <p><b>结论：</b>教程整体与当前 0.2.x 预览版一致，没有 P0 级硬错误。主要风险不在「写错」，而在「写的是会变的」：版本要求、模型名、benchmark 与发布时间需要逐条核实。</p>
  </div>

  <div class="audit-strip" style="margin:24px 0">
    <div class="ok"><b>{counts["ok"]}</b><span>仍然成立</span></div>
    <div class="old"><b>{counts["old"]}</b><span>表述过时</span></div>
    <div class="add"><b>{counts["add"]}</b><span>建议补充</span></div>
    <div class="todo"><b>{counts["todo"]}</b><span>存疑待核实</span></div>
  </div>

  <h2><span class="no">01</span>优先处理</h2>
  <div class="table-wrap">
    <table>
      <caption>按「会不会让你照抄出错」排序</caption>
      <thead><tr><th style="width:70px">优先级</th><th>问题</th><th>为什么先处理</th></tr></thead>
      <tbody>
        {''.join(f'<tr><td><span class="status {"p1" if t["prio"]=="P1" else "p2"}">{t["prio"]}</span></td><td><a href="{t["url"]}">{t["num"]} {t["title"]}</a></td><td>{t["note"]}</td></tr>' for t in top3)}
      </tbody>
    </table>
  </div>

  <h2><span class="no">02</span>台账（{TOTAL} 节全覆盖）</h2>
  <p class="small muted">状态口径：仍然成立 / 表述过时 / 建议补充 / 存疑待核实。没有证据的「感觉旧」不写成过时。</p>
  <div class="table-wrap">
    <table>
      <caption>按本站阅读顺序排列；链接指向原文</caption>
      <thead><tr><th style="width:40px">#</th><th style="width:200px">章节</th><th style="width:96px">状态</th><th style="width:100px">影响范围</th><th style="width:60px">严重度</th><th style="width:60px">优先级</th><th>依据 / 说明</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <h2><span class="no">03</span>审计方法与依据</h2>
  <ul>
    <li>抓取原文 34 个页面，提取正文与代码块，逐节核对「安装命令、版本要求、模型名、API 名、统计数字」。</li>
    <li>可独立核对的事实：npm 包 <code>@deepseek-ai/dsh</code> 当前 latest 为 <code>0.2.1-rc.5</code>，license 为 MIT；PyPI 包 <code>deepseek-harness-sdk</code> 为 <code>0.2.1rc2</code>，要求 Python &gt;= 3.10；GitHub 仓库可访问。</li>
    <li>无法独立核对的事实：Node 24.9 硬性要求（npm 元数据未声明 engines）、视觉模型名与 384 token 上限、Opus-4.8 对比与 benchmark 数字、开源月份。</li>
    <li>原文标题里有两处「DeeSeek」拼写错误（第 33、34 章对应的 slug），本站正文已更正，链接仍指向原页。</li>
  </ul>

  <h2><span class="no">04</span>建议的更新顺序</h2>
  <ol>
    <li>1.2 已将 Node 版本要求标为「待核实」，补充 <code>node -v</code> 检查方法；后续仍需核对所选版本的官方安装文档。</li>
    <li>2.5 已在正文展开模型名、token 与对比数字的待核实说明，并标出既有审计日期；补齐官方证据后再更新结论。</li>
    <li>在 4.3 明确 waterfall 的 await 差异：官方文档说「不 await」，示例普遍 await，读代码时以类型签名为准。</li>
  </ol>

  <nav class="pager">
    <a href="index.html"><span class="dir">上一页</span><span class="t">阅读路径</span></a>
    <a class="next" href="about.html"><span class="dir">下一页</span><span class="t">来源、许可与维护</span></a>
  </nav>
</main>'''
(ROOT / "audit.html").write_text(page("内容审计", "audit", body), encoding="utf-8")

# ── 搜索页 ───────────────────────────────────────────────────────────────
body = f'''<main id="main" class="doc">
  <div class="kicker">Search · {TOTAL} 节本地索引</div>
  <h1>全文搜索</h1>
  <p class="lede">搜索标题、学习目标、核心要点、动手任务与自检答案，定位到具体小节和句子。索引在本地生成，不联网、不上传查询。</p>
  <form class="search-box" id="search-form" role="search">
    <label for="search-q">关键词</label>
    <input id="search-q" name="q" type="search" placeholder="例如：插件的 inject、ctx.effect、沙箱、StreamChunk" autocomplete="off" spellcheck="false">
  </form>
  <div class="search-suggests">
    <span>试试：</span>
    <button type="button" data-q="inject">inject</button>
    <button type="button" data-q="ctx.effect">ctx.effect</button>
    <button type="button" data-q="沙箱">沙箱</button>
    <button type="button" data-q="StreamChunk">StreamChunk</button>
    <button type="button" data-q="会话日志">会话日志</button>
    <button type="button" data-q="审批">审批</button>
  </div>
  <div class="search-meta">
    <span id="search-count" aria-live="polite">输入关键词开始</span>
    <span id="search-index-meta" class="muted"></span>
  </div>
  <div class="search-results" id="search-results"></div>
  <div class="search-empty" id="search-empty" hidden>没有匹配结果。试试更短的关键词，或换一个同义词。</div>
  <div class="search-empty" id="search-idle">搜索范围：{TOTAL} 节的标题、目标、要点、任务、自检与实操示例（含代码和排错）；不包含原文全文。想按原文目录查，用 <a href="contents.html">全部章节</a>。</div>
  <noscript><div class="callout warn"><p>搜索需要启用 JavaScript。你仍然可以通过 <a href="contents.html">全部章节</a> 浏览。</p></div></noscript>
  <nav class="pager">
    <a href="contents.html"><span class="dir">上一页</span><span class="t">全部章节</span></a>
    <a class="next" href="audit.html"><span class="dir">下一页</span><span class="t">内容审计</span></a>
  </nav>
</main>'''
(ROOT / "search.html").write_text(page("全文搜索", "search", body, '<script src="assets/search-index.js"></script>'), encoding="utf-8")

# ── 关于 ─────────────────────────────────────────────────────────────────
body = f'''<main id="main" class="doc">
  <div class="kicker">About · Usage · Maintenance</div>
  <h1>说明</h1>
  <p class="lede">这一页写清四件事：本站基于什么假设、怎么打开与维护、设计令牌怎么改、哪些内容必须自行核实。</p>

  <h2 id="open"><span class="no">01</span>打开方式</h2>
  <p>本站是纯静态页面，不需要安装、服务器或联网。保持 <code>index.html</code> 与 <code>assets/</code> 在 <code>deepseek-harness/</code> 目录内同级，双击 <code>index.html</code> 即可。阅读手册可离线进行；安装软件、访问模型端点和打开外部文档需要联网。</p>
  <p>首页会返回上次未完成的小节；该节完成后，推荐按阅读顺序排在最前的未完成小节。阅读位置与完成进度保存在当前浏览器；若存储失败，页面会持续提示「本次进度未保存」。不同浏览器、不同访问地址或直接打开文件时，记录可能不互通。</p>
  <div class="callout warn"><p>如果样式丢失，通常是把 HTML 单独移动了位置；页面引用的是 <code>assets/style.css</code> 相对路径。</p></div>

  <h2 id="assumptions"><span class="no">02</span>假设声明</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th style="width:160px">输入项</th><th style="width:240px">采用的假设</th><th>影响</th></tr></thead>
      <tbody>
        <tr><td>蓝本</td><td>runoob DeepSeek Harness 教程的 34 个条目</td><td>不增删主题；章节顺序按学习路径重排，原文分组保留在「全部章节」</td></tr>
        <tr><td>学习者</td><td>有编程经验、无 dsh 实战经验</td><td>不教 TypeScript 语法；插件 API 从最小示例讲起</td></tr>
        <tr><td>规模与时长</td><td>{TOTAL} 节、6 章、约 15 小时</td><td>每节 20–50 分钟；动手任务控制在可一次完成的范围</td></tr>
        <tr><td>运行环境</td><td>本地现代浏览器，离线优先</td><td>零外部字体/CDN；搜索索引本地加载</td></tr>
        <tr><td>视觉</td><td>编辑式手册：纸白、墨色、黄铜；衬线标题 + 无衬线正文</td><td>首页导读与目录分栏，四条路线并列；正文以留白、细线组织层级</td></tr>
        <tr><td>时效</td><td>审计时间 2026-10，产品处于 0.2.x 预览版</td><td>版本、模型名、benchmark 标「待核实」；以官方为准</td></tr>
      </tbody>
    </table>
  </div>

  <h2 id="tokens"><span class="no">03</span>设计说明</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>令牌</th><th>值</th><th>用途</th><th>对比度</th></tr></thead>
      <tbody>
        <tr><td><code>--ink</code></td><td>#14202B</td><td>正文、标题</td><td>15.8:1（on #FBFAF6）</td></tr>
        <tr><td><code>--muted</code></td><td>#5D6A76</td><td>次要文字</td><td>5.3:1</td></tr>
        <tr><td><code>--brass-deep</code></td><td>#6F5522</td><td>标签、强调文字</td><td>6.7:1</td></tr>
        <tr><td><code>--teal</code></td><td>#0F5A5A</td><td>链接、完成态</td><td>7.6:1</td></tr>
        <tr><td><code>--navy</code></td><td>#0C1722</td><td>封面</td><td>白字 18.1:1</td></tr>
        <tr><td><code>--rule</code></td><td>#D8DDE1</td><td>发丝线</td><td>非文字元素</td></tr>
      </tbody>
    </table>
  </div>
  <h3>版式与动效</h3>
  <ul>
    <li>标题用衬线（宋体 / Noto Serif SC），正文用无衬线；正文 16.5px / 行高 1.8。</li>
    <li>无阴影、2px 圆角、1px 发丝线；层级靠字号、留白与黄铜细线，而不是颜色堆叠。</li>
    <li>动效只有 160ms 的颜色/下划线变化；<code>prefers-reduced-motion</code> 下关闭。</li>
    <li>首页在窄屏按导读、目录、路线依次排列；章节页提供折叠目录，表格在自身区域横向滚动。</li>
  </ul>

  <h2 id="source"><span class="no">04</span>来源、许可与维护</h2>
  <ul>
    <li><b>蓝本：</b><a href="{BASE}deepseek-harness-tutorial.html" target="_blank" rel="noopener">runoob · DeepSeek Harness 教程</a>，版权归原站点/原作者。本站不复制原文全文，只做导读、任务与审计，每节保留原文链接。</li>
    <li><b>许可：</b>代码 MIT；本站原创文字（学习路径、要点、任务、审计、说明）采用 CC BY-NC-SA 4.0。详见 <a href="LICENSE">LICENSE</a> 与 <a href="LICENSE-CONTENT.md">LICENSE-CONTENT.md</a>；原文与第三方内容不在本站授权范围。</li>
    <li><b>生成：</b>页面与搜索索引由 <code>tools/build.py</code> 生成；修改课程数据后重新运行即可。</li>
    <li><b>维护：</b>新增一节需要补五字段、更新 <code>STAGE_LESSONS</code> 与前后篇；搜索索引会随构建自动重建。</li>
  </ul>

  <h2 id="verify"><span class="no">05</span>必须自行核实的清单</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th style="width:210px">内容</th><th>核实什么</th><th style="width:190px">去哪查</th></tr></thead>
      <tbody>
        <tr><td>Node / Python 版本</td><td>Node 24.9+ 是否仍是硬性要求；Python SDK 支持矩阵</td><td>官方安装页、npm/PyPI 元数据</td></tr>
        <tr><td>模型与计费</td><td>视觉模型名、单图 token 上限、benchmark 数字</td><td>DeepSeek 模型页与 API 文档</td></tr>
        <tr><td>插件 API</td><td><code>defineTool</code>、<code>ctx.effect</code>、<code>ctx.llm</code> 的当前签名</td><td>仓库类型定义与官方文档</td></tr>
        <tr><td>沙箱与审批</td><td>enforcement 平台差异、审批结果语义</td><td>官方安全文档</td></tr>
        <tr><td>发布时间</td><td>「2026 年 8 月开源」等时间线</td><td>官方公告 / GitHub Releases</td></tr>
      </tbody>
    </table>
  </div>

  <nav class="pager">
    <a href="audit.html"><span class="dir">上一页</span><span class="t">内容审计</span></a>
    <a class="next" href="index.html"><span class="dir">回到</span><span class="t">阅读路径</span></a>
  </nav>
</main>'''
(ROOT / "about.html").write_text(page("说明", "about", body), encoding="utf-8")

# ── 搜索索引 ─────────────────────────────────────────────────────────────
lessons = []
for x in L:
    sents = [("目标", x["goal"]), ("前置", x["pre"])]
    sents += [("要点", p) for p in x["points"]]
    sents += [("任务", x["task"])]
    for q, a in x["qa"]:
        sents += [("自检", q), ("答案", a)]
    example = EXAMPLES.get(x["id"])
    if example:
        sents += [("实操", example["intro"]), ("预期", example["expected"])]
        sents += [("步骤", step) for step in example["steps"]]
        sents += [("排错", error) for error in example["errors"]]
        sents += [("示例代码", code) for _, _, code in example["blocks"]]
    # 去标签、去重
    clean = []
    seen = set()
    for k, t in sents:
        t = (t if k == "示例代码" else html.unescape(re.sub(r"<[^>]+>", "", t))).strip()
        if t and t not in seen:
            seen.add(t)
            clean.append({"k": k, "t": t})
    lessons.append({"id": x["id"], "stage": x["stage"], "title": x["title"], "url": x["url"], "sentences": clean})

payload = {"generated": datetime.date.today().isoformat(), "count": len(lessons), "lessons": lessons}
(ROOT / "assets/search-index.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "assets/search-index.js").write_text(
    "/* 由 tools/build.py 生成，请勿手改。 */\nwindow.__DSH_INDEX__ = " + json.dumps(payload, ensure_ascii=False) + ";\n",
    encoding="utf-8")

print(f"lessons={len(lessons)} sentences={sum(len(x['sentences']) for x in lessons)}")
print("generated pages:", len(list(ROOT.glob('*.html'))))
