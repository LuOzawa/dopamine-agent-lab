#!/usr/bin/env python3
"""将真实源码与已执行输出嵌入第 5 阶段，并生成白名单下载包。
修改 examples/stage5 后运行本脚本，再运行 build_search_index.py。
本脚本不执行示例、不读取 .env、不打包运行缓存。
"""
from pathlib import Path
import html
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'examples' / 'stage5'
LESSONS = [
 dict(n=1, title='最小模型调用', files=['s51_setup.py','lab/config.py','requirements.txt','.env.example'],
      intro='先运行离线命令确认解释器与目录正确，再安装锁定依赖、填写密钥并运行 --live。离线 pong 是固定响应，只有真实模式才能验证模型连接。',
      commands=[('python s51_setup.py','s51')], live='python s51_setup.py --live',
      check='离线输出 mode=offline 和 pong；真实模式输出 SDK 版本、模型名和模型返回文本。真实 API 输出可能有标点差异。',
      errors=[('找不到 python3.11 / py -3.11','安装 Python 3.11，再创建虚拟环境。'),('缺少 OPENAI_API_KEY','编辑本目录 .env；只想离线练习就去掉 --live。'),('No module named openai / dotenv','使用当前解释器执行 python -m pip install -r requirements-lock.txt。'),('401 / 403 / 404 / 429 / 超时','分别检查密钥、权限、模型名称、额度/速率、网络连接；不要反复盲目重试。')]),
 dict(n=2, title='两个工具的完整闭环', files=['s52_tools.py','lab/tools.py','lab/models.py'],
      intro='查看两个工具的 schema、白名单执行器和 Responses 适配器。--invalid 先注入空城市参数，再修复为北京并调用计算器。真实模式同样执行本地工具；天气始终是固定教学数据。共用循环代码见 5.4，下载包已经包含。',
      commands=[('python s52_tools.py --invalid','s52')], live='python s52_tools.py --live',
      check='空城市返回可恢复错误；成功天气值为 22°C，算式结果为 30。离线驱动器在第 4 轮结束；这证明程序闭环可运行，不代表真实模型必然同样修复。',
      errors=[('city 不能为空','修正为北京或上海；其他城市不在教学数据中。'),('算式格式错误 / 除数不能为 0','仅使用数字、括号及 + - * /；禁止 eval 和函数调用。'),('工具不在白名单 / 参数字段多余','工具名、字段名与类型必须匹配 schema。'),('--invalid 与 --live 同时使用','故障注入只用于离线测试，真实调用去掉 --invalid。')]),
 dict(n=3, title='可持久化的 SQLite 记忆', files=['s53_memory.py'],
      intro='默认使用临时内存数据库，演示写入、到期过滤和删除。显式执行 set/list/delete 才使用 .runtime/memory.sqlite3；同一个 id 的新偏好覆盖旧值，只有 --confirmed 的偏好才允许写入。',
      commands=[('python s53_memory.py','s53')], live=None,
      extra='python s53_memory.py set --id language --content "回答用中文" --confirmed\npython s53_memory.py list\npython s53_memory.py delete --id language',
      check='默认演示写入 1 条记录；模拟 31 天后读取为 0 条；删除 1 条后为空。持久命令跨进程仍能读到记录。过期过滤不等于物理删除。',
      errors=[('请添加 --confirmed','先确认这条偏好确实来自用户，再显式确认写入。'),('ttl-days 无效','有效范围为 1–365 天，内容最多 1000 字。'),('database is locked / 无法访问数据库','关闭其他写入进程，检查 .runtime 的目录权限。')]),
 dict(n=4, title='会恢复、会停止的 Agent 循环', files=['s54_agent.py','lab/agent.py'],
      intro='循环核心位于 lab/agent.py，入口在 s54_agent.py。每轮保留完整 response.output，并用 call_id 回传工具结果；记录动作、观察、token 用量与耗时，不要求模型暴露内部思维链。',
      commands=[('python s54_agent.py','s54')], live='python s54_agent.py --live',
      extra='python s54_agent.py --max-turns 1',
      check='missing.md 不存在 → list_docs → read_doc(setup.md) → 完成。离线共 4 轮、3 次工具执行；只给 1 轮预算会返回 turn_limit 及未完成项。',
      errors=[('FileNotFoundError','错误作为工具结果回传，先列目录再修正文件名。'),('permission_denied','文件只能来自 data/docs 内的 Markdown；不能用 ../ 越界。'),('model_incomplete / empty_output','检查输出预算、模型支持情况或服务端状态；不要把空响应当作完成。')]),
 dict(n=5, title='把循环整理成可维护项目', files=['lab/__main__.py','lab/__init__.py'],
      intro='保留同一套循环，不再维护第二份重复实现：lab/__main__.py 管入口，agent.py 管编排，tools.py 管工具，config.py 管配置，models.py 管模型适配。--dry-run 在创建客户端前返回。',
      commands=[('python -m lab --dry-run','s55'),('python -m lab','s55-run')],
      live='python -m lab --live --question "读取 setup.md，说明密钥配置方式。"',
      check='dry-run 只打印静态任务和允许工具，零 API 请求、零工具执行、零文件写入。去掉该参数后执行离线问答；离线驱动器固定读取 setup.md，不理解任意问题。',
      errors=[('No module named lab','先进入 examples/stage5，保持整个 lab 目录完整。'),('自定义问题仍返回 setup.md','这是离线固定演示；需要真实问答时加 --live。'),('换模型后工具调用报错','新模型必须支持 Responses 和 function calling；在 .env 中配置。')]),
 dict(n=6, title='故障注入与预算终止', files=['s56_guardrails.py'],
      intro='复用 5.4 的循环并启用 guarded：连续相同动作在再次执行前停止；JSON 解析错误只允许修正一次；轮次和工具次数都有上限。离线可以确定性重现故障，真实模式不保证出现相同动作。',
      commands=[('python s56_guardrails.py','s56'),('python s56_guardrails.py --scenario malformed','s56-retry'),('python s56_guardrails.py --scenario bad-json','s56-parse'),('python s56_guardrails.py --scenario docs --max-turns 1','s56-budget')],
      live='python s56_guardrails.py --live',
      extra='python s56_guardrails.py --scenario docs --max-calls 1',
      check='loop 在第 2 轮停止，工具仅执行 1 次；malformed 修正一次后完成；bad-json 第 2 次解析错误即停止；预算不足输出已完成工具、未完成任务与下一步。',
      errors=[('repeated_action','连续重复是预期停机信号，先检查观察结果，不要仅增加轮次。'),('parse_error','连续测试中已用完唯一一次格式修复机会，检查 schema 和 JSON。'),('turn_limit / tool_limit','拆小任务或合理调整预算；这不是程序崩溃。'),('tokens=0','离线驱动器没有调用模型；真实模式累计 SDK 返回的 token 用量。')]),
 dict(n=7, title='带引用、可拒答的 RAG', files=['s57_rag.py','data/docs/setup.md','data/docs/learning.md','data/docs/safety.md'],
      intro='随包提供 3 篇教学 Markdown。按段落切分，长段落为 240 字、重叠 40 字；离线版用字符二元组词频向量与原文摘录，--live 改为真实 embedding 和模型生成。二者分别缓存，不能混用结果比较语义能力。',
      commands=[('python s57_rag.py --eval','s57')],
      live='python s57_rag.py --live --question "API 密钥存放在哪里？"\npython s57_rag.py --live --eval',
      extra='python s57_rag.py --question "API 密钥存放在哪里？"\npython s57_rag.py --question "火星最高的山峰叫什么？"',
      check='固定教学集 5/5 通过，包含资料外拒答；首次 index=built，后续 index=cache。真实模式逐次生成结果，需要实际检查，不承诺 5/5。',
      errors=[('资料不足','检查资料、切分和检索分数；默认阈值离线 0.12、真实 0.35，仅为教学起点。'),('引用无效','回答缺少编号或编号越界时程序拒答；有效编号仍需人工核对语义。'),('缓存损坏 / 维度不一致','删除对应 rag-offline.json 或 rag-live.json 后重建，不要删除记忆库。'),('embedding 模型无权限','检查 OPENAI_EMBEDDING_MODEL，默认 text-embedding-3-small；确认账号权限。')]),
]


def code(text, kind='command', label='命令'):
    return f'<pre class="example-code example-{kind}" tabindex="0" role="region" aria-label="{html.escape(label)}"><code>{html.escape(text.rstrip())}</code></pre>'


def link(path, label=None):
    return f'<a href="examples/stage5/{html.escape(path)}">{html.escape(label or path)}</a>'


def setup():
    return '''<div id="stage5-setup" class="example-setup">
<h4>先准备一次，后面七节共用</h4>
<p><a class="btn sm" href="examples/stage5-examples.zip" download>下载完整示例包</a> 或直接使用本站 examples/stage5 目录。请保持 lab、data 与入口脚本同级。</p>
<p><b>验证环境：</b>Python 3.11.15。直接依赖固定为 openai==2.29.0、python-dotenv==1.2.2；SQLite 为标准库。这是复现基线，不是最新版声明。Python 3.12 未在本次环境实测。</p>
<p>所有后续运行命令均在 examples/stage5 内执行；下载 ZIP 后则进入解压出的 stage5 目录。</p>
<h4>macOS / Linux</h4>''' + code('cd examples/stage5\npython3.11 -m venv .venv\nsource .venv/bin/activate\npython --version') + '''
<h4>Windows PowerShell</h4>''' + code('cd examples/stage5\npy -3.11 -m venv .venv\n.\\.venv\\Scripts\\python.exe s51_setup.py') + '''
<p>Windows 不必激活环境；将后文 python 换为 .\\.venv\\Scripts\\python.exe 即可，不需要修改执行策略。</p>
<h4>真实 API 模式才需要这一步</h4>''' + code('python -m pip install -r requirements-lock.txt') + '''
<p>复制 .env.example 为 .env，用编辑器填写 OPENAI_API_KEY；已有 .env 时直接编辑。默认模型为 gpt-5.4-mini-2026-03-17，可改成账号有权限且支持 Responses/工具调用的模型。示例固定官方 API 端点。</p>
<p><b>运行边界：</b>默认离线、无需密钥；--live 会发送任务与示例资料并产生 API 费用。请求超时 30 秒、不自动重试；Agent 默认最多 6 轮、8 次工具执行，单次输出最多 2048 tokens，这不是美元预算。</p>
<p><b>验证状态（2026-10-27）：</b>离线运行与固定依赖下的本地模拟 HTTP 契约测试已通过；真实 API 端到端调用尚未验证。下面预期输出均来自离线实跑，不能作为真实模型表现保证。</p>
<p>文件：''' + ' · '.join(link(p) for p in ['requirements.txt','requirements-lock.txt','.env.example','README.md']) + '''</p>
<p>官方依据：<a href="https://developers.openai.com/api/docs/quickstart" target="_blank" rel="noopener">Responses</a> · <a href="https://developers.openai.com/api/docs/guides/function-calling" target="_blank" rel="noopener">工具调用</a> · <a href="https://developers.openai.com/api/docs/guides/embeddings" target="_blank" rel="noopener">Embedding</a> · <a href="https://developers.openai.com/api/docs/models/gpt-5.4-mini" target="_blank" rel="noopener">模型快照</a> · <a href="https://pypi.org/project/openai/2.29.0/" target="_blank" rel="noopener">SDK 版本</a> · <a href="https://pypi.org/project/python-dotenv/1.2.2/" target="_blank" rel="noopener">dotenv 版本</a></p>
</div>'''


def block(item):
    n=item['n']
    parts=[f'<section class="runnable-example" id="example-s5-{n}" aria-labelledby="example-title-{n}">',
           f'<h3 id="example-title-{n}">可运行实验 · {item["title"]}</h3>', f'<p>{item["intro"]}</p>']
    if n==1:
        parts.append(setup())
    else:
        deps='仅需 Python 标准库，无第三方依赖。' if n==3 else '离线仅需标准库；--live 使用 openai==2.29.0 与 python-dotenv==1.2.2。'
        parts.append(f'<p><b>依赖：</b>{deps} <a href="#stage5-setup">环境与完整包见 5.1</a>。</p>')
    parts.append('<h4>运行命令与预期输出</h4>')
    for command,expected in item['commands']:
        parts.append(code(command))
        parts.append(code((LAB/'expected'/f'{expected}.txt').read_text(), 'output', '离线实跑输出'))
    if item.get('extra'):
        parts.extend(['<h4>再试一个场景</h4>',code(item['extra'])])
    if item['live']:
        parts.extend(['<h4>切换真实 API</h4>',code(item['live']),'<p>先完成 5.1 的依赖安装与密钥配置；真实输出措辞、轮次和分数可能不同。</p>'])
    parts.append(f'<p><b>验收：</b>{item["check"]}</p>')
    parts.append('<h4>常见报错与处理</h4><ul>')
    parts.extend(f'<li><b>{html.escape(error)}：</b>{html.escape(fix)}</li>' for error,fix in item['errors'])
    parts.append('</ul><h4>完整代码与配套文件</h4><p>下面展示实际文件内容；运行时请使用完整目录。下载包包含全部共享模块与测试。</p>')
    for path in item['files']:
        parts.append(f'<details class="example-source"><summary>{html.escape(path)}</summary><p>{link(path,"打开源文件")}</p>')
        parts.append(code((LAB/path).read_text(), 'source-code', path))
        parts.append('</details>')
    parts.append('</section>')
    return '\n'.join(parts)


def main():
    path=ROOT/'stage-5.html'
    source=path.read_text()
    for item in LESSONS:
        n=item['n']; start=f'<!-- STAGE5-EXAMPLE-{n}:START -->'; end=f'<!-- STAGE5-EXAMPLE-{n}:END -->'
        generated=start+'\n'+block(item)+'\n'+end+'\n'
        if start in source:
            source=re.sub(re.escape(start)+r'.*?'+re.escape(end)+r'\n?',lambda _:generated,source,flags=re.S)
        else:
            article=source.index(f'<article class="lesson" id="s5-{n}">')
            anchor=source.index('        <div class="lesson-actions">',article)
            source=source[:anchor]+generated+source[anchor:]
    path.write_text(source)
    allowed=[]
    for p in sorted(LAB.rglob('*')):
        rel=p.relative_to(LAB)
        if p.is_file() and not p.is_symlink() and not any(part in {'.runtime','.venv','__pycache__','.git'} for part in rel.parts):
            if p.suffix in {'.py','.md','.txt'} or p.name in {'.env.example','.gitignore'}:
                allowed.append(p)
    with zipfile.ZipFile(ROOT/'examples'/'stage5-examples.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in allowed:
            archive.write(p,Path('stage5')/p.relative_to(LAB))
    print(f'Updated 7 examples; packaged {len(allowed)} source/data/output files (no .env or runtime files).')


if __name__=='__main__':
    main()
