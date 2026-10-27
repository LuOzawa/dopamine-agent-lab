"""5.2：天气与计算工具的完整请求—执行—回传循环。"""
import argparse
from lab.config import cli
from lab.models import DemoModel, LiveModel
from lab.agent import run, show


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--invalid", action="store_true", help="离线注入空城市参数，观察修复")
    args = parser.parse_args()
    if args.live and args.invalid:
        raise ValueError("--invalid 是确定性的离线故障演示，请去掉 --live。")
    model = LiveModel() if args.live else DemoModel("invalid" if args.invalid else "weather")
    print("mode=" + ("live" if args.live else "offline（脚本驱动器，非模型推理）"))
    show(run("先查北京的教学天气，再计算 (12+3)*2，报告来源和结果。", model, ["get_weather", "calculate"]))


if __name__ == "__main__":
    cli(main)
