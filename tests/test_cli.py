import contextlib
import io
import unittest
from pathlib import Path

from loadbearing.cli import NOT_BUILT, main

EXAMPLE = str(Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json")


class ReservedFlagTests(unittest.TestCase):
    def test_each_reserved_flag_says_it_is_not_built_and_runs_nothing(self):
        flags = {"baseline_runs": ["--baseline-runs", "5"], "explain": ["--explain"],
                 "intent": ["--intent"], "fix": ["--fix"], "prove": ["--prove"]}
        for name in NOT_BUILT:
            err = io.StringIO()
            with self.subTest(flag=name), contextlib.redirect_stderr(err):
                self.assertEqual(main(["probe", EXAMPLE, *flags[name]]), 2)
                self.assertIn("not built yet", err.getvalue())

    def test_a_plain_probe_still_runs(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["probe", EXAMPLE]), 1)  # two defects


if __name__ == "__main__":
    unittest.main()
