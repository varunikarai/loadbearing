import json
import unittest

from fakes import MODELS, router
from loadbearing.nemotron import _strip_reasoning
from loadbearing.verdict import RELEVANT, SILENT_PASSTHROUGH, Evidence, FieldVerdict

VERDICT = FieldVerdict(
    "body",
    RELEVANT,
    {"destroy": False, "drop": False, "nudge": False},
    SILENT_PASSTHROUGH,
    explanation="The body is read under the key 'bdoy'.",
    evidence=Evidence(RELEVANT, "Priority comes from the body.", "https://example.org/spec"),
)
SOURCES = {"pipeline.py": "text = ticket.get('bdoy', '')\n"}
FIXED = {"pipeline.py": "text = ticket.get('body', '')\n"}
EDIT = {"path": "pipeline.py", "old": "'bdoy'", "new": "'body'"}


class WriteFixTests(unittest.TestCase):
    def test_parses_a_fenced_reply_and_asks_ultra(self):
        reply = "```json\n" + json.dumps({"rationale": "misspelled key", "edits": [EDIT]}) + "\n```"
        r, client = router({"ultra": reply})
        files, rationale = r.write_fix(VERDICT, SOURCES)
        self.assertEqual(files, FIXED)
        self.assertEqual(rationale, "misspelled key")
        model, messages = client.calls[0]
        self.assertEqual(model, MODELS["ultra"])

    def test_the_prompt_carries_the_defect_the_why_the_evidence_and_the_source(self):
        r, client = router({"ultra": json.dumps({"rationale": "r", "edits": [EDIT]})})
        r.write_fix(VERDICT, SOURCES)
        prompt = client.calls[0][1][1]["content"]
        for expected in ("silent passthrough", "'body'", "bdoy", "https://example.org/spec", "--- pipeline.py"):
            self.assertIn(expected, prompt)

    def test_lines_ultra_never_quoted_are_left_exactly_as_they_were(self):
        sources = {"pipeline.py": 'TRACE = r"<think>.*?</think>"\ntext = ticket.get(\'bdoy\', \'\')'}
        reply = "<think>quote only the key</think>" + json.dumps({"rationale": "r", "edits": [EDIT]})
        r, _ = router({"ultra": reply})
        files, _ = r.write_fix(VERDICT, sources)
        self.assertEqual(files, {"pipeline.py": 'TRACE = r"<think>.*?</think>"\ntext = ticket.get(\'body\', \'\')'})

    def test_an_edit_whose_old_text_is_missing_or_repeated_is_refused(self):
        for old in ("'missing'", "", "ticket"):
            sources = {"pipeline.py": "ticket = load()\ntext = ticket.get('bdoy', '')\n"}
            r, _ = router({"ultra": json.dumps({"rationale": "r", "edits": [dict(EDIT, old=old)]})})
            with self.assertRaises(ValueError, msg=old):
                r.write_fix(VERDICT, sources)

    def test_an_edit_outside_the_sources_is_refused(self):
        r, _ = router({"ultra": json.dumps({"rationale": "r", "edits": [dict(EDIT, path="setup.py")]})})
        with self.assertRaises(ValueError):
            r.write_fix(VERDICT, SOURCES)

    def test_a_whole_file_reply_is_refused(self):
        r, _ = router({"ultra": json.dumps({"rationale": "r", "files": FIXED})})
        with self.assertRaises(ValueError):
            r.write_fix(VERDICT, SOURCES)

    def test_a_reply_without_edits_is_refused(self):
        r, _ = router({"ultra": json.dumps({"rationale": "r"})})
        with self.assertRaises(ValueError):
            r.write_fix(VERDICT, SOURCES)

    def test_a_reply_with_no_json_is_refused(self):
        r, _ = router({"ultra": "I would change the key."})
        with self.assertRaises(ValueError):
            r.write_fix(VERDICT, SOURCES)



class ReasoningTests(unittest.TestCase):
    def test_reasoning_never_reaches_the_answer(self):
        cases = {
            "<think>weigh it</think>noise": "noise",
            "the template opened it</think>\nmeaningful": "meaningful",
            "noise<think>cut off before the end": "noise",
            "  meaningful  ": "meaningful",
            '<think>t</think>{"old": "r\\"<think>.*?</think>\\""}': '{"old": "r\\"<think>.*?</think>\\""}',
            '{"new": "strip <think>x</think> here"}': '{"new": "strip <think>x</think> here"}',
            '{"old": "rsplit(\\"</think>\\", 1)"}': '{"old": "rsplit(\\"</think>\\", 1)"}',
            '{"new": "split(\\"<think>\\", 1)[0]"}': '{"new": "split(\\"<think>\\", 1)[0]"}',
            '```json\n{"old": "a</think>"}\n```': '```json\n{"old": "a</think>"}\n```',
            'the template opened it</think>{"old": "a</think>"}': '{"old": "a</think>"}',
            '{"a": 1}<think>cut off before the end': '{"a": 1}',
        }
        for raw, answer in cases.items():
            self.assertEqual(_strip_reasoning(raw), answer, raw)


class Excerpt:
    def __init__(self, url, content):
        self.url, self.content, self.title = url, content, ""


class InferIntentTests(unittest.TestCase):
    EXCERPTS = [Excerpt("https://example.org/rag", "Answers must be grounded in the retrieved passages.")]

    def reply(self, fields):
        return json.dumps({"fields": fields})

    def test_keeps_relevant_and_irrelevant_and_drops_unknown(self):
        r, _ = router({"super": self.reply({
            "passages": {"intent": "relevant", "quote": "Answers must be grounded in the retrieved passages.", "url": "https://example.org/rag"},
            "user_id": {"intent": "irrelevant", "quote": "q", "url": "u"},
            "request_ts": {"intent": "unknown", "quote": "", "url": ""},
        })})
        out = r.infer_intent(["passages", "user_id", "request_ts"], self.EXCERPTS)
        self.assertEqual(sorted(out), ["passages", "user_id"])
        self.assertEqual(out["passages"].intent, RELEVANT)
        self.assertEqual(out["passages"].url, "https://example.org/rag")

    def test_the_prompt_carries_fields_values_and_excerpts_and_goes_to_super(self):
        r, client = router({"super": self.reply({})})
        r.infer_intent(["user_id"], self.EXCERPTS, record={"user_id": "u-42"})
        model, messages = client.calls[0]
        self.assertEqual(model, MODELS["super"])
        prompt = messages[1]["content"]
        for expected in ("user_id", "u-42", "https://example.org/rag", "grounded in the retrieved"):
            self.assertIn(expected, prompt)

    def test_a_reply_without_fields_is_refused(self):
        r, _ = router({"super": json.dumps({"answer": "both matter"})})
        with self.assertRaises(ValueError):
            r.infer_intent(["user_id"], self.EXCERPTS)

if __name__ == "__main__":
    unittest.main()
