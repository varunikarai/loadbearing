"""V6: the pre-public audit finds what history hides, and passes a clean repository."""

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "audit.py"
spec = importlib.util.spec_from_file_location("audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
sys.modules["audit"] = audit  # dataclasses look their module up by name
spec.loader.exec_module(audit)

# Built at run time, so this file never holds a key-shaped string or a stray
# address, and the audit of this repository does not flag its own tests.
FAKE_KEY = "tvly-" + "a1b2" * 6
STRAY = "someone" + "@" + "mail.test"

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Builder", "GIT_AUTHOR_EMAIL": "builder@example.com",
    "GIT_COMMITTER_NAME": "Builder", "GIT_COMMITTER_EMAIL": "builder@example.com",
}


class AuditTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.commit("README.md", "a pipeline prober\n", "Start")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=ENV, check=True, capture_output=True)

    def commit(self, name, text, message):
        (self.repo / name).write_text(text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def kinds(self, words=()):
        findings, _ = audit.audit(self.repo, words=list(words))
        return {f.kind for f in findings}

    def test_a_clean_repository_is_a_go(self):
        findings, counts = audit.audit(self.repo)
        self.assertEqual(findings, [])
        self.assertEqual(counts["commits"], 1)

    def test_a_key_deleted_later_is_still_found(self):
        self.commit("config.py", f'KEY = "{FAKE_KEY}"\n', "Add config")
        self.commit("config.py", "KEY = None\n", "Remove the key")
        findings, _ = audit.audit(self.repo)
        self.assertEqual([f.kind for f in findings], ["Tavily key"])
        self.assertIn("config.py", findings[0].where)
        self.assertNotIn(FAKE_KEY, findings[0].text)  # the report never prints a whole key

    def test_a_key_in_a_commit_message_is_found(self):
        self.commit("notes.md", "notes\n", f"Try the key {FAKE_KEY}")
        self.assertEqual(self.kinds(), {"Tavily key"})

    def test_short_placeholders_and_known_fakes_pass(self):
        self.commit("test_x.py", 'KEY = "tvly-test"\nSECRET = "lb-secret-value-6f1c"\n', "Fakes")
        self.assertEqual(self.kinds(), set())

    def test_a_committed_env_file_is_found_but_the_example_is_not(self):
        self.commit(".env.example", "NEBIUS_API_KEY=\n", "Example env")
        self.assertEqual(self.kinds(), set())
        self.commit(".env", "NEBIUS_API_KEY=\n", "Oops")
        self.git("rm", "-q", "--cached", ".env")
        self.git("commit", "-q", "-m", "Untrack it")
        self.assertEqual(self.kinds(), {"secrets file committed"})

    def test_an_address_that_is_not_ours_is_found(self):
        self.commit("a.md", "mail builder@example.com or demo@example.org\n", "Ours and examples")
        self.assertEqual(self.kinds(), set())
        self.commit("b.md", f"mail {STRAY}\n", "A stranger")
        findings, _ = audit.audit(self.repo)
        self.assertEqual([(f.kind, f.text) for f in findings], [("email address", STRAY)])

    def test_a_trailer_is_found(self):
        self.commit("c.md", "c\n", "Change\n\nSigned-off-by: Other Person <other@example.com>")
        self.assertEqual(self.kinds(), {"trailer in a commit message"})

    def test_an_ordinary_word_ending_in_by_is_not_a_trailer(self):
        self.commit("d.md", "d\n", "Keep the server on stand-by: it is cheap")
        self.assertEqual(self.kinds(), set())

    def test_also_words_are_found_in_files_paths_messages_and_branches(self):
        self.assertEqual(self.kinds(["acme"]), set())
        self.commit("acme_notes.md", "nothing\n", "Notes")
        self.commit("plan.md", "built at Acme\n", "Plan for acme")
        self.git("branch", "acme-spike")
        findings, _ = audit.audit(self.repo, words=["ACME"])
        wheres = {f.where for f in findings}
        self.assertTrue(any(w.startswith("plan.md (") for w in wheres))  # a file's contents
        self.assertTrue(any(w.endswith(" message") for w in wheres))  # a commit message
        self.assertIn("a committed path", wheres)
        self.assertIn("a branch name", wheres)

    def test_main_exits_one_on_no_go_and_zero_on_go(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(audit.main(["--repo", str(self.repo)]), 0)
        self.assertIn("go: nothing found", out.getvalue())
        self.commit("config.py", f'KEY = "{FAKE_KEY}"\n', "Add config")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(audit.main(["--repo", str(self.repo)]), 1)
        self.assertIn("no-go: 1 finding(s)", out.getvalue())
        self.assertIn("identity, check it is meant to be public: Builder <builder@example.com>", out.getvalue())


if __name__ == "__main__":
    unittest.main()
