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
        # Links a reader can click are fine; nothing may load on its own.
        self.assertNotIn("<script", self.page)
        self.assertNotIn("<link", self.page)
        self.assertNotIn("src=", self.page)
        self.assertNotIn("@import", self.page)

    def test_pipeline_output_is_escaped(self):
        hostile = dict(self.data)
        hostile["baseline"] = dict(self.data["baseline"], output={"x": "<script>alert(1)</script>"})
        hostile["target"] = "<img src=x onerror=alert(1)>"
        page = render_html(hostile)
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;", page)

    def test_a_card_says_when_the_intent_came_from_docs_not_a_declaration(self):
        inferred = dict(self.data)
        inferred["verdicts"] = [
            dict(v, intent_source="inferred") if v["field"] == "body" else v for v in self.data["verdicts"]
        ]
        page = render_html(inferred)
        self.assertIn("Not declared, but its docs say it is an input that should change the output", page)
        self.assertIn("Declared as an input that should not matter", page)

    def test_a_clean_run_says_so(self):
        clean = dict(self.data, defects=[])
        clean["verdicts"] = [dict(v, defect=False, verdict="inert") for v in self.data["verdicts"]]
        self.assertIn("Every declared input does what the pipeline claims", render_html(clean))



class HtmlReportV2Tests(unittest.TestCase):
    """The schema 2 panels: noise floor, model text, evidence, and the proven fix."""

    @classmethod
    def setUpClass(cls):
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
        cls.data = report_json.to_dict(before, loop, target)
        body = next(v for v in cls.data["verdicts"] if v["field"] == "body")
        body.update(
            reconciliation="Super says <b>no</b>.",
            explanation="Ultra says the key is misspelled.",
            evidence={"intent": "relevant", "quote": "Priority comes from the body.",
                      "url": "https://example.com/spec?a=1&b=2"},
        )
        cls.page = render_html(cls.data)

    def test_the_proven_fix_is_shown_with_its_diff_and_verdict_change(self):
        self.assertIn("The fix, proven", self.page)
        self.assertIn("body · fixed by Nemotron Ultra", self.page)
        self.assertIn('<div class="add">', self.page)
        self.assertIn('<div class="del">', self.page)
        self.assertIn("the defect is gone, and no other field gained one", self.page)
        self.assertIn("1/2</div>", self.page)

    def test_a_refused_fix_is_listed_with_its_reason(self):
        self.assertIn("No fix applied for <b>submitted_at</b>", self.page)

    def test_model_text_and_evidence_are_escaped_and_linked(self):
        self.assertIn("NEMOTRON SUPER", self.page)
        self.assertIn("Super says &lt;b&gt;no&lt;/b&gt;.", self.page)
        self.assertIn("NEMOTRON ULTRA", self.page)
        self.assertIn('href="https://example.com/spec?a=1&amp;b=2"', self.page)

    def test_the_noise_floor_is_explained_not_called_unsound(self):
        noisy = dict(self.data, unstable_keys=["answer"], baseline_runs=5, void=False)
        page = render_html(noisy)
        self.assertIn("ran <b>5</b> times", page)
        self.assertNotIn('class="warn"', page)
        self.assertIn('class="warn"', render_html(dict(noisy, void=True)))



class ProseTests(unittest.TestCase):
    """Model prose arrives as markdown; it is shown formatted, and never as live HTML."""

    def test_bold_code_and_fences_are_formatted(self):
        from loadbearing.html_report import _prose

        html = _prose("**Why:** `build_prompt` reads it.\n\n```python\nx = r.get('context')\n```")
        self.assertIn("<b>Why:</b> <code>build_prompt</code>", html)
        self.assertIn('<pre class="code">x = r.get(&#x27;context&#x27;)</pre>', html)
        self.assertNotIn("```", html)
        self.assertNotIn("**", html)

    def test_a_fence_cut_off_at_the_length_limit_is_still_code(self):
        from loadbearing.html_report import _prose

        html = _prose("A fix:\n```python\nx = r.get('passages')\n```\n\nOr:\n```python\nctx = join(x) if")
        self.assertIn('<pre class="code">ctx = join(x) if</pre>', html)
        self.assertNotIn("```", html)

    def test_markup_in_model_text_stays_escaped(self):
        from loadbearing.html_report import _prose

        html = _prose('**<img src=x onerror=alert(1)>** `<script>` ```\n<b>no</b>\n```')
        self.assertNotIn("<img", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;b&gt;no&lt;/b&gt;", html)


if __name__ == "__main__":
    unittest.main()
