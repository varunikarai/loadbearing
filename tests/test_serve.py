import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from loadbearing.serve import Demo, serve

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class DemoServerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.servers = []

    def tearDown(self):
        for server in self.servers:
            server.shutdown()
            server.server_close()
        self._tmp.cleanup()

    def start(self, readonly=False):
        demo = Demo(EXAMPLES, self._tmp.name, readonly=readonly)
        server = serve(demo, port=0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}"

    def get(self, url):
        try:
            with urllib.request.urlopen(url) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as err:
            with err:
                return err.code, err.read().decode()

    def post(self, url):
        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(urllib.request.Request(url, data=b"", method="POST")) as resp:
                return resp.status, resp.headers
        except urllib.error.HTTPError as err:
            with err:
                return err.code, err.headers

    def test_index_lists_the_example_targets(self):
        base = self.start()
        status, body = self.get(base + "/")
        self.assertEqual(status, 200)
        self.assertIn("ticket_triage", body)
        self.assertIn("not run yet", body)

    def test_a_run_is_cached_and_served_as_a_report(self):
        base = self.start()
        status, headers = self.post(base + "/t/ticket_triage/run")
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/t/ticket_triage")
        status, body = self.get(base + "/t/ticket_triage")
        self.assertEqual(status, 200)
        self.assertIn("body · silent passthrough", body)
        status, body = self.get(base + "/t/ticket_triage.json")
        self.assertIn('"schema": 1', body)
        _, index = self.get(base + "/")
        self.assertIn("2 defects", index)

    def test_readonly_refuses_to_run(self):
        base = self.start(readonly=True)
        status, _ = self.post(base + "/t/ticket_triage/run")
        self.assertEqual(status, 403)
        self.assertNotIn("Run probe", self.get(base + "/")[1])

    def test_only_known_targets_can_be_named(self):
        base = self.start()
        self.assertEqual(self.get(base + "/t/..%2F..%2Fetc")[0], 404)
        self.assertEqual(self.post(base + "/t/nope/run")[0], 404)

    def test_health_check(self):
        self.assertEqual(self.get(self.start() + "/healthz"), (200, "ok"))


if __name__ == "__main__":
    unittest.main()
