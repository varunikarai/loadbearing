import importlib.util
import unittest
from pathlib import Path

from fakes import router

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "eval_nano.py"
spec = importlib.util.spec_from_file_location("eval_nano", SCRIPT)
eval_nano = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_nano)


class EvalNanoTests(unittest.TestCase):
    def setUp(self):
        self.cases = eval_nano.load_cases()

    def test_the_fixture_is_balanced(self):
        labels = [c["label"] for c in self.cases]
        self.assertEqual(len(labels), 20)
        self.assertEqual(labels.count("meaningful"), 10)
        self.assertEqual(labels.count("noise"), 10)

    def test_a_perfect_classifier_scores_20(self):
        answers = {(c["mutation"], c["fork"]): c["label"] for c in self.cases}
        correct, misses = eval_nano.evaluate(
            self.cases, lambda m, b, f: answers[(m.label, f.stdout)]
        )
        self.assertEqual((correct, misses), (20, []))

    def test_always_meaningful_scores_10_and_lists_its_misses(self):
        correct, misses = eval_nano.evaluate(self.cases, lambda m, b, f: "meaningful")
        self.assertEqual(correct, 10)
        self.assertTrue(all(miss["got"] == "meaningful" and miss["label"] == "noise" for miss in misses))

    def test_runs_through_the_real_router_and_its_prompt(self):
        r, client = router({"nano": "<think>it is a timestamp</think>noise"})
        correct, _ = eval_nano.evaluate(self.cases, r.classify_diff)
        self.assertEqual(correct, 10)
        self.assertEqual(len(client.calls), 20)


if __name__ == "__main__":
    unittest.main()
