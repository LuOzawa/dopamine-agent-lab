"""离线行为回归与真实 SDK 的模拟 HTTP 契约测试，不发送外部请求。"""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.agent import run
from lab.models import DemoModel, LiveModel
from lab.tools import execute, calculate, read_doc
from s53_memory import connect, put, recall, forget
from s57_rag import Rag, EVALS


class Examples(unittest.TestCase):
    def test_calculator_and_rejected_code(self):
        self.assertEqual(calculate('(12+3)*2'), {'value': 30})
        for expression in ['__import__("os").getcwd()', '2**100000', 'True+1', '1/0', '1e309', '(', '']:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                calculate(expression)

    def test_schema_errors(self):
        for args in ['{}', '[]', '{"city":3}', '{"city":"北京","extra":1}', '{broken']:
            with self.subTest(args=args):
                self.assertFalse(execute('get_weather', args, ['get_weather'])['ok'])
        self.assertTrue(execute('get_weather', '{"city":"北京"}', ['get_weather'])['ok'])

    def test_permission_boundary(self):
        with self.assertRaises(PermissionError):
            read_doc('../.env')
        with self.assertRaises(PermissionError):
            execute('unknown', '{}', ['list_docs'])

    def test_missing_file_recovery(self):
        result = run('read', DemoModel('missing'), ['list_docs', 'read_doc'], trace=lambda _: None)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['turns'], 4)
        self.assertIn('setup.md', result['answer'])
        self.assertEqual(result['tool_calls'], 3)

    def test_invalid_weather_recovery(self):
        result = run('weather', DemoModel('invalid'), ['get_weather', 'calculate'], trace=lambda _: None)
        self.assertEqual(result['status'], 'completed')
        self.assertIn('30', result['answer'])
        self.assertEqual(result['tool_calls'], 3)

    def test_loop_stops_before_second_execution(self):
        result = run('loop', DemoModel('loop'), ['list_docs'], guarded=True, trace=lambda _: None)
        self.assertEqual((result['status'], result['turns'], result['tool_calls']), ('repeated_action', 2, 1))

    def test_parse_retry_succeeds_once(self):
        result = run('read', DemoModel('malformed'), ['list_docs', 'read_doc'], guarded=True, trace=lambda _: None)
        self.assertEqual(result['status'], 'completed')
        result = run('read', DemoModel('bad-json'), ['list_docs'], guarded=True, trace=lambda _: None)
        self.assertEqual((result['status'], result['turns']), ('parse_error', 2))

    def test_budgets_preserve_partial_work(self):
        for options, status in [({'max_turns': 1}, 'turn_limit'), ({'max_calls': 1}, 'tool_limit')]:
            result = run('read', DemoModel(), ['list_docs', 'read_doc'], trace=lambda _: None, **options)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['completed'], ['list_docs'])
            self.assertEqual(result['unfinished'], ['read'])
            self.assertTrue(result['next_step'])

    def test_memory_persistence_update_expiry_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'memory.db'
            db = connect(path)
            with self.assertRaises(ValueError):
                put(db, 'language', '中文')
            put(db, 'language', '中文', confirmed=True)
            put(db, 'language', '英文', confirmed=True)
            db.close()
            db = connect(path)
            self.assertEqual(recall(db), [{'id': 'language', 'content': '英文'}])
            self.assertEqual(recall(db, now=1e12), [])
            self.assertEqual(forget(db, 'language'), 1)
            self.assertEqual(recall(db), [])
            db.close()

    def test_offline_rag_five_cases_and_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            rag = Rag(cache_dir=tmp)
            self.assertFalse(rag.cache_hit)
            for question, source, keyword in EVALS:
                result = rag.ask(question)
                if source is None:
                    self.assertTrue(result['refused'])
                else:
                    self.assertFalse(result['refused'])
                    self.assertIn(source, [result['hits'][n-1]['source'] for n in result['citations']])
                    self.assertIn(keyword, result['answer'])
            self.assertTrue(Rag(cache_dir=tmp).cache_hit)
            with self.assertRaises(ValueError):
                rag.ask('test', float('nan'))

    def test_cache_invalidated_on_document_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs, cache = Path(tmp) / 'docs', Path(tmp) / 'cache'
            docs.mkdir(); (docs / 'test.md').write_text('API 密钥保存在 .env。', encoding='utf-8')
            Rag(folder=docs, cache_dir=cache)
            (docs / 'test.md').write_text('API 密钥保存在环境变量。', encoding='utf-8')
            self.assertFalse(Rag(folder=docs, cache_dir=cache).cache_hit)
            (cache / 'rag-offline.json').write_text('{broken')
            self.assertFalse(Rag(folder=docs, cache_dir=cache).cache_hit)

    def test_dry_run_never_initializes_model(self):
        from lab.__main__ import main
        with patch.object(sys, 'argv', ['lab', '--dry-run', '--live']), patch('lab.__main__.LiveModel', side_effect=AssertionError('network')), contextlib.redirect_stdout(io.StringIO()) as output:
            main()
        self.assertIn('DRY RUN', output.getvalue())

    def test_all_cli_entrypoints_without_site_packages(self):
        # -S 禁用第三方包，证明离线路径只需标准库。
        for args in [['s51_setup.py'], ['s52_tools.py'], ['s53_memory.py'], ['s54_agent.py'], ['-m','lab'], ['s56_guardrails.py']]:
            result = subprocess.run([sys.executable, '-S', *args], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable,'-S','s57_rag.py','--eval','--cache-dir',tmp], cwd=ROOT, text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('通过 5/5', result.stdout)


try:
    import httpx
    from openai import OpenAI
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


def response(output, text=None):
    if text is not None:
        output = [{"id":"msg_test","type":"message","role":"assistant","status":"completed",
                   "content":[{"type":"output_text","text":text,"annotations":[]}]}]
    return {"id":"resp_test","object":"response","created_at":1,"status":"completed",
            "model":"test-model","output":output,"usage":{"input_tokens":5,"output_tokens":5,"total_tokens":10}}


@unittest.skipUnless(SDK_AVAILABLE, '安装 requirements-lock.txt 后执行 SDK 契约测试')
class SDKContract(unittest.TestCase):
    def test_responses_tool_round_trip_with_real_sdk(self):
        requests=[]
        def handler(request):
            body=json.loads(request.content); requests.append(body)
            self.assertEqual(request.url.path,'/v1/responses')
            self.assertFalse(body['store'])
            if len(requests)==1:
                return httpx.Response(200,json=response([
                    {"id":"rs_test","type":"reasoning","summary":[]},
                    {"id":"fc_test","type":"function_call","status":"completed","call_id":"call_test","name":"calculate","arguments":'{"expression":"1+2"}'}]))
            outputs=[x for x in body['input'] if x.get('type')=='function_call_output']
            self.assertEqual(outputs[0]['call_id'],'call_test')
            self.assertEqual(json.loads(outputs[0]['output'])['data']['value'],3)
            self.assertTrue(any(x.get('type')=='reasoning' for x in body['input']))
            return httpx.Response(200,json=response([],text='结果为 3。'))
        with OpenAI(api_key='test-not-a-real-key',http_client=httpx.Client(transport=httpx.MockTransport(handler)),base_url='https://example.test/v1',max_retries=0) as client:
            model=LiveModel.__new__(LiveModel);model.client=client;model.model='test-model'
            result=run('1+2',model,['calculate'],trace=lambda _:None)
        self.assertEqual(result['status'],'completed');self.assertEqual(result['tokens'],20)
        self.assertEqual(len(requests),2)

    def test_live_rag_embeddings_cache_and_invalid_citations(self):
        requests=[]; answer=['API 密钥保存在 .env。 [1]']
        def handler(request):
            body=json.loads(request.content);requests.append((request.url.path,body))
            if request.url.path.endswith('/embeddings'):
                return httpx.Response(200,json={"object":"list","model":"test-embedding","data":[{"object":"embedding","index":i,"embedding":[1.0,0.0]} for i,_ in enumerate(body['input'])],"usage":{"prompt_tokens":1,"total_tokens":1}})
            return httpx.Response(200,json=response([],text=answer[0]))
        with tempfile.TemporaryDirectory() as tmp, OpenAI(api_key='test-not-a-real-key',http_client=httpx.Client(transport=httpx.MockTransport(handler)),base_url='https://example.test/v1',max_retries=0) as client:
            docs=Path(tmp)/'docs';docs.mkdir();(docs/'setup.md').write_text('API 密钥保存在 .env。',encoding='utf-8')
            cache=Path(tmp)/'cache'
            rag=Rag(True,folder=docs,cache_dir=cache,client=client)
            self.assertFalse(rag.ask('密钥在哪里？')['refused'])
            before=len(requests);self.assertTrue(Rag(True,folder=docs,cache_dir=cache,client=client).cache_hit);self.assertEqual(before,len(requests))
            answer[0]='无依据回答 [99]';self.assertTrue(rag.ask('密钥在哪里？')['refused'])
            self.assertTrue((cache/'rag-live.json').exists())
            self.assertFalse((cache/'rag-offline.json').exists())

    def test_missing_key_has_actionable_error(self):
        from lab.config import live_client
        with patch.dict(os.environ,{'OPENAI_API_KEY':''}),patch('dotenv.load_dotenv'):
            with self.assertRaisesRegex(ValueError,'缺少 OPENAI_API_KEY'):
                live_client()


if __name__ == '__main__':
    unittest.main(verbosity=2)
