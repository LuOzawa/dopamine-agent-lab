#!/usr/bin/env python3
"""重跑已定义的离线演示并记录输出。请用 Python 3.11 执行；不调用真实 API。"""
from pathlib import Path
import subprocess
import sys
import tempfile

LAB = Path(__file__).resolve().parents[1] / 'examples' / 'stage5'
COMMANDS = {
    's51': ['s51_setup.py'], 's52': ['s52_tools.py', '--invalid'],
    's53': ['s53_memory.py'], 's54': ['s54_agent.py'],
    's55': ['-m', 'lab', '--dry-run'], 's55-run': ['-m', 'lab'],
    's56': ['s56_guardrails.py'],
    's56-retry': ['s56_guardrails.py', '--scenario', 'malformed'],
    's56-budget': ['s56_guardrails.py', '--scenario', 'docs', '--max-turns', '1'],
    's56-parse': ['s56_guardrails.py', '--scenario', 'bad-json'],
    's57': ['s57_rag.py', '--eval'],
}


def main():
    for name, args in COMMANDS.items():
        with tempfile.TemporaryDirectory() as tmp:
            command = list(args) + (['--cache-dir', tmp] if name == 's57' else [])
            result = subprocess.run([sys.executable, '-S', *command], cwd=LAB,
                                    text=True, capture_output=True, check=True, timeout=30)
            (LAB / 'expected' / f'{name}.txt').write_text(result.stdout, encoding='utf-8')
    print(f'Captured {len(COMMANDS)} offline outputs. Review them before rebuilding HTML.')


if __name__ == '__main__':
    main()
