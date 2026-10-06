import tempfile
import unittest
from pathlib import Path

from loadbearing.backends.local import LocalBackend
from loadbearing.target import load_target

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json"


class LocalBackendTests(unittest.TestCase):
    def setUp(self):
        self.backend = LocalBackend()
        self.target = load_target(EXAMPLE)

    def tearDown(self):
        self.backend.close()

    def test_one_backend_can_hold_many_checkpoints(self):
        a = self.backend.checkpoint(self.target)
        b = self.backend.checkpoint(self.target)
        self.assertNotEqual(a, b)

    def test_apply_derives_a_new_checkpoint_and_leaves_the_original_alone(self):
        original = self.backend.checkpoint(self.target)
        before = (original / "pipeline.py").read_text()
        derived = self.backend.apply(original, {"pipeline.py": "print('patched')\n"})
        self.assertEqual((derived / "pipeline.py").read_text(), "print('patched')\n")
        self.assertEqual((original / "pipeline.py").read_text(), before)

    def test_apply_refuses_a_path_outside_the_checkpoint(self):
        original = self.backend.checkpoint(self.target)
        with self.assertRaises(ValueError):
            self.backend.apply(original, {"../escape.py": "x"})


if __name__ == "__main__":
    unittest.main()
