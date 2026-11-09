"""在断网的临时 n8n 容器中实际执行工作流，并检查成功/失败路由。"""
import json
from pathlib import Path
import subprocess
import uuid

IMAGE = 'docker.n8n.io/n8nio/n8n:2.44.7'
ROOT = Path(__file__).resolve().parent


def parse_execution(output):
    # n8n --rawOutput 前仍可能打印迁移与 runner 日志。
    decoder = json.JSONDecoder()
    for i, char in enumerate(output):
        if char != '{':
            continue
        try:
            value, _ = decoder.raw_decode(output[i:])
        except ValueError:
            continue
        if isinstance(value, dict) and 'data' in value and 'finished' in value:
            return value
    raise RuntimeError('没有找到 n8n 执行结果；检查容器日志')


def verify(result):
    if result.get('status') != 'success':
        raise RuntimeError('工作流失败：' + str(result.get('status')))
    runs = result['data']['resultData']['runData']
    items = [item['json'] for name in ('Success', 'Fallback')
             for run in runs.get(name, []) for branch in run['data']['main'] for item in branch]
    routes = {i['case']: i['route'] for i in items}
    if routes != {'valid': 'success', 'malformed': 'fallback', 'missing-field': 'fallback'}:
        raise RuntimeError('分支结果与验收不符：' + str(routes))
    return items


def main():
    name = 'stage6-test-' + uuid.uuid4().hex[:12]
    cmd = ['docker', 'run', '--rm', '--name', name, '--network', 'none',
           '-e', 'N8N_DIAGNOSTICS_ENABLED=false', '-e', 'N8N_VERSION_NOTIFICATIONS_ENABLED=false',
           '-e', 'N8N_TEMPLATES_ENABLED=false', '-e', 'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true',
           '-v', f'{ROOT / "n8n"}:/work:ro', '--entrypoint', '/bin/sh', IMAGE, '-c',
           'n8n import:workflow --input=/work/offline.json >/tmp/import.log && '
           'n8n execute --id=Stage6Smoke --rawOutput']
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=120)
    finally:
        # 超时杀掉 Docker CLI 后也清理本次容器；不会操作其他容器。
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=15)
    if result.returncode:
        raise RuntimeError('n8n 执行失败：\n' + (result.stderr + result.stdout)[-2000:])
    items = verify(parse_execution(result.stdout))
    print('n8n 2.44.7：真实工作流；容器断网；模型输出为固定样本')
    for item in items:
        print(f'{item["case"]} → {item["route"]}：{item["summary"]}')
    print('3/3 分支验收通过；容器退出即删除数据库')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(str(exc))
