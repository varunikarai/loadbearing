import json
import unittest

from fakes import MODELS, router
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


class WriteFixTests(unittest.TestCase):
    def test_parses_a_fenced_reply_and_asks_ultra(self):
        reply = "```json\n" + json.dumps({"rationale": "misspelled key", "files": FIXED}) + "\n```"
        r, client = router({"ultra": reply})
        files, rationale = r.write_fix(VERDICT, SOURCES)
        self.assertEqual(files, FIXED)
        self.assertEqual(rationale, "misspelled key")
        model, messages = client.calls[0]
        self.assertEqual(model, MODELS["ultra"])

    def test_the_prompt_carries_the_defect_the_why_the_evidence_and_the_source(self):
        r, client = router({"ultra": json.dumps({"rationale": "r", "files": FIXED})})
        r.write_fix(VERDICT, SOURCES)
        prompt = client.calls[0][1][1]["content"]
        for expected in ("silent passthrough", "'body'", "bdoy", "https://example.org/spec", "--- pipeline.py"):
            self.assertIn(expected, prompt)

    def test_a_reply_without_files_is_refused(self):
        r, _ = router({"ultra": json.dumps({"rationale": "r"})})
        with self.assertRaises(ValueError):
            r.write_fix(VERDICT, SOURCES)

    def test_a_reply_with_no_json_is_refused(self):
        r, _ = router({"ultra": "I would change the key."})
        with self.assertRaises(ValueError):
            r.write_fix(VERDICT, SOURCES)


if __name__ == "__main__":
    unittest.main()
