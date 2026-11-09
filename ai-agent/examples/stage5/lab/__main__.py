"""5.5：python -m lab；入口、编排、工具与配置分别维护。"""
import argparse
from .config import cli
from .models import DemoModel, LiveModel
from .agent import run, show


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--question", default="列出文档并读取 setup.md，说明 Python 环境和密钥的配置方法。")
    args = parser.parse_args()
    if args.dry_run:
        print("DRY RUN：不调用模型、不执行工具、不写入文件。")
        print("任务：" + args.question)
        print("可用工具：list_docs, read_doc；最多 6 轮 / 8 次工具调用。")
        return
    print("mode=" + ("live" if args.live else "offline（固定 setup.md 演示；自定义问题请使用 --live）"))
    show(run(args.question, LiveModel() if args.live else DemoModel("docs"), ["list_docs", "read_doc"]))


if __name__ == "__main__":
    cli(main)
