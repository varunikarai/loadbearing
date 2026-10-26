"""Loadbearing as a tool a coding agent can call: a Model Context Protocol server on stdio.

An agent that has just written or changed a pipeline can probe it before it calls the work
done. The `probe` tool runs exactly what `loadbearing probe` runs and returns what the
terminal would show, with the exit code's meaning, so there is one implementation and the
agent reads the same verdicts a person would. Standard library only, like the core.

Messages are JSON-RPC 2.0, one per line, on stdin and stdout. Anything the probe itself
prints goes into the tool result, never onto the protocol stream.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from typing import Any, Optional, TextIO

from loadbearing import __version__

PROTOCOL_VERSION = "2025-06-18"

PROBE_TOOL = {
    "name": "probe",
    "description": (
        "Run a pipeline once per mutated input field, from one checkpoint, and report which "
        "inputs it actually reads. A field that should matter but never moves the output is a "
        "SILENT PASSTHROUGH; a field that should not matter but moves it is a PHANTOM "
        "SENSITIVITY. Point it at a target.json next to the pipeline: {\"name\", \"files\": "
        "[files to copy], \"command\": \"python3 pipeline.py input.json\" (each run reads its "
        "record from input.json and prints JSON), \"record\": \"a JSON file holding one real input\", "
        "\"expects\": {\"relevant\": [fields that should change the output], \"irrelevant\": "
        "[fields that should not]}}. Undeclared fields are probed and reported but never "
        "called defects."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Path to the target.json"},
            "backend": {"type": "string", "enum": ["local", "sandbox"], "default": "local",
                        "description": "local runs on this machine; sandbox runs every fork in Nebius Token Factory Sandboxes"},
            "baseline_runs": {"type": "integer", "minimum": 2,
                              "description": "Runs of the unmutated input for the noise floor; use 3 to 5 for an LLM pipeline"},
            "explain": {"type": "boolean", "description": "Nemotron Super and Ultra explain each defect from the source"},
            "intent": {"type": "boolean", "description": "Infer from the pipeline's docs whether undeclared fields should matter"},
            "fix": {"type": "boolean", "description": "Nemotron Ultra writes the smallest fix for each defect"},
            "prove": {"type": "boolean", "description": "Apply each fix in a fresh fork of the same checkpoint and probe again"},
            "nano": {"type": "boolean", "description": "Nemotron Nano judges whether each moved output changed meaningfully"},
        },
        "required": ["target"],
        "additionalProperties": False,
    },
}

EXIT_MEANING = {
    0: "No defects found.",
    1: "Defects found: the pipeline does not read its inputs as declared.",
    2: "The probe could not run; see the output.",
}


def probe_argv(arguments: dict[str, Any]) -> list[str]:
    """The `loadbearing probe` command line for one tool call."""
    target = arguments.get("target")
    if not isinstance(target, str) or not target:
        raise ValueError("target must be the path to a target.json")
    argv = ["probe", target, "--backend", str(arguments.get("backend", "local"))]
    if arguments.get("baseline_runs") is not None:
        argv += ["--baseline-runs", str(int(arguments["baseline_runs"]))]
    for flag in ("explain", "intent", "fix", "prove", "nano"):
        if arguments.get(flag):
            argv.append(f"--{flag}")
    return argv


def call_probe(arguments: dict[str, Any]) -> dict[str, Any]:
    from loadbearing.cli import main

    argv = probe_argv(arguments)
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed), contextlib.redirect_stderr(printed):
        try:
            code = main(argv)
        except SystemExit as exc:  # argparse rejected a value
            code = exc.code if isinstance(exc.code, int) else 2
    text = f"$ loadbearing {' '.join(argv)}\n{printed.getvalue().rstrip()}\n\nexit {code}: {EXIT_MEANING.get(code, '')}"
    return {"content": [{"type": "text", "text": text}], "isError": code == 2}


def handle(message: dict[str, Any]) -> Optional[dict[str, Any]]:
    """The reply to one JSON-RPC message, or None for a notification."""
    method, params, msg_id = message.get("method"), message.get("params") or {}, message.get("id")
    if msg_id is None:
        return None
    if method == "initialize":
        result: Any = {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "loadbearing", "version": __version__},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [PROBE_TOOL]}
    elif method == "tools/call":
        if params.get("name") != "probe":
            return _error(msg_id, -32602, f"unknown tool: {params.get('name')}")
        try:
            result = call_probe(params.get("arguments") or {})
        except ValueError as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    else:
        return _error(msg_id, -32601, f"method not found: {method}")
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    for line in stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            reply: Optional[dict[str, Any]] = _error(None, -32700, "parse error")
        else:
            reply = handle(message) if isinstance(message, dict) else _error(None, -32600, "invalid request")
        if reply is not None:
            stdout.write(json.dumps(reply) + "\n")
            stdout.flush()
    return 0


def _error(msg_id: Any, code: int, text: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": text}}
