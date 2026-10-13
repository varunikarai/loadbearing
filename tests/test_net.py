"""Retries: a rate limit or a 5xx costs a wait, a bad key fails at once."""

import io
import json
import unittest
import urllib.error
import urllib.request
from unittest import mock

from loadbearing.net import fetch_json

URL = "https://api.example.test/v1/chat"


def http_error(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    return urllib.error.HTTPError(URL, code, "error", headers, io.BytesIO(b"{}"))


def ok(body):
    return io.BytesIO(json.dumps(body).encode())


class FetchJsonTests(unittest.TestCase):
    def fetch(self, *outcomes, tries=4):
        """Run fetch_json against urlopen answering with `outcomes` in order."""
        waits = []
        replies = iter(outcomes)

        def urlopen(req, timeout):
            outcome = next(replies)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with mock.patch.object(urllib.request, "urlopen", urlopen):
            result = fetch_json(urllib.request.Request(URL), timeout=5, tries=tries, sleep=waits.append)
        return result, waits

    def test_a_rate_limit_and_a_server_error_are_waited_out(self):
        result, waits = self.fetch(http_error(429), http_error(503), ok({"id": 1}))
        self.assertEqual(result, {"id": 1})
        self.assertEqual(waits, [1.0, 2.0])

    def test_a_dropped_connection_is_retried(self):
        result, waits = self.fetch(urllib.error.URLError("reset"), ok({"id": 2}))
        self.assertEqual((result, waits), ({"id": 2}, [1.0]))

    def test_retry_after_is_honoured_and_capped(self):
        _, waits = self.fetch(http_error(429, "7"), http_error(429, "600"), ok({}))
        self.assertEqual(waits, [7.0, 30.0])

    def test_a_bad_key_fails_at_once(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.fetch(http_error(401), ok({}))
        self.assertEqual(caught.exception.code, 401)

    def test_it_gives_up_after_the_last_try(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.fetch(http_error(500), http_error(500), http_error(500), tries=3)


if __name__ == "__main__":
    unittest.main()
