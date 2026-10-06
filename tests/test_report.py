import json
import tempfile
import unittest
from pathlib import Path

from loadbearing import report as report_json
from loadbearing.backends.local import LocalBackend
from loadbearing.probe import probe
from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class ReportJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        backend = LocalBackend()
        try:
            cls.report = probe(load_target(EXAMPLE), backend)
        finally:
            backend.close()
        cls.data = report_json.to_dict(cls.report)

    def test_it_is_plain_json(self):
        self.assertEqual(json.loads(json.dumps(self.data)), self.data)

    def test_each_fork_records_what_the_field_became(self):
        forks = {f["label"]: f for f in self.data["forks"]}
        self.assertEqual(forks["destroy:customer_tier"]["value"], "xxx")
        self.assertEqual(forks["nudge:submitted_at"]["value"], "2026-09-30T09:14:08+00:00")
        self.assertIsNone(forks["drop:body"]["value"])

    def test_the_evidence_for_each_defect_is_in_the_report(self):
        self.assertEqual(sorted(self.data["defects"]), ["body", "submitted_at"])
        nudged = next(f for f in self.data["forks"] if f["label"] == "nudge:submitted_at")
        self.assertTrue(nudged["moved"])
        self.assertEqual(nudged["changed"], ["queue"])

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            report_json.save(self.report, path)
            self.assertEqual(report_json.load(path), self.data)

    def test_an_old_schema_is_refused_not_misread(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(dict(self.data, schema=0)))
            with self.assertRaises(RuntimeError):
                report_json.load(path)


if __name__ == "__main__":
    unittest.main()
