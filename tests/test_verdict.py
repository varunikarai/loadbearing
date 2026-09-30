import unittest

from loadbearing.backends.base import RunResult
from loadbearing.compare import compare
from loadbearing.verdict import (
    INERT,
    IRRELEVANT,
    LOAD_BEARING,
    PHANTOM_SENSITIVITY,
    RELEVANT,
    SILENT_PASSTHROUGH,
    UNDECLARED,
    intent_of,
    judge,
)

SAME = {"destroy": False, "drop": False, "nudge": False}


class VerdictTests(unittest.TestCase):
    def test_relevant_field_that_never_moves_is_a_silent_passthrough(self):
        self.assertEqual(judge("body", RELEVANT, SAME).verdict, SILENT_PASSTHROUGH)

    def test_relevant_field_that_moves_is_load_bearing(self):
        moved = dict(SAME, destroy=True)
        self.assertEqual(judge("body", RELEVANT, moved).verdict, LOAD_BEARING)

    def test_irrelevant_field_that_moves_on_a_nudge_is_a_phantom_sensitivity(self):
        moved = dict(SAME, nudge=True)
        verdict = judge("submitted_at", IRRELEVANT, moved)
        self.assertEqual(verdict.verdict, PHANTOM_SENSITIVITY)
        self.assertTrue(verdict.defect)

    def test_irrelevant_field_that_never_moves_is_inert(self):
        self.assertEqual(judge("ticket_id", IRRELEVANT, SAME).verdict, INERT)

    def test_undeclared_fields_never_raise_a_defect(self):
        self.assertFalse(judge("x", UNDECLARED, SAME).defect)
        self.assertFalse(judge("x", UNDECLARED, dict(SAME, drop=True)).defect)

    def test_a_declared_parent_covers_nested_fields(self):
        expects = {"relevant": ["customer"], "irrelevant": []}
        self.assertEqual(intent_of("customer.tier", expects), RELEVANT)
        self.assertEqual(intent_of("customerx", expects), UNDECLARED)


class CompareTests(unittest.TestCase):
    def test_json_outputs_report_which_keys_changed(self):
        a = RunResult('{"p": "P1", "q": "a"}', "", 0)
        b = RunResult('{"p": "P3", "q": "a"}', "", 0)
        diff = compare(a, b)
        self.assertTrue(diff.moved)
        self.assertEqual(diff.changed, ["p"])

    def test_a_crash_counts_as_moved(self):
        self.assertEqual(compare(RunResult("{}", "", 0), RunResult("", "boom", 1)).changed, ["<exit>"])

    def test_stderr_alone_does_not_count(self):
        self.assertFalse(compare(RunResult("ok", "", 0), RunResult("ok", "warn", 0)).moved)


if __name__ == "__main__":
    unittest.main()
