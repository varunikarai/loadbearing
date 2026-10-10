import contextlib
import json
import io
import unittest
from unittest import mock
from pathlib import Path

from loadbearing.cli import NOT_BUILT, main

EXAMPLE = str(Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json")


class CrashExitTests(unittest.TestCase):
    """Exit 1 means defects were found; a crash must exit 2 so CI never reads it as a finding."""

    def run_quietly(self, argv):
        with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()):
            code = main(argv)
        return code, err.getvalue()

    def test_a_missing_target_file_exits_2(self):
        code, err = self.run_quietly(["probe", "/no/such/target.json"])
        self.assertEqual(code, 2)
        self.assertIn("Traceback", err)

    def test_a_target_without_command_exits_2(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "r.json").write_text("{}")
            Path(tmp, "target.json").write_text(json.dumps({"record": "r.json"}))
            self.assertEqual(self.run_quietly(["probe", str(Path(tmp, "target.json"))])[0], 2)


class ReservedFlagTests(unittest.TestCase):
    def test_each_reserved_flag_says_it_is_not_built_and_runs_nothing(self):
        flags = {"explain": ["--explain"],
                 "intent": ["--intent"], "fix": ["--fix"], "prove": ["--prove"]}
        for name in NOT_BUILT:
            err = io.StringIO()
            with self.subTest(flag=name), contextlib.redirect_stderr(err):
                self.assertEqual(main(["probe", EXAMPLE, *flags[name]]), 2)
                self.assertIn("not built yet", err.getvalue())

    def test_baseline_runs_reaches_the_probe(self):
        from loadbearing import cli

        with mock.patch.object(cli, "probe", wraps=cli.probe) as spy, \
                contextlib.redirect_stdout(io.StringIO()):
            main(["probe", EXAMPLE, "--baseline-runs", "4"])
        self.assertEqual(spy.call_args.kwargs["baseline_runs"], 4)

    def test_a_plain_probe_still_runs(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["probe", EXAMPLE]), 1)  # two defects



def _ultra(verdict, sources):
    if verdict.field == "body":
        return {"pipeline.py": sources["pipeline.py"].replace("'bdoy'", "'body'")}, "Read the body under its real key."
    return {"pipeline.py": "("}, "broken"


class LoopFlagTests(unittest.TestCase):
    def run_cli(self, *flags):
        from fakes import FakeRouter
        from loadbearing.nemotron import NemotronRouter

        out = io.StringIO()
        fake = FakeRouter(write_fix=_ultra, reconcile="Super: it never moved.",
                          explain="Ultra: read under a misspelled key.")
        with mock.patch.object(NemotronRouter, "from_env", return_value=fake) as built, \
                contextlib.redirect_stdout(out):
            code = main(["probe", EXAMPLE, *flags])
        self.tiers = built.call_args.kwargs["tiers"] if built.called else None
        return code, out.getvalue()

    def test_prove_prints_the_fix_its_diff_and_the_proof(self):
        code, text = self.run_cli("--prove")
        self.assertEqual(code, 1)  # the pipeline as given still has defects
        self.assertIn("fix for body (silent passthrough): Read the body under its real key.", text)
        self.assertIn("+++ b/pipeline.py", text)
        self.assertIn("proof: body is now load-bearing, and no other field gained a defect.", text)
        self.assertIn("no fix for submitted_at:", text)

    def test_fix_writes_without_proving(self):
        _, text = self.run_cli("--fix")
        self.assertIn("fix for body", text)
        self.assertNotIn("proof:", text)

    def test_fix_implies_explain_and_asks_for_exactly_the_tiers_it_uses(self):
        _, text = self.run_cli("--fix", "--json")
        body = next(v for v in json.loads(text)["verdicts"] if v["field"] == "body")
        self.assertEqual(body["explanation"], "Ultra: read under a misspelled key.")
        self.assertEqual(self.tiers, ("super", "ultra"))

    def test_explain_alone_annotates_defects_without_fixing(self):
        _, text = self.run_cli("--explain", "--json")
        data = json.loads(text)
        body = next(v for v in data["verdicts"] if v["field"] == "body")
        self.assertEqual(body["reconciliation"], "Super: it never moved.")
        self.assertEqual(data["fixes"], [])

    def test_explain_prints_super_and_ultra_under_each_defect(self):
        _, text = self.run_cli("--explain")
        self.assertIn("why body:\n  Super: Super: it never moved.\n  Ultra: Ultra: read under a misspelled key.", text)
        self.assertIn("why submitted_at:", text)
        self.assertNotIn("why subject:", text)  # a field that behaves needs no explaining

    def test_without_explain_no_why_is_printed(self):
        _, text = self.run_cli()
        self.assertNotIn("why ", text)

    def test_intent_feeds_inferred_intents_to_the_probe_and_the_proof(self):
        from loadbearing import cli
        from loadbearing.verdict import Evidence

        evidence = {"ticket_id": Evidence("irrelevant", "The id is for lookup only.", "https://x.test/spec")}
        with mock.patch("loadbearing.intent.infer_expects", return_value=evidence) as infer, \
                mock.patch.object(cli, "close_loop", wraps=cli.close_loop) as loop:
            self.run_cli("--intent", "--prove")
        infer.assert_called_once()
        self.assertIs(loop.call_args.kwargs["inferred"], evidence)
        self.assertEqual(self.tiers, ("super", "ultra"))

    def test_prove_lands_in_the_json(self):
        _, text = self.run_cli("--prove", "--json")
        data = json.loads(text)
        self.assertTrue(data["proofs"][0]["clean"])


class RenderTests(unittest.TestCase):
    def report(self, unstable, output='{"a": 1, "id": "x"}'):
        from loadbearing.backends.base import RunResult
        from loadbearing.probe import Report

        return Report(target="t", backend="local", deterministic=not unstable,
                      baseline=RunResult(output, "", 0), forks=[], verdicts=[],
                      baseline_runs=5, unstable_keys=unstable)

    def test_a_noisy_key_is_named_and_the_report_still_stands(self):
        from loadbearing.cli import render

        text = render(self.report(["id"]))
        self.assertIn("noise floor: 5 baseline runs; varies on its own, not judged: id", text)
        self.assertNotIn("WARNING", text)

    def test_only_a_void_report_is_called_unsound(self):
        from loadbearing.cli import render

        self.assertIn("WARNING", render(self.report(["a", "id"])))
        self.assertNotIn("WARNING", render(self.report([])))


if __name__ == "__main__":
    unittest.main()
