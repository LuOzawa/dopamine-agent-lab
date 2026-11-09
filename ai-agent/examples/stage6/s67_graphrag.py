"""实际 GraphRAG CLI 初始化/配置检查。默认不建索引、不调用模型。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def prepare(path):
    if path.exists():
        raise ValueError('目标已存在：请指定新目录，避免覆盖已有配置和密钥')
    path.mkdir(parents=True)
    cli = Path(sys.executable).with_name('graphrag.exe' if os.name == 'nt' else 'graphrag')
    env = dict(os.environ, LITELLM_LOCAL_MODEL_COST_MAP='True', GRAPHRAG_API_KEY='offline-placeholder')
    commands = [[str(cli), 'init', '--root', str(path), '--model', 'gpt-5.4-mini-2026-03-17',
                 '--embedding', 'text-embedding-3-small'],
                [str(cli), 'index', '--root', str(path), '--dry-run', '--skip-validation']]
    for i, cmd in enumerate(commands):
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=90)
        if proc.returncode:
            raise RuntimeError('GraphRAG CLI 失败：\n' + (proc.stderr + proc.stdout)[-2000:])
        if i == 0:
            shutil.copytree(ROOT/'data/articles', path/'input', dirs_exist_ok=True)
    if not (path/'settings.yaml').is_file() or len(list((path/'input').glob('*.txt'))) != 5:
        raise RuntimeError('项目材料不完整')
    print('GraphRAG 3.3.0：init 完成；5 篇教学资料已复制')
    print('index --dry-run --skip-validation：配置检查通过')
    print('模型请求=0；未生成实体、社区报告或向量索引')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', type=Path, help='保留项目供真实 API 实验，目标必须不存在')
    args = parser.parse_args()
    try:
        if args.prepare:
            prepare(args.prepare.resolve())
            print('下一步：按 GRAPHRAG.md 配置密钥，再真实 index/query。')
        else:
            with tempfile.TemporaryDirectory(prefix='stage6-graphrag-') as tmp:
                prepare(Path(tmp)/'project')
            print('临时项目已清理；真实检索质量与费用尚未测量')
    except (ValueError, RuntimeError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, str(exc) + '\n')
