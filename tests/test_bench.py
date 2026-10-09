"""The benchmark is reproducible: the committed cases are what the generator writes,
and Loadbearing's calls on them are the ones RESULTS.md reports."""

import json
import sys
import unittest
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent / "bench"
sys.path.insert(0, str(BENCH))

import generate  # noqa: E402
import run  # noqa: E402


class BenchTests(unittest.TestCase):
    def test_committed_cases_match_the_generator(self):
        for name, case in generate.cases().items():
            folder = BENCH / "cases" / name
            self.assertEqual((folder / "pipeline.py").read_text(), case["source"], name)
            self.assertEqual(json.loads((folder / "truth.json").read_text())["defects"], case["truth"], name)
        self.assertEqual(len(list((BENCH / "cases").iterdir())), len(generate.cases()))

    def test_loadbearing_calls_match_the_published_results(self):
        published = json.loads((BENCH / "results.json").read_text())["calls"]["Loadbearing (runs it)"]
        cases = sorted(p for p in (BENCH / "cases").iterdir() if p.is_dir())
        self.assertEqual({c.name: run.loadbearing(c) for c in cases}, published)

    def test_mcnemar_matches_a_hand_computed_value(self):
        # 3 vs 0 discordant pairs: p = 2 * (1/8) = 0.25
        a = {"c": {"x": "silent passthrough", "y": "silent passthrough", "z": "silent passthrough"}}
        b = {"c": {}}
        original = run.units
        run.units = lambda case: [("x", "silent passthrough"), ("y", "silent passthrough"), ("z", "silent passthrough")]
        try:
            self.assertEqual(run.mcnemar(a, b, [Path("c")]), (3, 0, 0.25))
        finally:
            run.units = original


if __name__ == "__main__":
    unittest.main()
