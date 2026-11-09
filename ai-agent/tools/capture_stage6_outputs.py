#!/usr/bin/env python3
"""使用三个独立环境和 Docker 实跑七个入口，保存标准输出。"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT/'examples/stage6'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--framework-python', required=True)
    parser.add_argument('--crew-python', required=True)
    parser.add_argument('--graph-python', required=True)
    args=parser.parse_args()
    cases=[(args.framework_python,'s61_langchain.py'),(args.framework_python,'s62_langgraph.py'),
           (args.crew_python,'s63_crewai.py'),(args.framework_python,'s64_deepagents.py'),
           (sys.executable,'s65_dify.py'),(sys.executable,'s66_n8n.py'),(args.graph_python,'s67_graphrag.py')]
    captured=[]
    for interpreter,script in cases:
        # 保留 venv 入口：resolve() 会跟随 symlink 跳回系统解释器。
        run=subprocess.run([str(Path(interpreter).absolute()),script],cwd=LAB,text=True,
                           capture_output=True,timeout=180)
        if run.returncode or not run.stdout.strip():
            raise RuntimeError(f'{script} failed:\n{run.stderr}\n{run.stdout}')
        captured.append((script[:3]+'.txt',run.stdout.rstrip()+'\n'))
        print(f'{script}: OK')
    # 全部成功才更新，避免半份新输出混入页面。
    for name,output in captured:
        (LAB/'expected'/name).write_text(output)


if __name__=='__main__': main()
