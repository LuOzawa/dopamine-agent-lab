"""5.6：重复动作、JSON 解析失败、轮次与工具预算。"""
import argparse
from lab.config import cli
from lab.models import DemoModel, LiveModel
from lab.agent import run, show


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--scenario", choices=["docs", "loop", "malformed", "bad-json"], default="loop")
    parser.add_argument("--max-turns", type=int, default=6)
    parser.add_argument("--max-calls", type=int, default=8)
    args = parser.parse_args()
    print("mode=" + ("live（真实模型不保证复现指定故障）" if args.live else "offline（确定性故障注入）"))
    model = LiveModel() if args.live else DemoModel(args.scenario)
    show(run("列出文档，读取 setup.md，说明配置方法。", model, ["list_docs", "read_doc"],
             max_turns=args.max_turns, max_calls=args.max_calls, guarded=True))


if __name__ == "__main__":
    cli(main)
