"""A2: secrets reach baseline and fork runs only, and never land in a checkpoint."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from loadbearing.backends.local import LocalBackend
from loadbearing.target import load_target

SECRET = "lb-secret-value-6f1c"
UNNAMED = "nebius-key-that-must-not-leak"

# The pipeline reports only the secret's length, so its source never contains the value.
PIPELINE = """
import json, os
print(json.dumps({"named": len(os.environ.get("LB_TEST_SECRET", "")),
                  "unnamed": "NEBIUS_API_KEY" in os.environ}))
"""


class SecretsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        (root / "pipeline.py").write_text(PIPELINE)
        (root / "record.json").write_text('{"q": "hi"}')
        # The setup step tries its hardest to leak: it writes its whole environment to disk.
        (root / "target.json").write_text(json.dumps({
            "command": "python3 pipeline.py",
            "setup": "env > setup_env.txt",
            "files": ["pipeline.py"],
            "record": "record.json",
            "env": ["LB_TEST_SECRET"],
        }))
        self.target = load_target(root / "target.json")
        self._env = dict(os.environ)
        os.environ["LB_TEST_SECRET"] = SECRET
        os.environ["NEBIUS_API_KEY"] = UNNAMED
        self.backend = LocalBackend()

    def tearDown(self):
        self.backend.close()
        os.environ.clear()
        os.environ.update(self._env)
        self._tmp.cleanup()

    def test_a_fork_sees_the_named_secret_and_nothing_else(self):
        ckpt = self.backend.checkpoint(self.target)
        out = json.loads(self.backend.run(ckpt, self.target, self.target.record).stdout)
        self.assertEqual(out, {"named": len(SECRET), "unnamed": False})

    def test_no_file_in_the_checkpoint_contains_a_secret(self):
        ckpt = self.backend.checkpoint(self.target)
        self.backend.run(ckpt, self.target, self.target.record)
        written = [p for p in ckpt.rglob("*") if p.is_file()]
        self.assertTrue(any(p.name == "setup_env.txt" for p in written))
        for path in written:
            text = path.read_text(errors="replace")
            self.assertNotIn(SECRET, text, path.name)
            self.assertNotIn(UNNAMED, text, path.name)

    def test_a_missing_secret_fails_before_any_run(self):
        del os.environ["LB_TEST_SECRET"]
        with self.assertRaisesRegex(RuntimeError, "LB_TEST_SECRET"):
            self.backend.checkpoint(self.target)


if __name__ == "__main__":
    unittest.main()
