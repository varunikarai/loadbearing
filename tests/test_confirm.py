"""On a pipeline that is not deterministic, a move counts only if it happens again."""

import json
import threading
import unittest
import uuid

from loadbearing.backends.base import RunResult
from loadbearing.probe import CONFIRM_RUNS, probe
from loadbearing.verdict import INERT, LOAD_BEARING, PHANTOM_SENSITIVITY

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


class IdSensitiveBackend:
    """Routes by the ticket id's last character every time: a real phantom sensitivity."""

    name = "id-sensitive"

    def checkpoint(self, target):
        return None

    def run(self, checkpoint, target, record):
        out = {"queue": str(record.get("ticket_id", ""))[-1:], "request_id": uuid.uuid4().hex}
        return RunResult(json.dumps(out), "", 0)

    def close(self):
        pass


class WeakReaderBackend:
    """Reads `body`, but like a model that only sometimes uses its context: each changed body
    moves the priority on its first run only, and later runs of that same input fall back to
    the answer it gives with the real body."""

    name = "weak"

    def __init__(self):
        self.seen = set()
        self._lock = threading.Lock()

    def checkpoint(self, target):
        return None

    def run(self, checkpoint, target, record):
        body = str(record.get("body", "<dropped>"))
        with self._lock:
            first = body not in self.seen
            self.seen.add(body)
        priority = "P1" if "outage" in body or not first else "P3"
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

    def test_a_move_on_a_field_that_should_matter_counts_at_once(self):
        report = probe(noisy_target(), FlukyBackend(fluke=False))
        body = [f for f in report.forks if f.mutation.field == "body" and f.diff.moved]
        self.assertTrue(body)
        self.assertTrue(all(f.moved and f.runs == f.moves == 1 for f in body))

    def test_a_real_phantom_sensitivity_is_confirmed_on_every_run(self):
        report = probe(noisy_target(), IdSensitiveBackend())
        self.assertEqual(self.verdicts(report)["ticket_id"], PHANTOM_SENSITIVITY)
        moved = [f for f in report.forks if f.mutation.field == "ticket_id" and f.diff.moved]
        self.assertTrue(moved)
        self.assertTrue(all(f.moved and f.runs == f.moves == 1 + CONFIRM_RUNS for f in moved))

    def test_a_fork_that_never_moved_records_no_moves(self):
        report = probe(noisy_target(), FlukyBackend(fluke=False))
        still = [f for f in report.forks if not f.diff.moved]
        self.assertTrue(still)
        self.assertTrue(all(f.moves == 0 and f.runs == 1 for f in still))

    def test_a_weak_reading_of_a_field_that_should_matter_is_not_called_a_silent_passthrough(self):
        # Confirming moves here would turn a real but unreliable reading into a defect claim.
        report = probe(noisy_target(), WeakReaderBackend())
        self.assertEqual(self.verdicts(report)["body"], LOAD_BEARING)

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
