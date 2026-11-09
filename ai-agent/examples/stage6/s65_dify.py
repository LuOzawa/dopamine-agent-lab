"""Dify Chatflow API v1 客户端。默认回放契约样本，--live 才发送网络请求。"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse


def ask(query, base_url, key, opener=urlopen):
    parsed = urlparse(base_url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname:
        raise ValueError('DIFY_BASE_URL 必须是完整 http(s) URL，含 /v1')
    if parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('远程服务请使用 HTTPS')
    if not key.strip():
        raise ValueError('缺少 DIFY_API_KEY：使用已发布 Chatflow 的应用密钥')
    payload = {'inputs': {}, 'query': query, 'response_mode': 'blocking', 'user': 'stage6-learner'}
    request = Request(base_url.rstrip('/') + '/chat-messages',
                      data=json.dumps(payload).encode(),
                      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with opener(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f'Dify HTTP {exc.code}：检查应用发布、密钥、模型与额度') from None
    except (URLError, TimeoutError):
        raise RuntimeError('Dify 连接失败或超时：检查地址与网络') from None
    except (ValueError, UnicodeError):
        raise RuntimeError('Dify 返回的不是有效 JSON') from None
    return summarize(data)


def summarize(data):
    if not isinstance(data, dict) or not isinstance(data.get('answer'), str) or not data['answer'].strip():
        raise ValueError('响应缺少非空 answer；确认应用类型为 Chatflow')
    metadata = data.get('metadata') or {}
    if not isinstance(metadata, dict):
        raise ValueError('响应 metadata 必须是对象')
    resources = metadata.get('retriever_resources') or []
    if not isinstance(resources, list):
        raise ValueError('retriever_resources 必须是列表')
    names = sorted({r['document_name'] for r in resources if isinstance(r, dict) and r.get('document_name')})
    return {'answer': data['answer'], 'sources': names}


def demo():
    cases = json.loads((Path(__file__).parent/'data/dify-cases.json').read_text())
    print('模式：API 契约样本回放；尚未连接 Dify 知识库')
    for case in cases:
        result = summarize(case['response'])
        print('问题：' + case['query'])
        print('回答：' + result['answer'])
        print('来源：' + ('、'.join(result['sources']) or '无（资料外拒答）'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--query', default='进度如何保存，换设备后还能继续吗？')
    args = parser.parse_args()
    try:
        if args.live:
            print(json.dumps(ask(args.query, os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1'),
                                 os.getenv('DIFY_API_KEY', '')), ensure_ascii=False, indent=2))
        else:
            demo()
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, str(exc) + '\n')
