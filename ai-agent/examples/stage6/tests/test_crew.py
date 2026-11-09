import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from s63_crewai import run, FACTS, DRAFT, FINAL


class CrewTests(unittest.TestCase):
    def test_sequential_context_and_editor(self):
        result,models=run()
        self.assertEqual([t.agent for t in result.tasks_output],['researcher','writer','editor'])
        self.assertEqual([m.calls for m in models],[1,1,1])
        self.assertIn(FACTS,models[1].seen[0])
        self.assertIn(DRAFT,models[2].seen[0])
        self.assertEqual(result.raw,FINAL)
        self.assertTrue(250 <= len(FINAL) <= 400)

    def test_without_editor_keeps_draft(self):
        result,models=run(False)
        self.assertEqual(result.raw,DRAFT)
        self.assertEqual(len(models),2)


if __name__=='__main__': unittest.main()
