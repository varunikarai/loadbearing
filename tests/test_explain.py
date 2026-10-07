"""--explain: Super and Ultra speak only about defects, and Ultra reads the real source."""

import unittest
from pathlib import Path

from fakes import FakeRouter
from loadbearing.backends.local import LocalBackend
from loadbearing.probe import probe
from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


def run_probe(**kwargs):
    backend = LocalBackend()
    try:
        return probe(load_target(EXAMPLE), backend, **kwargs)
    finally:
        backend.close()


class ExplainTests(unittest.TestCase):
    def setUp(self):
        self.router = FakeRouter(
            reconcile=lambda v: f"{v.field}: {v.verdict}",
            explain=lambda v, source: f"{v.field} explained from {len(source)} chars",
        )
        self.report = run_probe(explain_with=self.router)
        self.by_field = {v.field: v for v in self.report.verdicts}

    def test_every_defect_gets_a_statement_and_an_explanation(self):
        for field in ("body", "submitted_at"):
            verdict = self.by_field[field]
            self.assertEqual(verdict.reconciliation, f"{field}: {verdict.verdict}")
            self.assertTrue(verdict.explanation.startswith(f"{field} explained"))

    def test_fields_without_a_defect_cost_no_calls(self):
        for field in ("ticket_id", "customer_tier", "subject"):
            self.assertIsNone(self.by_field[field].reconciliation)
            self.assertIsNone(self.by_field[field].explanation)
        self.assertEqual(len(self.router.calls), 4)  # two defects, two calls each

    def test_ultra_reads_the_pipeline_source(self):
        source = next(args[1] for name, args in self.router.calls if name == "explain")
        self.assertIn("--- pipeline.py", source)
        self.assertIn("bdoy", source)

    def test_without_a_router_nothing_is_explained(self):
        report = run_probe()
        self.assertTrue(all(v.explanation is None and v.reconciliation is None for v in report.verdicts))


if __name__ == "__main__":
    unittest.main()
