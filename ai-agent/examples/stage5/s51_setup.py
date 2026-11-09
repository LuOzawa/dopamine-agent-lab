"""5.1：默认离线；--live 验证真实 SDK 调用。"""
import argparse
from lab.config import cli, live_client, model_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        print("mode=offline（固定响应，未调用模型）")
        print("pong")
        return
    from importlib.metadata import version
    with live_client() as client:
        reply = client.responses.create(model=model_name(), input="只回复 pong", store=False, max_output_tokens=2048)
    if reply.status != "completed" or not reply.output_text.strip():
        raise RuntimeError("模型没有返回完整文本；检查输出预算或换用支持 Responses 的可用模型。")
    print(f"mode=live sdk={version('openai')} model={model_name()}")
    print(reply.output_text)


if __name__ == "__main__":
    cli(main)
