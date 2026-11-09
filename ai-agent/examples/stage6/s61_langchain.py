"""真实 create_agent + 两个本地工具，无密钥运行两个固定问题。"""
import ast
import operator
from scripted_model import ScriptedModel, call
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool


@tool
def weather(city: str) -> str:
    """返回北京或上海的固定教学天气，不是实时天气。"""
    data = {'北京': '22°C 晴', '上海': '25°C 多云'}
    return data.get(city, '错误：仅支持北京或上海')


@tool
def calculate(expression: str) -> str:
    """计算只含数字、括号及加减乘除的算式，不执行任意代码。"""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1e9:
                raise ValueError('数字过大')
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError('仅允许数字和加减乘除')
    try:
        if len(expression) > 100:
            raise ValueError('算式过长')
        return str(visit(ast.parse(expression, mode='eval').body))
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
        return f'错误：{exc}'


def run(city='北京', expression='(2+3)*6'):
    model = ScriptedModel(steps=[call('weather', {'city': city}, 1),
        call('calculate', {'expression': expression}, 2), AIMessage(content='工具执行完成。')])
    agent = create_agent(model=model, tools=[weather, calculate],
                         system_prompt='使用工具核对天气和算式。')
    return agent.invoke({'messages': [{'role': 'user',
        'content': f'{city}天气如何？计算 {expression}。'}]}, {'recursion_limit': 12})


if __name__ == '__main__':
    print('模式：固定模型响应；真实 LangChain 工具循环')
    for city, expr in [('北京', '(2+3)*6'), ('上海', '8/2')]:
        result = run(city, expr)
        print(f'问题：{city}天气；{expr}')
        for m in result['messages']:
            if isinstance(m, ToolMessage):
                print(f'  工具 {m.name}: {m.content}')
        print('  消息类型：' + ' → '.join(m.type for m in result['messages']))
