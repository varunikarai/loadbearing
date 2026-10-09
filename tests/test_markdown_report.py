import unittest
from pathlib import Path

from loadbearing import report as report_json
from loadbearing.backends.local import LocalBackend
from loadbearing.markdown_report import render_markdown
from loadbearing.probe import probe
from loadbearing.prove import Pinned, close_loop
from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class MarkdownReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fakes import FakeRouter

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
        cls.plain = render_markdown(report_json.to_dict(before))
        cls.full = render_markdown(report_json.to_dict(before, loop, target))

    def test_heading_table_and_defect_lines(self):
        self.assertIn("### Loadbearing · `ticket-triage`: 2 defects", self.plain)
        self.assertIn("| `body` | yes | same | same | same | 🔴 **silent passthrough** |", self.plain)
        self.assertIn("- **`submitted_at`**, phantom sensitivity:", self.plain)

    def test_proofs_show_their_status_and_a_folded_diff(self):
        self.assertIn("**Fix for `body`:** ✅ proven: the defect is gone and no other field gained one.", self.full)
        self.assertIn("```diff", self.full)
        self.assertIn("No fix applied for `submitted_at`", self.full)

    def test_table_cells_cannot_break_the_table(self):
        data = report_json.to_dict(probe(load_target(EXAMPLE), LocalBackend()))
        data["verdicts"][0]["field"] = "a|b`c"
        self.assertIn("`a\\|b'c`", render_markdown(data))

    def test_inferred_intent_and_evidence_are_shown(self):
        data = report_json.to_dict(probe(load_target(EXAMPLE), LocalBackend()))
        v = next(x for x in data["verdicts"] if x["field"] == "body")
        v.update(intent_source="inferred", evidence={"intent": "relevant", "quote": "Read the body.",
                                                     "url": "https://example.com/spec"})
        text = render_markdown(data)
        self.assertIn("| `body` | yes (from docs) |", text)
        self.assertIn("[https://example.com/spec](https://example.com/spec): “Read the body.”", text)


if __name__ == "__main__":
    unittest.main()
