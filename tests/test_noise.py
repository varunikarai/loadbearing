"""The noise floor: verdicts stay right when the output varies on its own."""

import json
import unittest
import uuid
from pathlib import Path

from loadbearing.backends.base import RunResult
from loadbearing.backends.local import LocalBackend
from loadbearing.compare import EXIT, STDOUT, compare
from loadbearing.noise import unstable_keys, void
from loadbearing.probe import probe
from loadbearing.target import Target, load_target
from loadbearing.verdict import INERT, IRRELEVANT, LOAD_BEARING, PHANTOM_SENSITIVITY, RELEVANT

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


def run(output, exit_code=0):
    return RunResult(output if isinstance(output, str) else json.dumps(output), "", exit_code)


class NoisyBackend:
    """A pipeline that reads `body`, ignores `ticket_id`, and stamps a fresh request id on every run,
    the way an LLM call returns a new id or a reworded sentence each time."""

    name = "noisy"

    def __init__(self, whole_output_varies=False):
        self.whole_output_varies = whole_output_varies

    def checkpoint(self, target):
        return None

    def run(self, checkpoint, target, record):
        if self.whole_output_varies:
            return run(uuid.uuid4().hex)
        priority = "P1" if "outage" in str(record.get("body", "")) else "P3"
        return run({"priority": priority, "request_id": uuid.uuid4().hex})

    def close(self):
        pass


def noisy_target(baseline_runs=3):
    return Target(
        name="noisy",
        root=Path("."),
        image="",
        setup="",
        files=[],
        command="",
        record={"ticket_id": "T-7", "body": "full outage since 09:00"},
        expects={"relevant": ["body"], "irrelevant": ["ticket_id"]},
        baseline_runs=baseline_runs,
    )


class UnstableKeysTests(unittest.TestCase):
    def test_finds_only_the_key_that_varies(self):
        runs = [run({"p": "P1", "id": i}) for i in range(3)]
        self.assertEqual(unstable_keys(runs), ["id"])

    def test_a_stable_output_has_no_unstable_keys(self):
        self.assertEqual(unstable_keys([run({"p": "P1"})] * 3), [])

    def test_varying_plain_text_is_unstable_as_a_whole(self):
        self.assertEqual(unstable_keys([run("a"), run("b")]), [STDOUT])

    def test_a_varying_exit_code_voids_the_report(self):
        unstable = unstable_keys([run({"p": "P1"}), run("", exit_code=1)])
        self.assertEqual(unstable, [EXIT])
        self.assertTrue(void(unstable, run({"p": "P1"})))

    def test_void_only_when_nothing_stable_is_left(self):
        self.assertFalse(void(["id"], run({"p": "P1", "id": 1})))
        self.assertTrue(void(["p", "id"], run({"p": "P1", "id": 1})))

    def test_compare_never_counts_an_ignored_key_as_moved(self):
        diff = compare(run({"p": "P1", "id": 1}), run({"p": "P1", "id": 2}), ignore=["id"])
        self.assertFalse(diff.moved)
        diff = compare(run({"p": "P1", "id": 1}), run({"p": "P3", "id": 2}), ignore=["id"])
        self.assertEqual(diff.changed, ["p"])


class ProbeAboveTheNoiseFloorTests(unittest.TestCase):
    def test_verdicts_stay_right_when_one_key_varies_on_its_own(self):
        report = probe(noisy_target(), NoisyBackend())
        verdicts = {v.field: v.verdict for v in report.verdicts}
        self.assertEqual(verdicts, {"ticket_id": INERT, "body": LOAD_BEARING})
        self.assertEqual(report.unstable_keys, ["request_id"])
        self.assertEqual(report.baseline_runs, 3)
        self.assertFalse(report.deterministic)
        self.assertFalse(report.void)

    def test_without_the_floor_the_noise_would_frame_an_irrelevant_field(self):
        # What the old two-run check missed: every fork's request id differs from the baseline's.
        target = noisy_target()
        report = probe(target, NoisyBackend())
        fork = next(f for f in report.forks if f.mutation.label == "nudge:ticket_id")
        raw = compare(report.baseline, fork.result)
        self.assertEqual(raw.changed, ["request_id"])
        self.assertFalse(fork.moved)
        self.assertNotEqual({v.field: v.verdict for v in report.verdicts}["ticket_id"], PHANTOM_SENSITIVITY)

    def test_a_report_with_nothing_stable_is_void(self):
        report = probe(noisy_target(), NoisyBackend(whole_output_varies=True))
        self.assertTrue(report.void)

    def test_the_override_beats_the_target_setting(self):
        report = probe(noisy_target(baseline_runs=2), NoisyBackend(), baseline_runs=5)
        self.assertEqual(report.baseline_runs, 5)

    def test_one_baseline_run_is_refused(self):
        with self.assertRaises(ValueError):
            probe(noisy_target(), NoisyBackend(), baseline_runs=1)

    def test_the_toy_target_is_unchanged(self):
        backend = LocalBackend()
        try:
            report = probe(load_target(EXAMPLE), backend)
        finally:
            backend.close()
        self.assertEqual(report.unstable_keys, [])
        self.assertTrue(report.deterministic)
        self.assertFalse(report.void)


if __name__ == "__main__":
    unittest.main()
