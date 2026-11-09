"""有限轮次的工具循环；只记录动作与观察，不要求模型输出思维链。"""
import json
import time
from .tools import DEFINITIONS, execute


def run(task, model, allowed, max_turns=6, guarded=False, max_calls=8, trace=print):
    if not 1 <= max_turns <= 20 or not 1 <= max_calls <= 40:
        raise ValueError("max_turns 必须为 1–20，max_calls 必须为 1–40。")
    history = [{"role": "user", "content": task}]
    completed, previous, parse_failures, calls, tokens = [], None, 0, 0, 0
    started = time.monotonic()

    def finish(status, turn, answer=""):
        return {"status": status, "turns": turn, "tool_calls": calls,
                "tokens": tokens, "elapsed_ms": round((time.monotonic() - started) * 1000),
                "answer": answer, "completed": completed,
                "unfinished": [] if status == "completed" else [task],
                "next_step": "检查答案与来源。" if status == "completed" else "检查错误记录，缩小任务或修正参数后重跑。"}

    for turn in range(1, max_turns + 1):
        reply = model.respond(history, [DEFINITIONS[n] for n in allowed])
        tokens += reply.usage.total_tokens if reply.usage else 0
        # 完整保留 response.output（含 reasoning 等项目），再添加每个工具的结果。
        history.extend(reply.output)
        if reply.status != "completed":
            return finish("model_incomplete", turn)
        pending = [x for x in reply.output if x.type == "function_call"]
        if not pending:
            return finish("completed" if reply.output_text.strip() else "empty_output", turn, reply.output_text)
        for item in pending:
            if calls >= max_calls:
                return finish("tool_limit", turn)
            try:
                args = json.loads(item.arguments)
                fingerprint = (item.name, json.dumps(args, sort_keys=True, ensure_ascii=False))
            except json.JSONDecodeError:
                fingerprint = None
            if guarded and fingerprint is not None and fingerprint == previous:
                return finish("repeated_action", turn)
            previous = fingerprint
            try:
                result = execute(item.name, item.arguments, allowed)
            except PermissionError:
                return finish("permission_denied", turn)
            calls += 1
            trace(f"turn={turn} tool={item.name} args={item.arguments} result={json.dumps(result, ensure_ascii=False)}")
            history.append({"type": "function_call_output", "call_id": item.call_id,
                            "output": json.dumps(result, ensure_ascii=False)})
            if result["ok"]:
                completed.append(item.name)
            if guarded and result.get("error") == "invalid_json":
                parse_failures += 1
                if parse_failures >= 2:
                    return finish("parse_error", turn)
                history.append({"role": "user", "content": "上次工具参数不是合法 JSON。只允许修正一次，请严格按工具 schema 生成参数。"})
    return finish("turn_limit", max_turns)


def show(result):
    print(f"status={result['status']} turns={result['turns']} tool_calls={result['tool_calls']} tokens={result['tokens']}")
    if result["answer"]:
        print(result["answer"])
    else:
        print("已完成工具：" + (", ".join(result["completed"]) or "无"))
        print("未完成：" + "；".join(result["unfinished"]))
        print("建议下一步：" + result["next_step"])
    # result['elapsed_ms'] 可用于监控；预期输出省略随机器变化的耗时。
