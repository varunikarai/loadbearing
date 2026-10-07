"""The Tavily client builds the requests its docs describe, without touching the network."""

import io
import json
import unittest
from unittest import mock

from loadbearing import tavily


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TavilyClientTests(unittest.TestCase):
    def send(self, call):
        sent = {}

        def fake_urlopen(req, timeout):
            sent["url"], sent["body"] = req.full_url, json.loads(req.data)
            sent["auth"] = req.get_header("Authorization")
            return FakeResponse(json.dumps({"results": []}).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(call(), {"results": []})
        return sent

    def test_search_asks_for_whole_pages(self):
        sent = self.send(lambda: tavily.search("return window policy", api_key="tvly-test"))
        self.assertEqual(sent["url"], "https://api.tavily.com/search")
        self.assertEqual(sent["auth"], "Bearer tvly-test")
        self.assertEqual(sent["body"]["query"], "return window policy")
        self.assertTrue(sent["body"]["include_raw_content"])

    def test_extract_sends_the_urls(self):
        sent = self.send(lambda: tavily.extract(["https://example.org/a"], api_key="tvly-test"))
        self.assertEqual(sent["url"], "https://api.tavily.com/extract")
        self.assertEqual(sent["body"], {"urls": ["https://example.org/a"]})

    def test_no_key_is_a_clear_error(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                tavily.search("anything")


if __name__ == "__main__":
    unittest.main()
