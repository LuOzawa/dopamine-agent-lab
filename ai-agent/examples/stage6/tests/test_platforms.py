import io
import json
import sys
import tempfile
from pathlib import Path
import unittest
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from s65_dify import ask, summarize
from s66_n8n import parse_execution
from s67_graphrag import prepare, ROOT


class PlatformTests(unittest.TestCase):
    def test_dify_request_contract(self):
        def fake(request,timeout):
            self.assertEqual(request.full_url,'https://example.test/v1/chat-messages')
            self.assertEqual(timeout,30)
            self.assertEqual(request.get_header('Authorization'),'Bearer test-only')
            body=json.loads(request.data)
            self.assertEqual(body['response_mode'],'blocking')
            self.assertEqual(body['inputs'],{})
            return io.BytesIO(json.dumps({'answer':'ok','metadata':{'retriever_resources':[{'document_name':'faq.md'}]}}).encode())
        self.assertEqual(ask('问题','https://example.test/v1','test-only',fake),{'answer':'ok','sources':['faq.md']})

    def test_dify_missing_key_and_insecure_remote(self):
        for base,key in [('https://example.test/v1',''),('http://example.test/v1','test')]:
            with self.assertRaises(ValueError): ask('q',base,key)

    def test_dify_http_failure(self):
        def fail(*args,**kwargs): raise HTTPError('url',401,'no',None,None)
        with self.assertRaisesRegex(RuntimeError,'401'): ask('q','https://example.test/v1','test',fail)

    def test_dify_bad_json(self):
        with self.assertRaisesRegex(RuntimeError,'JSON'):
            ask('q','https://example.test/v1','test',lambda *a,**k:io.BytesIO(b'not json'))

    def test_dify_empty_and_refusal(self):
        with self.assertRaises(ValueError): summarize({'answer':''})
        cases=json.loads((ROOT/'data/dify-cases.json').read_text())
        self.assertEqual(len(cases),3)
        self.assertEqual(summarize(cases[-1]['response'])['sources'],[])

    def test_n8n_shared_validation_and_branches(self):
        docs=[json.loads((ROOT/'n8n'/p).read_text()) for p in ['offline.json','webhook.json']]
        for name in ['Validate','Valid?','Success','Fallback']:
            self.assertEqual(next(n for n in docs[0]['nodes'] if n['name']==name),next(n for n in docs[1]['nodes'] if n['name']==name))
        self.assertEqual(next(n for n in docs[0]['nodes'] if n['name']=='Validate')['parameters']['jsCode'],(ROOT/'n8n/validate.js').read_text().rstrip())

    def test_n8n_parser_handles_prefixed_logs(self):
        self.assertEqual(parse_execution('runner started\n{"data":{},"finished":true}')['finished'],True)
        with self.assertRaises(RuntimeError): parse_execution('no JSON')

    def test_graphrag_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as path:
            with self.assertRaisesRegex(ValueError,'已存在'): prepare(Path(path))


if __name__=='__main__': unittest.main()
