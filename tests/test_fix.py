import unittest
from pathlib import Path

from loadbearing.fix import Fix
from loadbearing.target import load_target
from loadbearing.verdict import SILENT_PASSTHROUGH

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


if __name__ == "__main__":
    unittest.main()
