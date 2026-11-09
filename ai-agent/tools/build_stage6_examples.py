#!/usr/bin/env python3
"""把第 6 阶段真实文件和实跑输出嵌入 HTML，生成可下载的独立包。"""
from pathlib import Path
import html
import re
import zipfile
from build_stage5_examples import code

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'examples/stage6'
FW='.venv-frameworks/bin/python'
CREW='.venv-crew/bin/python'
GRAPH='.venv-graph/bin/python'
LESSONS=[
 dict(n=1,title='真实 create_agent 工具闭环',env='frameworks',command=f'{FW} s61_langchain.py',
 intro='固定模型响应替代在线推理，LangChain 仍真正执行 weather 与 calculate。两个问题分别覆盖北京/上海天气和不同算式；天气是教学数据。完整消息中可核对 AI tool_call id 与 ToolMessage.tool_call_id。',
 files=['s61_langchain.py','scripted_model.py','requirements/frameworks.txt'],
 check='每个问题都有 human → ai → tool → ai → tool → ai；北京算式得到 30，上海算式得到 4.0。修改问题需同步修改固定响应，不能用它评价真实模型理解能力。',
 errors=[('No module named langchain_core','先安装 frameworks-lock.txt，并使用 .venv-frameworks 的解释器。'),('create_tool_calling_agent / AgentExecutor 导入失败','此例固定 LangChain 1.4.7，使用 create_agent，不混用旧教程。'),('固定响应耗尽 / GraphRecursionError','核对工具名和调用参数；本例设置递归上限 12，不无限重试。'),('错误：仅允许数字和加减乘除','计算器拒绝函数调用和幂运算，除零也返回错误。')],
 source='https://docs.langchain.com/oss/python/langchain/agents'),
 dict(n=2,title='checkpoint 恢复与有界检索',env='frameworks',command=f'{FW} s62_langgraph.py',
 intro='真实 StateGraph 包含 retrieve、grade、retry、answer 四个节点。第一次检索故意为空，第二次根据固定规则命中或拒答；这验证分支与预算，不模拟语义检索。InMemorySaver 暂停在 answer 前，以同一 thread_id 恢复。',
 files=['s62_langgraph.py'],check='两个问题都检索 2 次；密钥问题返回资料，火星问题拒答。不同 thread_id 的 checkpoint 隔离；退出进程后内存 checkpoint 消失。',
 errors=[('缺少 thread_id','每次 invoke/get_state 都传 configurable.thread_id。'),('恢复后没有结果','恢复用 graph.invoke(None, 原 config)，不要重新传 initial 状态覆盖本次流程。'),('GraphRecursionError','检查 grade 是否在 attempts >= 2 时路由 answer；示例 recursion_limit 为 16。')],
 source='https://docs.langchain.com/oss/python/langgraph/persistence'),
 dict(n=3,title='三角色顺序交接与对照',env='crew',command=f'{CREW} s63_crewai.py',
 intro='实际创建 Crew、Agent、Task，按 researcher → writer → editor 顺序运行，Task.context 传递上游结果。固定草稿故意含无依据承诺，固定编辑稿删除承诺；再运行无编辑版本，查看差异。',
 files=['s63_crewai.py','requirements/crew.txt'],extra=f'{CREW} s63_crewai.py --timings',
 check='各角色调用固定模型 1 次；编辑收到完整草稿；最终介绍约 300 字。--timings 输出各角色结果与本机耗时，数值不固定。该实验不能推出多角色必然比单 Agent 写得好。',
 errors=[('PermissionError：用户配置目录','CrewAI 导入时会初始化配置/凭据目录，检查当前用户权限；任务缓存放在本例 .runtime/crew。'),('近似 token count / DeprecationWarning','这是当前框架的计数与内部弃用提示；离线模型没有 API token 费用。'),('角色未收到上文','检查 Task.context 指向之前的任务，使用 Process.sequential。')],
 source='https://docs.crewai.com/v1.15.30/en/learn/custom-llm'),
 dict(n=4,title='内置文件工具、待办与缺文件恢复',env='frameworks',command=f'{FW} s64_deepagents.py',
 intro='Deep Agents 真正调用内置文件工具；预设路径先读 missing.md，再 ls 找到三份资料，读取后写摘要。0.7.32 显式加入 TodoListMiddleware 才提供 write_todos。StateBackend() 的文件位于图状态，不写入电脑磁盘。',
 files=['s64_deepagents.py'],check='执行 8 次工具，missing.md 返回 not found，/summary.md 写入成功，待办状态 completed。固定恢复路线不代表模型自主规划；未调用 shell 或子 Agent。',
 errors=[('write_todos is not a valid tool','保留 middleware=[TodoListMiddleware()]，不要依赖旧版本默认行为。'),('File not found','missing.md 是故意注入；检查下一步 ls 与后续三个真实路径。'),('摘要逐字换行','此版本 FileData.content 是字符串，直接打印，不能按旧版列表 join。'),('重启后文件消失','StateBackend 只在图状态内；持久化需另选后端。')],
 source='https://docs.langchain.com/oss/python/deepagents/backends'),
 dict(n=5,title='Dify Chatflow 客户端与三问验收',env='stdlib',command='python3.11 s65_dify.py',
 intro='先回放三个 API v1 契约样本，验证响应、引用和拒答处理。配套 DIFY.md 给出五条 FAQ、Start → 检索 → LLM → Answer 的绑定及发布步骤。Dify Cloud 持续更新，没有可锁定的云端版本；本次未部署在线 Chatflow。',
 files=['s65_dify.py','data/faq.md','data/dify-cases.json','DIFY.md'],
 extra='python3.11 s65_dify.py --live --query "进度如何保存，换设备后还能继续吗？"',
 check='离线回放显示单段回答、跨段综合和资料外拒答。真实模式先按 DIFY.md 设置 DIFY_API_KEY / DIFY_BASE_URL；在线需核对引用命中 FAQ 2、3，而非仅检查响应是否有 answer。',
 errors=[('缺少 DIFY_API_KEY','从已发布 Chatflow 的 API Access 获取应用密钥，设为环境变量；脚本不自动读取 .env。'),('HTTP 401 / 404 / 400','检查应用密钥、含 /v1 的 API 地址、应用类型及 inputs 必填变量。'),('HTTP 429 / 超时','检查额度、服务状态与网络；客户端超时 30 秒、不自动重试。'),('返回空来源 / 无关问题不拒答','检查知识库索引、检索 result 绑定、上下文提示与引用设置。')],
 source='https://docs.dify.ai/en/api-reference/chat-messages/send-chat-message'),
 dict(n=6,title='真实 n8n 引擎的 JSON 兜底',env='docker',command='python3.11 s66_n8n.py',
 intro='在 n8n 2.44.7 的断网临时容器里执行 Manual Trigger → 固定模型输出 → Validate → IF → 成功或兜底。包含合法 JSON、损坏 JSON、缺字段三条输入。另附可导入的 Webhook → 模型 HTTP 请求 → 同一验证逻辑 → 回应工作流。',
 files=['s66_n8n.py','n8n/validate.js','n8n/offline.json','n8n/webhook.json','N8N.md'],
 check='真实 n8n 执行的三条输入分别进入 success、fallback、fallback。只读挂载资料，退出/超时后清理本次容器；没有向外发送通知。在线 workflow 尚需绑定凭据并完成 webhook 端到端验收。',
 errors=[('Cannot connect to Docker daemon','先启动 Docker Desktop，再 pull 固定镜像。'),('Mounts denied / timeout','允许 Docker 访问解压目录，检查资源；启动器最长等待 120 秒。'),('Python task runner missing','此例只使用 JS Code 节点；验证 JS Task Runner 正常注册。'),('Webhook 404 / 模型 401','按 N8N.md 开启测试监听或发布，绑定 Header Auth；不把密钥写入工作流 JSON。')],
 source='https://docs.n8n.io/hosting/cli-commands/'),
 dict(n=7,title='GraphRAG 项目准备与真实查询清单',env='graph',command=f'{GRAPH} s67_graphrag.py',
 intro='用 GraphRAG 3.3.0 官方 CLI 实际执行 init 与 index --dry-run --skip-validation，复制五篇相关教学短文。此模式不调用模型、不生成实体和社区报告；真实索引与查询命令、两道全局/两道局部问题及答案检查点见 GRAPHRAG.md。',
 files=['s67_graphrag.py','requirements/graph.txt','GRAPHRAG.md']+[f'data/articles/{name}' for name in ['01_overview.txt','02_course.txt','03_platform.txt','04_review.txt','05_release.txt']],
 extra=f'{GRAPH} s67_graphrag.py --prepare .runtime/graphrag\n# 用编辑器填写新项目 .env 的 GRAPHRAG_API_KEY 后：\n.venv-graph/bin/graphrag index --root .runtime/graphrag\n.venv-graph/bin/graphrag query --root .runtime/graphrag --method global --query "团队如何分工保障发布质量？"\n.venv-graph/bin/graphrag query --root .runtime/graphrag --method local --query "李明负责什么，并与谁协作？"\n.venv-graph/bin/graphrag query --root .runtime/graphrag --method basic --query "团队如何分工保障发布质量？"',
 check='离线 CLI 配置检查通过；不等于模型连接成功。真实实验逐题记录引用、漏项、耗时与 token；basic 提供同语料向量查询基线，但共用图索引的总成本不能算作普通 RAG 独立索引成本。',
 errors=[('目标已存在','prepare 拒绝覆盖已有项目；指定新目录或继续使用原项目。'),('旧版 models 配置报错','3.3.0 使用 completion_models / embedding_models；用本版本 init 生成。'),('缺少实体/社区报告文件','先完成真实 index；dry-run 不生成这些文件。'),('401 / 404 / 429','核对密钥、模型权限与额度；离线检查无法验证这些。')],
 source='https://microsoft.github.io/graphrag/cli/'),
]


def link(path,label=None):
    return f'<a href="examples/stage6/{html.escape(path)}">{html.escape(label or path)}</a>'


def setup():
    return '''<div id="stage6-setup" class="example-setup"><h4>先选环境，再运行对应课程</h4>
<p><a class="btn sm" href="examples/stage6-examples.zip" download>下载第 6 阶段完整示例包</a> · '''+link('README.md','完整安装说明')+' · '+link('VALIDATION.md','验证记录')+'''</p>
<p>全部命令先进入 examples/stage6；ZIP 则进入解压后的 stage6。实测 Python 3.11.15 / macOS Apple Silicon。框架、CrewAI、GraphRAG 分别使用三个虚拟环境，避免混用依赖；只安装当前课程需要的环境。页面中的版本是复现基线，不是最新版承诺。</p>
<p>Windows：创建环境时将 python3.11 换成 py -3.11；执行时将 .venv-名称/bin/python 换成 .\\.venv-名称\\Scripts\\python.exe；graphrag 同理换为 Scripts\\graphrag.exe。无需激活环境。Windows/Linux 未在本次环境实测。</p>
<p><b>验证范围：</b>7 个入口已实跑、15 项行为与契约测试通过；n8n 运行真实断网工作流。Dify 回放仅验证客户端，GraphRAG dry-run 仅验证配置；真实模型调用、平台发布和索引质量没有标为已验证。离线固定响应不能作为模型表现保证。</p></div>'''


def environment(item):
    env=item['env']
    versions={'frameworks':'langchain==1.4.7、langgraph==1.2.18、deepagents==0.7.32、langchain-openai==1.7.3',
              'crew':'crewai==1.15.30','graph':'graphrag==3.3.0'}
    if env in versions:
        parts=[f'<p><b>依赖：</b>{versions[env]}。完整传递依赖：{link("requirements/"+env+"-lock.txt")}。</p>']
        if item['n'] in [1,3,7]:
            parts.append(code(f'python3.11 -m venv .venv-{env}\n.venv-{env}/bin/python -m pip install -r requirements/{env}-lock.txt'))
        else:
            parts.append('<p>沿用 6.1 的 .venv-frameworks 环境。'+link('scripted_model.py','共享固定模型模块')+' 已包含在完整包中。</p>')
        return '\n'.join(parts)
    if env=='docker':
        return '<p><b>依赖：</b>Python 3.11 标准库、Docker、n8n==2.44.7。先启动 Docker，再下载镜像：</p>'+code('docker pull docker.n8n.io/n8nio/n8n:2.44.7')
    return '<p><b>依赖：</b>Python 3.11 标准库，无 pip 包；Dify API v1。在线配置见 '+link('DIFY.md')+'。</p>'


def block(item):
    n=item['n']
    parts=[f'<section class="runnable-example" id="example-s6-{n}" aria-labelledby="example-title-{n}">',f'<h3 id="example-title-{n}">可运行实验 · {item["title"]}</h3>',f'<p>{item["intro"]}</p>']
    parts.append(setup() if n==1 else '<p><a href="#stage6-setup">环境、下载包与验证范围见 6.1</a>。</p>')
    parts.append(environment(item))
    parts.extend(['<h4>运行命令与预期输出</h4>',code(item['command']),code((LAB/'expected'/f's6{n}.txt').read_text(),'output','离线实跑标准输出')])
    if item.get('extra'): parts.extend(['<h4>进一步练习</h4>',code(item['extra'])])
    parts.append(f'<p><b>验收：</b>{item["check"]}</p>')
    parts.append('<h4>常见报错与处理</h4><ul>')
    parts.extend(f'<li><b>{html.escape(a)}：</b>{html.escape(b)}</li>' for a,b in item['errors'])
    parts.append('</ul><p>接口依据：<a href="'+item['source']+'" target="_blank" rel="noopener">官方文档</a>；具体行为以本例固定版本实测为准。</p>')
    parts.append('<h4>完整代码与配套文件</h4><p>下列内容来自实际文件；运行时使用完整下载包，保留共享模块、资料与工作流目录。</p>')
    for p in item['files']:
        parts.extend([f'<details class="example-source"><summary>{html.escape(p)}</summary><p>{link(p,"打开文件")}</p>',code((LAB/p).read_text(),'source-code',p),'</details>'])
    parts.append('</section>')
    return '\n'.join(parts)


def main():
    path=ROOT/'stage-6.html'; source=path.read_text()
    for item in LESSONS:
        n=item['n']; start=f'<!-- STAGE6-EXAMPLE-{n}:START -->'; end=f'<!-- STAGE6-EXAMPLE-{n}:END -->'
        generated=start+'\n'+block(item)+'\n'+end+'\n'
        if start in source:
            source=re.sub(re.escape(start)+r'.*?'+re.escape(end)+r'\n?',lambda _:generated,source,flags=re.S)
        else:
            article=source.index(f'<article class="lesson" id="s6-{n}">')
            anchor=source.index('        <div class="lesson-actions">',article)
            source=source[:anchor]+generated+source[anchor:]
    path.write_text(source)
    files=[]
    for p in sorted(LAB.rglob('*')):
        rel=p.relative_to(LAB)
        if not p.is_file() or p.is_symlink() or any(x.startswith('.venv') or x in {'.runtime','__pycache__','.git'} for x in rel.parts): continue
        if p.suffix in {'.py','.md','.txt','.json','.js'} or p.name=='.gitignore': files.append(p)
    with zipfile.ZipFile(ROOT/'examples/stage6-examples.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in files: archive.write(p,Path('stage6')/p.relative_to(LAB))
    print(f'Updated 7 examples; packaged {len(files)} files, excluding secrets/runtime.')


if __name__=='__main__': main()
