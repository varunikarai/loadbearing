"""The MCP server: a coding agent calls the probe and reads what the terminal would show."""

import io
import json
import unittest
from pathlib import Path

from loadbearing import mcp

EXAMPLE = str(Path(__file__).resolve().parent.parent / "examples" / "ticket_triage" / "target.json")


def converse(*messages):
    stdin = io.StringIO("".join((m if isinstance(m, str) else json.dumps(m)) + "\n" for m in messages))
    stdout = io.StringIO()
    mcp.serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def call(msg_id, arguments, name="probe"):
    return {"jsonrpc": "2.0", "id": msg_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}}


class ProtocolTests(unittest.TestCase):
    def test_initialize_echoes_the_clients_version_and_offers_tools(self):
        [reply] = converse({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2025-03-26", "capabilities": {}}})
        self.assertEqual(reply["result"]["protocolVersion"], "2025-03-26")
        self.assertIn("tools", reply["result"]["capabilities"])
        self.assertEqual(reply["result"]["serverInfo"]["name"], "loadbearing")

    def test_notifications_get_no_reply(self):
        self.assertEqual(converse({"jsonrpc": "2.0", "method": "notifications/initialized"}), [])

    def test_the_probe_tool_is_listed_with_a_schema_that_requires_a_target(self):
        [reply] = converse({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        [tool] = reply["result"]["tools"]
        self.assertEqual(tool["name"], "probe")
        self.assertEqual(tool["inputSchema"]["required"], ["target"])
        self.assertIn("SILENT PASSTHROUGH", tool["description"])

    def test_unknown_methods_tools_and_bad_json_are_errors(self):
        replies = converse({"jsonrpc": "2.0", "id": 3, "method": "resources/list"}, call(4, {}, name="other"), "{not json")
        self.assertEqual([r["error"]["code"] for r in replies], [-32601, -32602, -32700])


class ProbeToolTests(unittest.TestCase):
    def test_a_probe_returns_the_verdict_table_and_what_the_exit_code_means(self):
        [reply] = converse(call(5, {"target": EXAMPLE}))
        result = reply["result"]
        self.assertFalse(result["isError"])
        text = result["content"][0]["text"]
        self.assertIn("body           relevant    same     same   same   SILENT PASSTHROUGH", text)
        self.assertTrue(text.endswith("exit 1: Defects found: the pipeline does not read its inputs as declared."))

    def test_nothing_the_probe_prints_reaches_the_protocol_stream(self):
        replies = converse(call(6, {"target": EXAMPLE}), {"jsonrpc": "2.0", "id": 7, "method": "ping"})
        self.assertEqual([r["id"] for r in replies], [6, 7])

    def test_a_missing_target_file_is_a_tool_error_not_a_crash(self):
        [reply] = converse(call(8, {"target": "no/such/target.json"}))
        self.assertTrue(reply["result"]["isError"])
        self.assertIn("exit 2", reply["result"]["content"][0]["text"])

    def test_a_call_without_a_target_is_refused(self):
        [reply] = converse(call(9, {}))
        self.assertTrue(reply["result"]["isError"])

    def test_flags_map_onto_the_probe_command_line(self):
        argv = mcp.probe_argv({"target": "t.json", "backend": "sandbox", "baseline_runs": 5, "prove": True, "nano": False})
        self.assertEqual(argv, ["probe", "t.json", "--backend", "sandbox", "--baseline-runs", "5", "--prove"])


if __name__ == "__main__":
    unittest.main()
