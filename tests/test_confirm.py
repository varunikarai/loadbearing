"""On a pipeline that is not deterministic, a move counts only if it happens again."""

import json
import threading
import unittest
import uuid

from loadbearing.backends.base import RunResult
from loadbearing.probe import CONFIRM_RUNS, probe
from loadbearing.verdict import INERT, LOAD_BEARING

from test_noise import noisy_target


class FlukyBackend:
    """Reads `body`, ignores `ticket_id`, stamps a fresh request id like an LLM call, and gets
    the priority wrong exactly once on the first run with a changed `ticket_id`: a sampling fluke."""

    name = "fluky"

    def __init__(self, fluke=True):
        self.fluke = fluke
        self.calls = 0
        self._lock = threading.Lock()
        self._fluked = False

    def checkpoint(self, target):
        return None

    def run(self, checkpoint, target, record):
        priority = "P1" if "outage" in str(record.get("body", "")) else "P3"
        with self._lock:
            self.calls += 1
            if self.fluke and record.get("ticket_id") != "T-7" and not self._fluked:
                self._fluked = True
                priority = "P2"
        return RunResult(json.dumps({"priority": priority, "request_id": uuid.uuid4().hex}), "", 0)

    def close(self):
        pass


class ConfirmTests(unittest.TestCase):
    def verdicts(self, report):
        return {v.field: v.verdict for v in report.verdicts}

    def test_one_fluke_on_an_irrelevant_field_is_not_a_phantom(self):
        report = probe(noisy_target(), FlukyBackend())
        self.assertEqual(self.verdicts(report), {"ticket_id": INERT, "body": LOAD_BEARING})
        fluked = [f for f in report.forks if f.mutation.field == "ticket_id" and f.runs > 1]
        self.assertEqual([(f.runs, f.moves) for f in fluked], [(1 + CONFIRM_RUNS, 1)])

    def test_the_terminal_and_the_page_say_which_move_was_not_counted(self):
        from loadbearing import report as report_json
        from loadbearing.cli import render
        from loadbearing.html_report import render_html

        report = probe(noisy_target(), FlukyBackend())
        fluke = next(f for f in report.forks if f.runs > 1 and not f.moved).mutation.label
        self.assertIn(f"not counted: {fluke} (1 of 3)", render(report))
        page = render_html(report_json.to_dict(report))
        self.assertIn(f"<b>{fluke}</b> (1 of 3) moved too rarely and was not counted", page)

    def test_a_real_move_is_confirmed_on_every_run(self):
        report = probe(noisy_target(), FlukyBackend(fluke=False))
        body = [f for f in report.forks if f.mutation.field == "body" and f.diff.moved]
        self.assertTrue(body)
        self.assertTrue(all(f.moved and f.runs == f.moves == 1 + CONFIRM_RUNS for f in body))

    def test_a_deterministic_pipeline_runs_nothing_extra(self):
        from pathlib import Path

        from loadbearing.backends.local import LocalBackend
        from loadbearing.target import load_target

        example = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"
        backend = LocalBackend()
        try:
            report = probe(load_target(example), backend)
        finally:
            backend.close()
        self.assertTrue(all(f.runs == 1 for f in report.forks))


if __name__ == "__main__":
    unittest.main()
