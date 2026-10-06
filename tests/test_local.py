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


if __name__ == "__main__":
    unittest.main()
