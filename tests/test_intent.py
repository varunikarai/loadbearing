"""Intent inference: Tavily's docs turn an undeclared field into a checkable defect claim."""

import tempfile
import unittest
from pathlib import Path

from fakes import FakeRouter
from loadbearing.backends.local import LocalBackend
from loadbearing.intent import Excerpt, gather, infer_expects, quoted, undeclared_fields
from loadbearing.probe import probe
from loadbearing.target import load_target
from loadbearing.verdict import (
    INERT,
    INFERRED,
    IRRELEVANT,
    LOAD_BEARING,
    PHANTOM_SENSITIVITY,
    RELEVANT,
    UNDECLARED,
    Evidence,
)

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"
SPEC_URL = "https://example.org/triage-spec"
SPEC = (
    "Triage spec. Priority comes from the subject and the body.\n"
    "Routing depends only on the customer tier. The submission time and the ticket id are\n"
    "kept for audit and must not affect routing."
)
QUOTE = "The submission time and the ticket id are kept for audit and must not affect routing."
API_URL = "https://example.org/api"
API_PAGE = f"page at {API_URL}"


class FakeTavily:
    def __init__(self):
        self.searches, self.extracts = [], []

    def search(self, query):
        self.searches.append(query)
        return {"results": [{"url": SPEC_URL, "title": "Triage spec", "content": "snippet", "raw_content": SPEC}]}

    def extract(self, urls):
        self.extracts.append(urls)
        return {"results": [{"url": u, "raw_content": f"page at {u}"} for u in urls]}


def toy_with_two_undeclared_fields():
    """The toy target, with ticket_id and submitted_at left for the docs to settle."""
    target = load_target(EXAMPLE)
    target.expects = {"relevant": ["subject", "body", "customer_tier"], "irrelevant": []}
    target.docs = {"query": "ticket triage routing spec"}
    return target


def super_reading_the_spec(fields, excerpts, record):
    return {f: Evidence(IRRELEVANT, QUOTE, SPEC_URL) for f in fields}


class QuoteTests(unittest.TestCase):
    EXCERPTS = [Excerpt(SPEC_URL, "Triage spec", SPEC)]

    def test_a_real_quote_passes_even_across_a_line_break(self):
        self.assertTrue(quoted(Evidence(IRRELEVANT, QUOTE, SPEC_URL), self.EXCERPTS))

    def test_a_made_up_quote_fails(self):
        self.assertFalse(quoted(Evidence(IRRELEVANT, "Ticket ids are random.", SPEC_URL), self.EXCERPTS))

    def test_a_real_quote_under_the_wrong_url_fails(self):
        self.assertFalse(quoted(Evidence(IRRELEVANT, QUOTE, "https://elsewhere.example"), self.EXCERPTS))

    def test_an_empty_quote_fails(self):
        self.assertFalse(quoted(Evidence(IRRELEVANT, "", SPEC_URL), self.EXCERPTS))


class GatherTests(unittest.TestCase):
    def test_searches_the_query_extracts_the_urls_and_caches(self):
        target = toy_with_two_undeclared_fields()
        target.docs["urls"] = ["https://example.org/api"]
        tavily = FakeTavily()
        with tempfile.TemporaryDirectory() as runs:
            first = gather(target, tavily.search, tavily.extract, runs)
            second = gather(target, tavily.search, tavily.extract, runs)
        self.assertEqual([e.url for e in first], [SPEC_URL, "https://example.org/api"])
        self.assertEqual(first, second)
        self.assertEqual((len(tavily.searches), len(tavily.extracts)), (1, 1))


class InferExpectsTests(unittest.TestCase):
    def setUp(self):
        self.target = toy_with_two_undeclared_fields()
        self.tavily = FakeTavily()
        self.runs = tempfile.TemporaryDirectory()
        self.addCleanup(self.runs.cleanup)

    def infer(self, answer):
        router = FakeRouter(infer_intent=answer)
        result = infer_expects(self.target, router, self.tavily.search, self.tavily.extract, self.runs.name)
        return result, router

    def test_only_undeclared_fields_are_asked_about(self):
        self.assertEqual(undeclared_fields(self.target), ["ticket_id", "submitted_at"])

    def test_keeps_quoted_answers_and_drops_invented_ones(self):
        def answer(fields, excerpts, record):
            return {
                "ticket_id": Evidence(IRRELEVANT, QUOTE, SPEC_URL),
                "submitted_at": Evidence(IRRELEVANT, "Timestamps never matter.", SPEC_URL),
                "subject": Evidence(RELEVANT, QUOTE, SPEC_URL),
            }

        result, _ = self.infer(answer)
        self.assertEqual(list(result), ["ticket_id"])

    def test_a_second_run_reuses_the_cache_and_pays_nothing(self):
        self.infer(super_reading_the_spec)
        result, router = self.infer(super_reading_the_spec)
        self.assertEqual(sorted(result), ["submitted_at", "ticket_id"])
        self.assertEqual(router.calls, [])
        self.assertEqual(len(self.tavily.searches), 1)

    def test_the_targets_own_docs_are_quoted_before_a_search_hit(self):
        self.target.docs["urls"] = [API_URL]
        shown = []

        def answer(fields, excerpts, record):
            shown.append([e.url for e in excerpts])
            first = excerpts[0]
            return {f: Evidence(IRRELEVANT, first.content, first.url) for f in fields}

        result, _ = self.infer(answer)
        self.assertEqual(shown, [[API_URL]])
        self.assertEqual({e.url for e in result.values()}, {API_URL})

    def test_a_search_settles_only_what_the_own_docs_leave_open(self):
        self.target.docs["urls"] = [API_URL]
        asked = []

        def answer(fields, excerpts, record):
            asked.append((fields, [e.url for e in excerpts]))
            if excerpts[0].url == API_URL:
                return {"ticket_id": Evidence(IRRELEVANT, API_PAGE, API_URL)}
            return super_reading_the_spec(fields, excerpts, record)

        result, _ = self.infer(answer)
        self.assertEqual(asked, [(["ticket_id", "submitted_at"], [API_URL]), (["submitted_at"], [SPEC_URL])])
        self.assertEqual((result["ticket_id"].url, result["submitted_at"].url), (API_URL, SPEC_URL))

    def test_no_docs_means_no_calls(self):
        self.target.docs = None
        result, router = self.infer(super_reading_the_spec)
        self.assertEqual((result, router.calls), ({}, []))


class ProbeWithInferredIntentTests(unittest.TestCase):
    """The point of the Tavily call: an observation becomes a defect claim with a source."""

    def probe(self, inferred=None):
        backend = LocalBackend()
        try:
            report = probe(toy_with_two_undeclared_fields(), backend, inferred=inferred)
        finally:
            backend.close()
        return {v.field: v for v in report.verdicts}

    def test_undeclared_the_timestamp_is_only_an_observation(self):
        verdict = self.probe()["submitted_at"]
        self.assertEqual((verdict.verdict, verdict.intent_source), (LOAD_BEARING, UNDECLARED))
        self.assertFalse(verdict.defect)

    def test_with_the_docs_the_timestamp_is_a_cited_phantom_sensitivity(self):
        evidence = Evidence(IRRELEVANT, QUOTE, SPEC_URL)
        verdicts = self.probe({"submitted_at": evidence, "ticket_id": evidence})
        timestamp, ticket_id = verdicts["submitted_at"], verdicts["ticket_id"]
        self.assertEqual(timestamp.verdict, PHANTOM_SENSITIVITY)
        self.assertEqual((timestamp.intent_source, timestamp.evidence.url), (INFERRED, SPEC_URL))
        self.assertEqual((ticket_id.verdict, ticket_id.intent_source), (INERT, INFERRED))

    def test_a_declared_intent_always_wins(self):
        verdicts = self.probe({"body": Evidence(IRRELEVANT, QUOTE, SPEC_URL)})
        self.assertEqual(verdicts["body"].intent_source, "declared")
        self.assertIsNone(verdicts["body"].evidence)


if __name__ == "__main__":
    unittest.main()
