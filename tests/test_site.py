"""The demo's front page: built from recorded runs and the benchmark, never from typed-in numbers."""

import json
import tempfile
import unittest
from pathlib import Path

from loadbearing.serve import Demo
from loadbearing.site import render_index

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "demo" / "runs"


class FrontPageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        for run in RUNS.glob("*.json"):
            (Path(self._tmp.name) / run.name).write_text(run.read_text())
        self.demo = Demo([ROOT / "examples", ROOT / "bench" / "cases"], self._tmp.name, readonly=True)
        self.page = render_index(self.demo)

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_hero_quotes_the_recorded_bot_before_and_after_the_fix(self):
        data = json.loads((RUNS / "support_answerer.local.json").read_text())
        from html import escape

        before = data["baseline"]["output"]["answer"]
        after = next(p for p in data["proofs"] if p["clean"])["after"]["baseline"]["output"]["answer"]
        self.assertIn(escape(before), self.page)
        self.assertIn(escape(after), self.page)

    def test_the_hero_replays_every_copy_of_the_recorded_run_and_its_fix(self):
        data = json.loads((RUNS / "support_answerer.local.json").read_text())
        replay = json.loads(self.page.split('id="replay-data">', 1)[1].split("</script>", 1)[0])
        self.assertEqual([(f["field"], f["kind"], f["moved"]) for f in replay["forks"]],
                         [(f["field"], f["kind"], f["moved"]) for f in data["forks"]])
        self.assertEqual([f["name"] for f in replay["fields"] if f["defect"]], ["passages"])
        self.assertIn('request.get("passages", "")', " ".join(replay["fix"]["add"]))
        self.assertEqual(replay["after"]["verdicts"]["passages"], "load-bearing")

    def test_the_benchmark_numbers_come_from_results_json(self):
        results = json.loads((ROOT / "bench" / "results.json").read_text())
        ours = next(v for k, v in results["cases_right"].items() if k.startswith("Loadbearing"))
        self.assertIn(f'{ours}<small>/{results["cases"]}</small>', self.page)

    def test_every_benchmark_case_is_a_card_carrying_its_planted_truth(self):
        cases = sorted(p.parent.name for p in (ROOT / "bench" / "cases").glob("*/target.json"))
        for name in cases:
            truth = json.loads((ROOT / "bench" / "cases" / name / "truth.json").read_text())["defects"]
            self.assertIn(f'data-name="{name}"', self.page, name)
            self.assertIn(json.dumps(truth).replace('"', "&quot;"), self.page, name)

    def test_a_paid_target_offers_its_recorded_run_and_a_free_one_a_run_button(self):
        paid = self.page.split('data-name="support_answerer"', 1)[1].split("</article>", 1)[0]
        free = self.page.split('data-name="ticket_triage"', 1)[1].split("</article>", 1)[0]
        self.assertIn("View the recorded run", paid)
        self.assertNotIn("Run probe", paid)
        self.assertIn('action="/t/ticket_triage/run"', free)

    def test_the_page_claims_nothing_that_is_not_true_yet(self):
        self.assertNotIn("pip install loadbearing", self.page)  # not on PyPI
        self.assertIn("waiting on beta access", self.page)  # Sandboxes has not run live
        self.assertNotIn("http://", self.page.replace("http://www.w3.org/2000/svg", ""))

    def test_the_page_fetches_nothing_from_elsewhere(self):
        for tag in ("<script src", "<link rel=\"stylesheet\"", "@import", "fonts.googleapis"):
            self.assertNotIn(tag, self.page)


if __name__ == "__main__":
    unittest.main()
