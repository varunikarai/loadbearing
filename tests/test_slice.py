"""The vertical slice, end to end on the local backend: both planted bugs must be caught."""

import unittest
from pathlib import Path

from loadbearing.backends.local import LocalBackend
from loadbearing.probe import probe
from loadbearing.target import load_target
from loadbearing.verdict import INERT, LOAD_BEARING, PHANTOM_SENSITIVITY, SILENT_PASSTHROUGH

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class TicketTriageSlice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        backend = LocalBackend()
        try:
            cls.report = probe(load_target(EXAMPLE), backend)
        finally:
            backend.close()

    def test_baseline_is_deterministic(self):
        self.assertTrue(self.report.deterministic)

    def test_the_pipeline_really_is_wrong(self):
        # The body reports a full outage and the pipeline still says P3.
        self.assertEqual(self.report.baseline.output()["priority"], "P3")

    def test_every_field_gets_the_right_verdict(self):
        verdicts = {v.field: v.verdict for v in self.report.verdicts}
        self.assertEqual(
            verdicts,
            {
                "ticket_id": INERT,
                "submitted_at": PHANTOM_SENSITIVITY,
                "customer_tier": LOAD_BEARING,
                "subject": LOAD_BEARING,
                "body": SILENT_PASSTHROUGH,
            },
        )


if __name__ == "__main__":
    unittest.main()
