"""The Sandboxes backend against a fake contree-sdk, so the calls are checked offline.

The fake mirrors the real signatures of contree-sdk 0.3.6: ContreeSync() with no
arguments, images.use(ref), image.apply_files(dict), image.run(shell=, cwd=,
files=, env=, timeout=, disposable=) returning an image whose .wait() runs it.
"""

import json
import sys
import types
import unittest
from pathlib import Path

from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class FakeImage:
    def __init__(self, sdk, ref, files=None):
        self.sdk, self.ref, self.files = sdk, ref, dict(files or {})
        self.request = None
        self.stdout, self.stderr, self.exit_code = "", "", 0

    def apply_files(self, files):
        return FakeImage(self.sdk, self.ref, {**self.files, **files})

    def run(self, shell=None, *, cwd=None, files=None, env=None, timeout=None, disposable=True):
        child = FakeImage(self.sdk, self.ref, {**self.files, **(files or {})})
        child.request = dict(shell=shell, cwd=cwd, files=files or {}, env=env, timeout=timeout,
                             disposable=disposable)
        return child

    def wait(self):
        self.sdk.runs.append(self)
        if self.request["shell"].startswith("python3 pipeline.py"):
            record = json.loads(self.files["/work/input.json"])
            self.stdout = json.dumps({"seen": sorted(record)})
        return self


class FakeSdk:
    def __init__(self, *args, **kwargs):
        if args or kwargs:
            raise TypeError("the real ContreeSync() is built from the environment, with no client")
        self.runs = []
        self.images = types.SimpleNamespace(use=lambda ref: FakeImage(self, ref))


class ContreeBackendTests(unittest.TestCase):
    def setUp(self):
        self.module = types.ModuleType("contree_sdk")
        self.module.ContreeSync = FakeSdk
        self._saved = sys.modules.get("contree_sdk")
        sys.modules["contree_sdk"] = self.module
        from loadbearing.backends.contree import ContreeBackend

        self.backend = ContreeBackend()
        self.target = load_target(EXAMPLE)

    def tearDown(self):
        if self._saved is None:
            sys.modules.pop("contree_sdk", None)
        else:
            sys.modules["contree_sdk"] = self._saved

    def test_the_checkpoint_keeps_its_image_and_holds_the_files(self):
        ckpt = self.backend.checkpoint(self.target)
        self.assertFalse(ckpt.request["disposable"])
        self.assertEqual(ckpt.request["cwd"], "/work")
        self.assertIn("/work/pipeline.py", ckpt.files)
        self.assertEqual(ckpt.files["/work/pipeline.py"], (self.target.root / "pipeline.py").read_bytes())

    def test_a_fork_is_disposable_and_gets_only_its_own_record(self):
        ckpt = self.backend.checkpoint(self.target)
        result = self.backend.run(ckpt, self.target, {"subject": "x"})
        fork = self.backend._sdk.runs[-1]
        self.assertTrue(fork.request["disposable"])
        self.assertEqual(json.loads(fork.request["files"]["/work/input.json"]), {"subject": "x"})
        self.assertEqual(json.loads(result.stdout), {"seen": ["subject"]})
        # The checkpoint itself is never written to by a fork.
        self.assertNotIn("/work/input.json", ckpt.files)

    def test_secrets_go_to_forks_only(self):
        import os

        saved = dict(os.environ)
        os.environ["LB_TEST_SECRET"] = "s3cret"
        try:
            self.target.env = ["LB_TEST_SECRET"]
            ckpt = self.backend.checkpoint(self.target)
            self.backend.run(ckpt, self.target, {})
        finally:
            os.environ.clear()
            os.environ.update(saved)
        setup, fork = self.backend._sdk.runs[0], self.backend._sdk.runs[-1]
        self.assertIsNone(setup.request["env"])
        self.assertEqual(fork.request["env"], {"LB_TEST_SECRET": "s3cret"})

    def test_a_failed_setup_is_reported(self):
        original = FakeImage.wait

        def failing(image):
            image = original(image)
            image.exit_code, image.stderr = 1, b"no python"
            return image

        FakeImage.wait = failing
        try:
            with self.assertRaisesRegex(RuntimeError, "no python"):
                self.backend.checkpoint(self.target)
        finally:
            FakeImage.wait = original


if __name__ == "__main__":
    unittest.main()
