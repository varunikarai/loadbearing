import unittest
from pathlib import Path

from loadbearing import report as report_json
from loadbearing.backends.local import LocalBackend
from loadbearing.html_report import fork_tree_svg, render_html
from loadbearing.probe import probe
from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class HtmlReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        backend = LocalBackend()
        try:
            cls.data = report_json.to_dict(probe(load_target(EXAMPLE), backend))
        finally:
            backend.close()
        cls.page = render_html(cls.data)

    def test_the_page_names_both_defects_and_their_evidence(self):
        self.assertIn("2 inputs</span> do not do", self.page)
        self.assertIn("body · silent passthrough", self.page)
        self.assertIn("submitted_at · phantom sensitivity", self.page)
        # The phantom card says which output key moved.
        self.assertIn("and queue changed", self.page)

    def test_the_tree_draws_one_line_per_fork(self):
        svg = fork_tree_svg(self.data)
        self.assertEqual(svg.count("<path "), len(self.data["forks"]))

    def test_the_page_fetches_nothing(self):
        self.assertNotIn("<script", self.page)
        self.assertNotIn("http://", self.page)
        self.assertNotIn("https://", self.page)

    def test_pipeline_output_is_escaped(self):
        hostile = dict(self.data)
        hostile["baseline"] = dict(self.data["baseline"], output={"x": "<script>alert(1)</script>"})
        hostile["target"] = "<img src=x onerror=alert(1)>"
        page = render_html(hostile)
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;", page)

    def test_a_clean_run_says_so(self):
        clean = dict(self.data, defects=[])
        clean["verdicts"] = [dict(v, defect=False, verdict="inert") for v in self.data["verdicts"]]
        self.assertIn("Every declared input does what the pipeline claims", render_html(clean))


if __name__ == "__main__":
    unittest.main()
