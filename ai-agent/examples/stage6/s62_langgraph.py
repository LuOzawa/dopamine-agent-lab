"""真实 StateGraph：有界重试、拒答、checkpoint 暂停后恢复。"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    question: str
    attempts: int
    docs: list[str]
    sufficient: bool
    answer: str


def build_graph(pause=False):
    def retrieve(s):
        # 第一次故意未命中，用于确定性验证 retry 分支。
        n = s['attempts'] + 1
        docs = ['密钥放在 .env，不提交到版本库。'] if n == 2 and '密钥' in s['question'] else []
        return {'attempts': n, 'docs': docs}
    def grade(s):
        return {'sufficient': bool(s['docs'])}
    def retry(s):
        return {'answer': ''}
    def answer(s):
        return {'answer': s['docs'][0] if s['sufficient'] else '资料不足，停止检索。'}
    graph = StateGraph(State)
    for name, fn in [('retrieve', retrieve), ('grade', grade), ('retry', retry), ('answer', answer)]:
        graph.add_node(name, fn)
    graph.add_edge(START, 'retrieve')
    graph.add_edge('retrieve', 'grade')
    graph.add_conditional_edges('grade', lambda s:
        'answer' if s['sufficient'] or s['attempts'] >= 2 else 'retry')
    graph.add_edge('retry', 'retrieve')
    graph.add_edge('answer', END)
    return graph.compile(checkpointer=InMemorySaver(), interrupt_before=['answer'] if pause else [])


def initial(question):
    return {'question': question, 'attempts': 0, 'docs': [], 'sufficient': False, 'answer': ''}


def demo():
    graph = build_graph(pause=True)
    for i, question in enumerate(['密钥放哪里？', '火星天气如何？']):
        config = {'configurable': {'thread_id': f'lesson-{i}'}, 'recursion_limit': 16}
        graph.invoke(initial(question), config)
        saved = graph.get_state(config)
        print(f'暂停：next={saved.next[0]}；检索={saved.values["attempts"]} 次')
        result = graph.invoke(None, config)
        print(f'恢复：{result["answer"]}')
    print('存储：进程内 InMemorySaver；退出进程后不保留')


if __name__ == '__main__':
    demo()
