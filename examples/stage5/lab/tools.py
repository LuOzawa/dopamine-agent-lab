"""工具白名单、参数校验与两个演示工具组。"""
import ast
import json
import math
import operator
from .config import DOCS


def calculate(expression):
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 80:
        raise ValueError("expression 必须是 1–80 字符的算式。")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("算式格式错误，只支持数字、括号和 + - * /。") from exc
    if len(list(ast.walk(tree))) > 40:
        raise ValueError("算式过长，请拆成更小的步骤。")
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in ops:
            value = ops[type(node.op)](visit(node.left), visit(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        else:
            raise ValueError("只允许数字、括号和 + - * /；不执行函数或 Python 代码。")
        if not math.isfinite(value) or abs(value) > 1e12:
            raise ValueError("数值超出演示范围 ±1e12。")
        return value
    try:
        return {"value": visit(tree.body)}
    except ZeroDivisionError as exc:
        raise ValueError("除数不能为 0，请修改算式。") from exc


def get_weather(city):
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city 不能为空；演示城市为北京或上海。")
    data = {"北京": 22, "上海": 25}
    if city not in data:
        raise ValueError("演示数据仅含北京、上海；请换城市。")
    return {"city": city, "temperature_c": data[city], "source": "固定教学数据，非实时天气"}


def list_docs():
    return {"files": sorted(p.name for p in DOCS.glob("*.md") if not p.is_symlink())}


def read_doc(name):
    if not isinstance(name, str) or not name or len(name) > 80:
        raise ValueError("name 必须是文档文件名；先调用 list_docs。")
    target = (DOCS / name).resolve()
    if target.parent != DOCS.resolve() or target.suffix != ".md":
        raise PermissionError("只能读取 data/docs 内的 Markdown，禁止目录穿越。")
    if not target.is_file():
        raise FileNotFoundError("文档不存在；调用 list_docs 查找正确文件名。")
    if target.stat().st_size > 12000:
        raise ValueError("文档超过 12 KB；请拆分后再读。")
    return {"source": name, "text": target.read_text(encoding="utf-8")}


def definition(name, description, properties):
    return {"type": "function", "name": name, "description": description,
            "strict": True, "parameters": {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}}


DEFINITIONS = {
    "get_weather": definition("get_weather", "读取北京/上海的固定教学天气，非实时数据。", {"city": {"type": "string"}}),
    "calculate": definition("calculate", "计算仅含数字和 + - * / 的算式。", {"expression": {"type": "string"}}),
    "list_docs": definition("list_docs", "列出可读取的教学文档。", {}),
    "read_doc": definition("read_doc", "读取教学文档；文件不存在时先 list_docs。", {"name": {"type": "string"}}),
}
FUNCTIONS = {"get_weather": get_weather, "calculate": calculate, "list_docs": list_docs, "read_doc": read_doc}


def execute(name, arguments, allowed):
    if name not in allowed:
        raise PermissionError("工具不在本轮白名单中。")
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json", "message": "参数必须是合法 JSON 对象，请修正后重试。"}
    props = DEFINITIONS[name]["parameters"]["properties"]
    if not isinstance(args, dict) or set(args) != set(props) or any(not isinstance(v, str) for v in args.values()):
        return {"ok": False, "error": "invalid_arguments", "message": "字段必须严格匹配工具 schema，参数值必须是字符串。"}
    try:
        return {"ok": True, "data": FUNCTIONS[name](**args)}
    except (ValueError, FileNotFoundError) as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}
