import json
import tempfile
import unittest
from pathlib import Path

from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class TargetV2Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "record.json").write_text('{"a": 1}')
        (self.root / "pipeline.py").write_text("print('{}')")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, **keys):
        spec = {"command": "python3 pipeline.py input.json", "record": "record.json",
                "files": ["pipeline.py"], **keys}
        path = self.root / "target.json"
        path.write_text(json.dumps(spec))
        return path

    def test_a_v1_target_loads_with_the_v2_defaults(self):
        t = load_target(EXAMPLE)
        self.assertEqual(t.baseline_runs, 2)
        self.assertEqual(t.env, [])
        self.assertIsNone(t.docs)
        self.assertEqual(t.sources, t.files)

    def test_every_v2_key_is_read(self):
        t = load_target(self.write(
            baseline_runs=5,
            env=["NEBIUS_API_KEY"],
            docs={"query": "what does triage read", "urls": ["https://example.com"]},
            sources=["pipeline.py"],
        ))
        self.assertEqual(t.baseline_runs, 5)
        self.assertEqual(t.env, ["NEBIUS_API_KEY"])
        self.assertEqual(t.docs["urls"], ["https://example.com"])
        self.assertEqual(t.sources, ["pipeline.py"])

    def test_bad_values_are_named_at_load_time(self):
        cases = [
            ({"baseline_runs": 1}, "baseline_runs"),
            ({"baseline_runs": True}, "baseline_runs"),
            ({"env": [""]}, "env"),
            ({"docs": {"query": 3}}, "docs"),
            ({"docs": {"query": "q", "urls": [1]}}, "docs.urls"),
            ({"sources": ["../escape.py"]}, "source"),
            ({"sources": ["missing.py"]}, "source"),
        ]
        for keys, word in cases:
            with self.subTest(keys=keys), self.assertRaisesRegex(RuntimeError, word):
                load_target(self.write(**keys))

    def test_an_expects_name_that_is_not_in_the_record_is_refused(self):
        (self.root / "record.json").write_text('{"body": "outage", "customer": {"tier": "pro"}}')
        with self.assertRaisesRegex(RuntimeError, "expects.relevant names 'boddy'"):
            load_target(self.write(expects={"relevant": ["boddy"]}))
        # A parent path covers what is nested under it.
        load_target(self.write(expects={"relevant": ["body", "customer"], "irrelevant": ["customer.tier"]}))

    def test_a_record_that_is_not_an_object_or_has_a_dotted_key_is_refused(self):
        for record, word in (("[1, 2]", "JSON object"), ('{"http.method": "GET"}', "contains a dot")):
            (self.root / "record.json").write_text(record)
            with self.subTest(record=record), self.assertRaisesRegex(RuntimeError, word):
                load_target(self.write())


if __name__ == "__main__":
    unittest.main()
