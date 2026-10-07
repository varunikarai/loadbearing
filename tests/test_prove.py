"""A4 on the toy target: the real body fix is proven, a bad fix is caught."""

import unittest
from pathlib import Path

from loadbearing.backends.local import LocalBackend
from loadbearing.fix import Fix
from loadbearing.probe import probe
from loadbearing.prove import Pinned, prove
from loadbearing.target import load_target
from loadbearing.verdict import LOAD_BEARING, PHANTOM_SENSITIVITY, SILENT_PASSTHROUGH

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


def _fix(target, new_source, rationale="test"):
    return Fix(field="body", defect=SILENT_PASSTHROUGH, files={"pipeline.py": new_source}, rationale=rationale)


class ProveTests(unittest.TestCase):
    def setUp(self):
        self.backend = LocalBackend()
        self.target = load_target(EXAMPLE)
        self.source = (self.target.root / "pipeline.py").read_text()
        # Probe once on a pinned checkpoint, so the proof derives from the exact same snapshot.
        self.checkpoint = self.backend.checkpoint(self.target)
        self.before = probe(self.target, Pinned(self.backend, self.checkpoint))

    def tearDown(self):
        self.backend.close()

    def verdicts(self, report):
        return {v.field: v.verdict for v in report.verdicts}

    def test_the_real_fix_removes_the_defect_and_nothing_else_changes(self):
        good = _fix(self.target, self.source.replace("ticket.get('bdoy', '')", "ticket.get('body', '')"))
        proof = prove(self.target, self.backend, good, self.before, checkpoint=self.checkpoint)
        self.assertTrue(proof.fixed)
        self.assertEqual(proof.new_defects, [])
        self.assertTrue(proof.clean)
        after = self.verdicts(proof.after)
        self.assertEqual(after["body"], LOAD_BEARING)
        # The other defect was not this fix's job, and it is still reported.
        self.assertEqual(after["submitted_at"], PHANTOM_SENSITIVITY)
        # And with the body read, the outage ticket is finally P1.
        self.assertEqual(proof.after.baseline.output()["priority"], "P1")

    def test_a_fix_that_breaks_another_field_is_caught(self):
        # Reads the body, but also leaks the ticket id into the summary.
        bad = _fix(self.target, self.source
                   .replace("ticket.get('bdoy', '')", "ticket.get('body', '')")
                   .replace('ticket.get("subject", "")[:48]', 'ticket["ticket_id"] + " " + ticket.get("subject", "")[:48]'))
        proof = prove(self.target, self.backend, bad, self.before, checkpoint=self.checkpoint)
        self.assertTrue(proof.fixed)
        self.assertEqual(proof.new_defects, ["ticket_id"])
        self.assertFalse(proof.clean)

    def test_a_fix_that_does_nothing_is_not_called_fixed(self):
        proof = prove(self.target, self.backend, _fix(self.target, self.source), self.before, checkpoint=self.checkpoint)
        self.assertFalse(proof.fixed)

    def test_the_original_checkpoint_is_never_changed(self):
        good = _fix(self.target, self.source.replace("bdoy", "body"))
        prove(self.target, self.backend, good, self.before, checkpoint=self.checkpoint)
        self.assertEqual((self.checkpoint / "pipeline.py").read_text(), self.source)

    def test_a_fix_may_only_write_the_target_sources(self):
        rogue = Fix(field="body", defect=SILENT_PASSTHROUGH, files={"other.py": "x"}, rationale="")
        with self.assertRaisesRegex(ValueError, "other.py"):
            prove(self.target, self.backend, rogue, self.before, checkpoint=self.checkpoint)

    def test_pinned_builds_its_checkpoint_once_and_times_the_real_build(self):
        pinned = Pinned(self.backend)
        first = probe(self.target, pinned)
        built = pinned.pinned
        probe(self.target, pinned)
        self.assertIs(pinned.pinned, built)
        self.assertGreater(first.checkpoint_seconds, 0)

    def test_without_a_checkpoint_it_builds_one_from_the_same_target(self):
        good = _fix(self.target, self.source.replace("bdoy", "body"))
        self.assertTrue(prove(self.target, self.backend, good, self.before).clean)


if __name__ == "__main__":
    unittest.main()
