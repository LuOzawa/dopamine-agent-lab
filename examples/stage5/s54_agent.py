"""5.4：文档 Agent，默认演示文件不存在后的修复。"""
import argparse
from lab.config import cli
from lab.models import DemoModel, LiveModel
from lab.agent import run, show


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--max-turns", type=int, default=6)
    args = parser.parse_args()
    print("mode=" + ("live" if args.live else "offline（脚本驱动器，非模型推理）"))
    model = LiveModel() if args.live else DemoModel("missing")
    show(run("读取 missing.md；不存在就列出文档，改读 setup.md，总结环境与密钥设置并标注来源。",
             model, ["list_docs", "read_doc"], max_turns=args.max_turns))


if __name__ == "__main__":
    cli(main)
