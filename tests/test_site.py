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
        data = json.loads((RUNS / "support_answerer.sandbox.json").read_text())
        from html import escape

        before = data["baseline"]["output"]["answer"]
        after = next(p for p in data["proofs"] if p["clean"])["after"]["baseline"]["output"]["answer"]
        self.assertIn(escape(before), self.page)
        self.assertIn(escape(after), self.page)

    def test_the_hero_replays_every_copy_of_the_recorded_run_and_its_fix(self):
        data = json.loads((RUNS / "support_answerer.sandbox.json").read_text())
        replay = json.loads(self.page.split('id="replay-data">', 1)[1].split("</script>", 1)[0])
        self.assertEqual([(f["field"], f["kind"], f["moved"]) for f in replay["forks"]],
                         [(f["field"], f["kind"], f["moved"]) for f in data["forks"]])
        self.assertEqual([f["name"] for f in replay["fields"] if f["defect"]], ["passages"])
        self.assertIn('request.get("passages", "")', " ".join(replay["fix"]["add"]))
        self.assertEqual(replay["after"]["verdicts"]["passages"], "load-bearing")

    def test_the_run_time_names_every_run_it_covers(self):
        data = json.loads((RUNS / "support_answerer.sandbox.json").read_text())
        where = "Nebius Sandboxes" if data["backend"] == "sandbox" else "Nemotron"
        self.assertIn(f'for all {data["timing"]["runs"]} runs on {where}', self.page)
        self.assertNotIn("Every test passed", self.page)  # the demo target has no tests

    def test_the_benchmark_numbers_come_from_results_json(self):
        results = json.loads((ROOT / "bench" / "results.json").read_text())
        ours = next(v for k, v in results["cases_right"].items() if k.startswith("Loadbearing"))
        self.assertIn(f'{ours}<small>/{results["cases"]}</small>', self.page)

    def test_the_model_is_shown_over_every_run_it_made_not_its_first(self):
        results = json.loads((ROOT / "bench" / "results.json").read_text())
        first = next(k for k in results["calls"] if k.startswith("Nemotron"))
        runs = [results["calls"][first], *results["repeats"].values()]
        cases = [p.parent for p in (ROOT / "bench" / "cases").glob("*/truth.json")]

        def right(calls, case):
            expects = json.loads((case / "target.json").read_text())["expects"]
            truth = json.loads((case / "truth.json").read_text())["defects"]
            got = calls.get(case.name, {})
            return all(got.get(f, "") == truth.get(f, "") for f in expects["relevant"] + expects["irrelevant"])

        scores = [sum(right(calls, case) for case in cases) for calls in runs]
        self.assertGreater(len(set(scores)), 1)  # the case this guards: the runs disagree
        self.assertIn(f'{min(scores)}–{max(scores)}<small>/{results["cases"]}</small>', self.page)
        self.assertIn(f"{len(runs)} runs", self.page)

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
        # Sandboxes is claimed only because the replayed run was recorded there.
        self.assertEqual(json.loads((RUNS / "support_answerer.sandbox.json").read_text())["backend"], "sandbox")
        self.assertIn("recorded there, live", self.page)
        self.assertIn("recorded live on Nebius Sandboxes", self.page)
        self.assertNotIn("http://", self.page.replace("http://www.w3.org/2000/svg", ""))

    def test_the_page_fetches_nothing_from_elsewhere(self):
        for tag in ("<script src", "<link rel=\"stylesheet\"", "@import", "fonts.googleapis"):
            self.assertNotIn(tag, self.page)


class CaughtInTheWildTests(unittest.TestCase):
    """Real bugs from public issues, judged from the recorded runs of both releases."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        for run in RUNS.glob("*.json"):
            (Path(self._tmp.name) / run.name).write_text(run.read_text())
        demo = Demo([ROOT / "examples", ROOT / "bench" / "cases", ROOT / "realworld"], self._tmp.name, readonly=True)
        self.page = render_index(demo)

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_case_is_caught_on_the_buggy_release_and_cleared_on_the_fixed_one(self):
        cases = json.loads((ROOT / "realworld" / "cases.json").read_text())
        for case in cases:
            buggy = json.loads((RUNS / f'{case["buggy"]}.sandbox.json').read_text())
            fixed = json.loads((RUNS / f'{case["fixed"]}.sandbox.json').read_text())
            flagged = [v["field"] for v in buggy["verdicts"] if v["defect"]]
            self.assertTrue(flagged, case["buggy"])
            self.assertTrue(all(f == case["field"] or f.startswith(case["field"] + ".") for f in flagged), flagged)
            self.assertFalse([v for v in fixed["verdicts"] if v["defect"]], case["fixed"])
            self.assertEqual((buggy["backend"], fixed["backend"]), ("sandbox", "sandbox"))
            self.assertIn(case["issue"], self.page)
        total = 2 * len(cases)
        self.assertIn(f'data-count="{total}">{total}</b><small> / {total}</small>', self.page)

    def test_the_releases_stay_out_of_the_benchmark_and_never_run_on_the_host(self):
        self.assertIn("Run all 54, live", self.page)
        for target in (ROOT / "realworld").glob("*/target.json"):
            card = self.page.split(f'href="/t/{target.parent.name}"', 1)
            self.assertEqual(len(card), 2, target.parent.name)  # linked from its case
            self.assertNotIn(f'action="/t/{target.parent.name}/run"', self.page)


if __name__ == "__main__":
    unittest.main()
