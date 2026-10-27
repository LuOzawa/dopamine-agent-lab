"""三个实际 CrewAI 角色，固定模型输出；不衡量真实写作质量。"""
import os
import argparse
from pathlib import Path
os.environ['CREWAI_STORAGE_DIR'] = str(Path(__file__).resolve().parent / '.runtime' / 'crew')
os.environ['OTEL_SDK_DISABLED'] = 'true'
os.environ['CREWAI_TELEMETRY_DISABLED'] = 'true'
os.environ['CREWAI_TRACING_ENABLED'] = 'false'

from crewai import Agent, Task, Crew, Process, BaseLLM

FACTS = '事实：学习站提供分阶段课程、本地进度、搜索与可下载实验。进度仅保存在当前浏览器。'
DRAFT = '这款学习站帮助初学者练习 Agent，并保证每个人都能在一天内精通所有框架。'
FINAL = ('这是一款面向 Agent 初学者的分阶段学习站。你可以从模型调用开始，逐步练习工具调用、'
         '状态保存、任务编排与知识检索，再根据项目需要选择框架。每节课程包含目标、动手任务与验收标准。'
         '配套示例提供固定依赖、运行命令和预期输出，方便对照自己的执行结果。遇到错误时，可以先检查'
         '常见报错，再缩小问题范围。搜索入口帮助定位概念，移动端目录方便切换课程，继续学习入口可以'
         '回到尚未完成的内容。学习进度保存在当前浏览器，不会自动同步到其他设备。建议先运行无需密钥的'
         '实验，确认程序流程，再按课程说明接入真实模型。示例中的固定响应用于验证编排逻辑，不能证明模型'
         '质量，也不保证学习时长。完成练习后，请用自己的问题复测，并记录失败场景。')


class RoleModel(BaseLLM):
    def __init__(self, output):
        super().__init__(model='offline-script', temperature=0)
        self.output = output
        self.calls = 0
        self.seen = []
        self.task_seconds = 0.0

    def call(self, messages, tools=None, callbacks=None, available_functions=None, **kwargs):
        self.calls += 1
        self.seen.append(str(messages))
        return 'Final Answer: ' + self.output

    def supports_function_calling(self):
        return False


def run(with_editor=True):
    agents, tasks, models = [], [], []
    roles = [('researcher', '整理可核对事实', FACTS), ('writer', '写约 300 字介绍', DRAFT)]
    if with_editor:
        roles.append(('editor', '删除无依据承诺，输出约 300 字介绍', FINAL))
    for role, goal, output in roles:
        model = RoleModel(output)
        agent = Agent(role=role, goal=goal, backstory='只处理学习站产品资料。',
                      llm=model, allow_delegation=False, max_iter=2, verbose=False)
        task = Task(description=goal, expected_output=goal, agent=agent, context=list(tasks))
        agents.append(agent); tasks.append(task); models.append(model)
    crew = Crew(agents=agents, tasks=tasks, process=Process.sequential,
                memory=False, cache=False, verbose=False, tracing=False)
    result = crew.kickoff()
    for task, model in zip(tasks, models):
        model.task_seconds = task.execution_duration or 0.0
    return result, models


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--timings', action='store_true')
    args = parser.parse_args()
    result, models = run()
    print('角色：' + ' → '.join(t.agent for t in result.tasks_output))
    print('各角色模型调用数：' + ', '.join(str(m.calls) for m in models))
    print('编辑收到草稿：' + str(DRAFT in models[-1].seen[0]))
    if args.timings:
        for output, model in zip(result.tasks_output, models):
            print(f'{output.agent}：{model.task_seconds:.3f}s；输出：{output.raw}')
    print('最终介绍：' + result.raw)
    without, _ = run(False)
    print('去掉编辑后仍有无依据承诺：' + str('保证' in without.raw))
    print('注意：这是固定对照样本；实际耗时与质量需使用真实模型另行测量。')
