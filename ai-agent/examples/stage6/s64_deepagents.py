"""真实 Deep Agents 内置文件工具与 todos；文件仅在图状态中。"""
from scripted_model import ScriptedModel, call
from langchain_core.messages import AIMessage, ToolMessage
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data
from langchain.agents.middleware import TodoListMiddleware

DOCS = {'/docs/plan.md': '课程：先运行离线示例，再接入真实模型。',
        '/docs/security.md': '密钥：放在环境变量中，不写进公开代码。',
        '/docs/testing.md': '测试：同时检查成功、失败和停止条件。'}
SUMMARY = '# 学习摘要\n\n先离线验证，再接入模型；密钥不公开；测试应覆盖失败与停止条件。\n'


def run():
    steps = [call('write_todos', {'todos': [{'content': '读三份资料并写摘要', 'status': 'in_progress'}]}, 1),
             call('read_file', {'file_path': '/docs/missing.md'}, 2),
             call('ls', {'path': '/docs'}, 3)]
    steps += [call('read_file', {'file_path': p}, i) for i, p in enumerate(DOCS, 4)]
    steps += [call('write_file', {'file_path': '/summary.md', 'content': SUMMARY}, 7),
              call('write_todos', {'todos': [{'content': '读三份资料并写摘要', 'status': 'completed'}]}, 8),
              AIMessage(content='摘要已写入状态文件 /summary.md。')]
    agent = create_deep_agent(model=ScriptedModel(steps=steps), backend=StateBackend(),
                             middleware=[TodoListMiddleware()],
                             system_prompt='只读提供的资料，在状态文件中写摘要。')
    return agent.invoke({'messages': [{'role': 'user', 'content': '读取三份资料并写摘要。'}],
                         'files': {p: create_file_data(c) for p, c in DOCS.items()}},
                        {'recursion_limit': 30})


if __name__ == '__main__':
    result = run()
    names = [m.name for m in result['messages'] if isinstance(m, ToolMessage)]
    print('实际工具：' + ' → '.join(names))
    print('待办：' + result['todos'][0]['status'])
    print('状态文件 /summary.md：')
    print(result['files']['/summary.md']['content'])
    print('宿主磁盘未写入；模型响应为固定脚本，缺文件恢复路径为预设。')
