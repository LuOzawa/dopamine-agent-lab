import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s61_langchain import run, calculate, weather
from s62_langgraph import build_graph, initial
from s64_deepagents import run as deep_run, SUMMARY, DOCS


class FrameworkTests(unittest.TestCase):
    def test_real_agent_message_and_call_linkage(self):
        messages = run()['messages']
        self.assertEqual([m.type for m in messages], ['human','ai','tool','ai','tool','ai'])
        self.assertEqual(messages[1].tool_calls[0]['id'], messages[2].tool_call_id)
        self.assertEqual(messages[4].content, '30')

    def test_tools_reject_invalid_input(self):
        for expr in ['__import__("os")', '1/0', '2**99', '9'*101]:
            self.assertTrue(calculate.invoke({'expression':expr}).startswith('错误'))
        self.assertIn('错误', weather.invoke({'city':'火星'}))

    def test_checkpoint_pause_resume_and_thread_isolation(self):
        graph=build_graph(True)
        config={'configurable':{'thread_id':'a'}, 'recursion_limit':16}
        graph.invoke(initial('密钥在哪里'), config)
        self.assertEqual(graph.get_state(config).next, ('answer',))
        self.assertEqual(graph.get_state(config).values['answer'], '')
        self.assertFalse(graph.get_state({'configurable':{'thread_id':'b'}}).values)
        result=graph.invoke(None,config)
        self.assertEqual(result['attempts'],2)
        self.assertIn('.env',result['answer'])

    def test_unanswerable_stops(self):
        result=build_graph().invoke(initial('火星'), {'configurable':{'thread_id':'missing'},'recursion_limit':16})
        self.assertEqual(result['attempts'],2)
        self.assertIn('资料不足',result['answer'])

    def test_deepagents_real_tools_and_recovery(self):
        result=deep_run()
        tools=[m for m in result['messages'] if m.type=='tool']
        self.assertEqual(len(tools),8)
        self.assertIn('not found',tools[1].content)
        self.assertTrue(all('not a valid tool' not in str(m.content) for m in tools))
        self.assertEqual(result['todos'][0]['status'],'completed')
        self.assertEqual(result['files']['/summary.md']['content'],SUMMARY)
        self.assertEqual(set(result['files']),set(DOCS)|{'/summary.md'})


if __name__=='__main__': unittest.main()
