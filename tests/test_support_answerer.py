"""A3 offline: the RAG demo target, probed and fixed against a fake Token Factory.

The fake answers like a grounded model: from the policy when the policy is in
the prompt, from "what most shops do" when it is not. Its free-text answer
changes on every call, as a real model's wording can, so the noise floor has
something to remove. The pipeline itself runs unmodified, over HTTP.
"""

import itertools
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from loadbearing.backends.local import LocalBackend
from loadbearing.fix import Fix
from loadbearing.probe import probe
from loadbearing.prove import Pinned, prove
from loadbearing.target import load_target
from loadbearing.verdict import INERT, LOAD_BEARING, SILENT_PASSTHROUGH

TARGET = Path(__file__).resolve().parent.parent / "examples" / "support_answerer" / "target.json"
_calls = itertools.count(1)


def grounded_model(prompt: str) -> dict:
    policy, _, question = prompt.partition("Customer question:\n")
    n = next(_calls)
    if "return" not in question.lower():
        return {"answer": f"I can help with orders and returns. (ref {n})", "can_return": None,
                "return_window_days": None}
    if "14 days" in policy:
        return {"answer": f"Our return window is 14 days, so a refund is not possible, but the "
                          f"warranty covers a repair. (ref {n})",
                "can_return": False, "return_window_days": 14}
    return {"answer": f"Yes, you have 30 days to return it for a full refund. (ref {n})",
            "can_return": True, "return_window_days": 30}


class FakeTokenFactory(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert self.headers["Authorization"] == "Bearer fake-key"
        assert body["model"] == "fake/nano" and body["temperature"] == 0
        reply = grounded_model(body["messages"][-1]["content"])
        raw = json.dumps({"choices": [{"message": {"content": json.dumps(reply)}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class SupportAnswererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeTokenFactory)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls._env = dict(os.environ)
        os.environ.update({
            "NEBIUS_API_KEY": "fake-key",
            "NEMOTRON_NANO_MODEL": "fake/nano",
            "TOKEN_FACTORY_BASE_URL": f"http://127.0.0.1:{cls.server.server_address[1]}/v1/",
        })
        cls.target = load_target(TARGET)
        cls.backend = LocalBackend()
        cls.pinned = Pinned(cls.backend)
        cls.report = probe(cls.target, cls.pinned)

    @classmethod
    def tearDownClass(cls):
        cls.backend.close()
        cls.server.shutdown()
        cls.server.server_close()
        os.environ.clear()
        os.environ.update(cls._env)

    def test_the_pipeline_answers_confidently_and_wrongly(self):
        out = self.report.baseline.output()
        self.assertEqual((out["can_return"], out["return_window_days"]), (True, 30))

    def test_the_noise_floor_removes_only_the_free_text(self):
        self.assertEqual(self.report.baseline_runs, 5)
        self.assertEqual(self.report.unstable_keys, ["answer"])
        self.assertFalse(self.report.void)

    def test_the_retrieved_passages_are_a_silent_passthrough(self):
        verdicts = {v.field: v.verdict for v in self.report.verdicts}
        self.assertEqual(verdicts, {
            "request_id": INERT,
            "user_id": INERT,
            "received_at": INERT,
            "question": LOAD_BEARING,
            "passages": SILENT_PASSTHROUGH,
        })

    def test_the_one_line_fix_is_proven_and_the_answer_becomes_14_days(self):
        source = (self.target.root / "pipeline.py").read_text()
        fixed = source.replace(
            'context = request.get("context", "")',
            'context = "\\n\\n".join(p["text"] for p in request.get("passages", []))',
        )
        self.assertNotEqual(fixed, source)
        fix = Fix("passages", SILENT_PASSTHROUGH, {"pipeline.py": fixed}, "Read the passages the retriever writes.")
        proof = prove(self.target, self.backend, fix, self.report, checkpoint=self.pinned.pinned)
        self.assertTrue(proof.clean)
        after = proof.after.baseline.output()
        self.assertEqual((after["can_return"], after["return_window_days"]), (False, 14))
        self.assertEqual({v.field: v.verdict for v in proof.after.verdicts}["passages"], LOAD_BEARING)


if __name__ == "__main__":
    unittest.main()
