import unittest

from loadbearing.mutations import DESTROY, DROP, NUDGE, Mutation, destroy, nudge, plan

RECORD = {
    "id": "T-1",
    "at": "2026-09-30T09:14:07Z",
    "count": 3,
    "urgent": True,
    "customer": {"tier": "pro", "tags": ["a"]},
}


class MutationTests(unittest.TestCase):
    def test_apply_never_touches_the_original(self):
        before = repr(RECORD)
        Mutation(DESTROY, "customer.tier").apply(RECORD)
        Mutation(DROP, "id").apply(RECORD)
        self.assertEqual(repr(RECORD), before)

    def test_destroy_keeps_type_and_length(self):
        self.assertEqual(destroy("pro"), "xxx")
        self.assertEqual(destroy(""), "x")
        self.assertEqual(destroy(5), 0)
        self.assertEqual(destroy(0), 1)
        self.assertIs(destroy(True), False)
        self.assertEqual(destroy(["a"]), [])

    def test_destroy_always_changes_the_value_even_when_it_is_empty(self):
        for value in ([], {}, "", 0, 0.0, False, None, ["a"], {"k": 1}):
            self.assertNotEqual(destroy(value), value, repr(value))

    def test_drop_removes_only_that_field(self):
        out = Mutation(DROP, "customer.tier").apply(RECORD)
        self.assertNotIn("tier", out["customer"])
        self.assertEqual(out["customer"]["tags"], ["a"])

    def test_nudge_moves_a_timestamp_by_one_second_and_keeps_its_format(self):
        self.assertEqual(nudge("2026-09-30T09:14:07Z"), "2026-09-30T09:14:08Z")
        self.assertEqual(nudge("2026-09-30T09:14:59+00:00"), "2026-09-30T09:15:00+00:00")

    def test_nudge_on_plain_text_and_numbers(self):
        self.assertEqual(nudge("pro"), "pro ")
        self.assertEqual(nudge("2026-09-30"), "2026-09-30 ")
        self.assertEqual(nudge(3), 4)

    def test_plan_covers_every_leaf_and_skips_impossible_nudges(self):
        labels = {m.label for m in plan(RECORD)}
        self.assertIn("destroy:customer.tier", labels)
        self.assertIn("nudge:at", labels)
        self.assertIn("drop:customer.tags", labels)
        self.assertNotIn("nudge:urgent", labels)
        self.assertNotIn("nudge:customer.tags", labels)


if __name__ == "__main__":
    unittest.main()
