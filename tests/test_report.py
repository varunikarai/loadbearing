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
            for old in (0, 1):
                path.write_text(json.dumps(dict(self.data, schema=old)))
                with self.subTest(schema=old), self.assertRaises(RuntimeError):
                    report_json.load(path)

    def test_schema_2_fields_are_present_and_empty_on_a_plain_probe(self):
        self.assertEqual(self.data["schema"], 2)
        self.assertEqual(self.data["baseline_runs"], 2)
        self.assertEqual(self.data["unstable_keys"], [])
        self.assertFalse(self.data["void"])
        self.assertEqual((self.data["fixes"], self.data["proofs"], self.data["rejected_fixes"]), ([], [], []))
        body = next(v for v in self.data["verdicts"] if v["field"] == "body")
        self.assertEqual(body["intent_source"], "declared")
        self.assertIsNone(body["evidence"])
        self.assertIsNone(body["explanation"])


class LoopReportTests(unittest.TestCase):
    """A closed loop serialises its fix, diff and proof."""

    def test_fix_diff_and_proof_are_in_the_report(self):
        from fakes import FakeRouter
        from loadbearing.prove import Pinned, close_loop

        target = load_target(EXAMPLE)
        backend = LocalBackend()
        try:
            pinned = Pinned(backend)
            before = probe(target, pinned)
            ultra = FakeRouter(write_fix=lambda v, src: (
                ({"pipeline.py": src["pipeline.py"].replace("'bdoy'", "'body'")}, "Read the real key.")
                if v.field == "body" else ({"pipeline.py": "("}, "broken")))
            loop = close_loop(target, backend, before, ultra, checkpoint=pinned.pinned)
        finally:
            backend.close()
        data = json.loads(json.dumps(report_json.to_dict(before, loop, target)))
        (fix,) = data["fixes"]
        self.assertIn("-    text = f\"{ticket.get('subject', '')} {ticket.get('bdoy', '')}\".lower()", fix["diff"])
        (proof,) = data["proofs"]
        self.assertTrue(proof["clean"])
        self.assertEqual(proof["after"]["baseline"]["output"]["priority"], "P1")
        self.assertNotIn("fixes", proof["after"])
        self.assertEqual([r["field"] for r in data["rejected_fixes"]], ["submitted_at"])


if __name__ == "__main__":
    unittest.main()
