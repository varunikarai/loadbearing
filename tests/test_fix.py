import unittest
from pathlib import Path

from fakes import FakeRouter
from loadbearing.backends.local import LocalBackend
from loadbearing.fix import Fix, FixRejected, validate, write_fix
from loadbearing.probe import probe
from loadbearing.prove import Pinned, prove
from loadbearing.target import load_target
from loadbearing.verdict import INERT, LOAD_BEARING, RELEVANT, SILENT_PASSTHROUGH, FieldVerdict

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


def body_fix(target) -> Fix:
    """The real fix for the toy target's planted bug: read the body under its actual key."""
    source = (target.root / "pipeline.py").read_text()
    return Fix(
        field="body",
        defect=SILENT_PASSTHROUGH,
        files={"pipeline.py": source.replace("ticket.get('bdoy', '')", "ticket.get('body', '')")},
        rationale="The body is read under a misspelled key, so it never reaches the priority rule.",
    )


class FixTests(unittest.TestCase):
    def setUp(self):
        self.target = load_target(EXAMPLE)

    def test_diff_shows_only_the_changed_line(self):
        diff = body_fix(self.target).diff(self.target)
        removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
        added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        self.assertEqual(len(removed), 1)
        self.assertEqual(len(added), 1)
        self.assertIn("bdoy", removed[0])
        self.assertIn("'body'", added[0])
        self.assertIn("a/pipeline.py", diff)

    def test_unchanged_content_has_an_empty_diff(self):
        source = (self.target.root / "pipeline.py").read_text()
        fix = Fix("body", SILENT_PASSTHROUGH, {"pipeline.py": source}, "no-op")
        self.assertEqual(fix.diff(self.target), "")

    def test_a_new_file_diffs_as_all_added(self):
        fix = Fix("body", SILENT_PASSTHROUGH, {"helpers.py": "X = 1\n"}, "new helper")
        diff = fix.diff(self.target)
        self.assertIn("+X = 1", diff)
        self.assertFalse([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")])

    def test_the_fix_never_touches_the_original_file(self):
        before = (self.target.root / "pipeline.py").read_text()
        body_fix(self.target).diff(self.target)
        self.assertEqual((self.target.root / "pipeline.py").read_text(), before)


def ultra_fixing_body(verdict, sources):
    """Stands in for Ultra: returns the real fix for the toy target's body defect."""
    fixed = sources["pipeline.py"].replace("ticket.get('bdoy', '')", "ticket.get('body', '')")
    return {"pipeline.py": fixed}, "The body is read under a misspelled key."


BODY_DEFECT = FieldVerdict("body", RELEVANT, {"destroy": False}, SILENT_PASSTHROUGH)


class WriteFixTests(unittest.TestCase):
    def setUp(self):
        self.target = load_target(EXAMPLE)
        self.sources = {"pipeline.py": (self.target.root / "pipeline.py").read_text()}

    def test_writes_a_valid_fix_through_the_router(self):
        fix = write_fix(BODY_DEFECT, self.target, FakeRouter(write_fix=ultra_fixing_body))
        self.assertEqual((fix.field, fix.defect), ("body", SILENT_PASSTHROUGH))
        self.assertIn("ticket.get('body', '')", fix.files["pipeline.py"])

    def test_the_router_sees_every_source_file(self):
        router = FakeRouter(write_fix=ultra_fixing_body)
        write_fix(BODY_DEFECT, self.target, router)
        _, (verdict, sources) = router.calls[0]
        self.assertEqual(set(sources), set(self.target.sources))

    def test_a_field_without_a_defect_is_not_fixed(self):
        fine = FieldVerdict("subject", RELEVANT, {"destroy": True}, LOAD_BEARING)
        with self.assertRaises(ValueError):
            write_fix(fine, self.target, FakeRouter(write_fix=ultra_fixing_body))

    def test_refuses_a_file_outside_the_sources(self):
        with self.assertRaises(FixRejected):
            validate(Fix("body", SILENT_PASSTHROUGH, {"other.py": "x = 1\n"}, "r"), self.sources)

    def test_refuses_a_fix_that_changes_nothing(self):
        with self.assertRaises(FixRejected):
            validate(Fix("body", SILENT_PASSTHROUGH, dict(self.sources), "r"), self.sources)

    def test_refuses_python_that_no_longer_compiles(self):
        broken = self.sources["pipeline.py"].replace("def triage(", "def triage((")
        with self.assertRaises(FixRejected):
            validate(Fix("body", SILENT_PASSTHROUGH, {"pipeline.py": broken}, "r"), self.sources)

    def test_refuses_a_rewrite_of_most_of_the_file(self):
        rewrite = "import json\nprint(json.dumps({'priority': 'P1'}))\n"
        with self.assertRaises(FixRejected):
            validate(Fix("body", SILENT_PASSTHROUGH, {"pipeline.py": rewrite}, "r"), self.sources)


class LoopTests(unittest.TestCase):
    """Find, fix, prove, end to end and offline: the claim the demo makes."""

    def test_the_fixed_field_stops_being_a_defect_and_nothing_new_breaks(self):
        target = load_target(EXAMPLE)
        backend = LocalBackend()
        try:
            checkpoint = backend.checkpoint(target)
            before = probe(target, Pinned(backend, checkpoint))
            defect = next(v for v in before.defects if v.field == "body")
            fix = write_fix(defect, target, FakeRouter(write_fix=ultra_fixing_body))
            proof = prove(target, backend, fix, before, checkpoint=checkpoint)
        finally:
            backend.close()
        after = {v.field: v.verdict for v in proof.after.verdicts}
        self.assertTrue(proof.clean)
        self.assertEqual(after["body"], LOAD_BEARING)
        self.assertEqual(after["ticket_id"], INERT)
        self.assertEqual(proof.after.baseline.output()["priority"], "P1")


if __name__ == "__main__":
    unittest.main()
