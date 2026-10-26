"""Ultra reads numbered source, and every file:line it cites is checked against that source."""

import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest import mock

from fakes import FakeRouter
from loadbearing import citations
from loadbearing import report as report_json
from loadbearing.backends.local import LocalBackend
from loadbearing.cli import main
from loadbearing.probe import probe
from loadbearing.target import load_target

ROOT = Path(__file__).resolve().parent.parent
TRIAGE = ROOT / "examples" / "ticket_triage" / "target.json"
QUOTE = "    text = f\"{ticket.get('subject', '')} {ticket.get('bdoy', '')}\".lower()"


def explain_citing(line: int):
    return lambda v, source: f"The misspelled key is read at pipeline.py:{line}:\n\n{QUOTE}\n"


class CheckTests(unittest.TestCase):
    sources = {"pipeline.py": "import json\n\ndef run(r):\n    context = r.get('context', '')\n    return context\n"}

    def test_a_citation_of_the_quoted_line_holds(self):
        text = "pipeline.py:4 reads the wrong key:\n    context = r.get('context', '')"
        self.assertEqual(citations.check(text, self.sources), [])

    def test_a_wrong_number_says_what_is_there_and_where_the_quote_is(self):
        text = "pipeline.py:1 reads the wrong key:\n    context = r.get('context', '')"
        self.assertEqual(citations.check(text, self.sources), [
            "pipeline.py:1 is `import json`, which the explanation does not quote; "
            "the line it quotes from that file is at pipeline.py:4"])

    def test_a_blank_line_or_one_past_the_end_is_named_as_such(self):
        notes = citations.check("See pipeline.py:2 and pipeline.py:40.", self.sources)
        self.assertEqual(notes, ["pipeline.py:2 is a blank line",
                                 "pipeline.py:40 is past the end of the file, which has 5 lines"])

    def test_a_path_that_is_not_a_source_is_left_alone(self):
        self.assertEqual(citations.check("Docs at https://example.com:443 and lib/other.py:9.", self.sources), [])

    def test_a_citation_by_file_name_matches_a_source_in_a_folder(self):
        sources = {"app/pipeline.py": self.sources["pipeline.py"]}
        self.assertEqual(len(citations.check("pipeline.py:1 is the problem", sources)), 1)

    def test_numbered_source_carries_the_numbers_a_citation_should_use(self):
        text = citations.numbered(self.sources)
        self.assertTrue(text.startswith("--- pipeline.py\n1| import json\n2| \n"))
        self.assertIn("4|     context = r.get('context', '')", text)


class RecordedRunTests(unittest.TestCase):
    def test_the_recorded_support_answerer_explanation_is_caught_citing_the_wrong_line(self):
        run = json.loads((ROOT / "demo" / "runs" / "support_answerer.sandbox.json").read_text())
        explanation = next(v["explanation"] for v in run["verdicts"] if v["field"] == "passages")
        source = (ROOT / "examples" / "support_answerer" / "pipeline.py").read_text()
        notes = citations.check(explanation, {"pipeline.py": source})
        self.assertEqual(len(notes), 1)
        self.assertTrue(notes[0].startswith("pipeline.py:18 is `import re`"), notes)
        self.assertTrue(notes[0].endswith("is at pipeline.py:37"), notes)


class ProbeTests(unittest.TestCase):
    def run_probe(self, router):
        backend = LocalBackend()
        try:
            return probe(load_target(TRIAGE), backend, explain_with=router)
        finally:
            backend.close()

    def test_ultra_reads_numbered_source_and_a_true_citation_leaves_no_note(self):
        router = FakeRouter(reconcile="it never moved", explain=explain_citing(23))
        report = self.run_probe(router)
        source = next(args[1] for name, args in router.calls if name == "explain")
        self.assertIn("23| " + QUOTE, source)
        body = next(v for v in report.verdicts if v.field == "body")
        self.assertEqual(body.citations, [])

    def test_a_false_citation_is_kept_in_the_report_next_to_the_explanation(self):
        report = self.run_probe(FakeRouter(reconcile="it never moved", explain=explain_citing(3)))
        body = next(v for v in report_json.to_dict(report)["verdicts"] if v["field"] == "body")
        self.assertEqual(len(body["citations"]), 1)
        self.assertIn("is at pipeline.py:23", body["citations"][0])

    def test_a_field_with_no_defect_is_never_checked(self):
        report = self.run_probe(FakeRouter(reconcile="it never moved", explain=explain_citing(3)))
        subject = next(v for v in report.verdicts if v.field == "subject")
        self.assertIsNone(subject.citations)


class CliTests(unittest.TestCase):
    def test_the_check_is_printed_under_ultra(self):
        from loadbearing.nemotron import NemotronRouter

        out = io.StringIO()
        fake = FakeRouter(reconcile="Super: it never moved.", explain=explain_citing(3))
        with mock.patch.object(NemotronRouter, "from_env", return_value=fake), contextlib.redirect_stdout(out):
            main(["probe", str(TRIAGE), "--explain"])
        self.assertIn("  check:  pipeline.py:3 is", out.getvalue())


if __name__ == "__main__":
    unittest.main()
