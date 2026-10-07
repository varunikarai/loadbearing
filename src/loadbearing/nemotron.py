"""Nemotron on Nebius Token Factory, routed by job.

Nano judges each fork (one cheap call per moved diff), Super reconciles across
forks into a defect class, Ultra explains why a code path does or does not read
a field. Token Factory speaks the standard chat-completions HTTP API, so this
uses the standard library rather than an SDK.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from loadbearing.backends.base import RunResult
    from loadbearing.mutations import Mutation
    from loadbearing.verdict import FieldVerdict

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
TIERS = ("nano", "super", "ultra")
# Exact model IDs come from the environment: `loadbearing models` lists the
# Nemotron IDs your key can call.
MODEL_ENV = {
    "nano": "NEMOTRON_NANO_MODEL",
    "super": "NEMOTRON_SUPER_MODEL",
    "ultra": "NEMOTRON_ULTRA_MODEL",
}

_THINK = re.compile(r"<think>.*?</think>", re.S)
_CLIP = 4000

CLASSIFY_SYSTEM = (
    "You compare two outputs of the same program. The only difference between the two "
    "runs is one mutated input field. Answer with exactly one word: 'meaningful' if the "
    "output changed in a way a user of this program would care about, or 'noise' if it "
    "changed only in something incidental such as a timestamp, a request id, ordering, "
    "or whitespace."
)

RECONCILE_SYSTEM = (
    "You are given, for one input field of a pipeline, what happened to the pipeline's "
    "output when that field was destroyed, dropped, and nudged, and whether the field "
    "is supposed to matter. State in two sentences whether this is a silent passthrough "
    "(a field that should matter is not read), a phantom sensitivity (a field that should "
    "not matter changes the output), or neither, and the evidence."
)

EXPLAIN_SYSTEM = (
    "You are given a pipeline's source code and a defect found by running it. Find the "
    "exact code path responsible and explain why it does or does not read the field. "
    "Quote the line. Propose the smallest fix."
)

FIX_SYSTEM = (
    "You fix one defect in a pipeline. You are given its source files and a defect found by "
    "running it: a field it should read but never does (silent passthrough), or a field it "
    "should ignore but reacts to (phantom sensitivity). Make the smallest change that removes "
    "that defect and nothing else. Reply with one JSON object and nothing around it: "
    '{"rationale": "<one paragraph>", "files": {"<path>": "<complete new file content>"}}. '
    "Include only the files you change, each with its complete new content."
)


class TokenFactory:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("NEBIUS_API_KEY")
        if not self.api_key:
            raise RuntimeError("NEBIUS_API_KEY is not set (see .env.example)")
        base = base_url or os.environ.get("TOKEN_FACTORY_BASE_URL") or BASE_URL
        self.base_url = base.rstrip("/") + "/"

    def list_models(self) -> list[str]:
        return sorted(m["id"] for m in self._request("models")["data"])

    def chat(self, model: str, messages: list[dict], max_tokens: int = 1024) -> str:
        reply = self._request(
            "chat/completions",
            {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0},
        )
        return _strip_reasoning(reply["choices"][0]["message"].get("content") or "")

    def _request(self, path: str, body: dict | None = None) -> Any:
        req = urllib.request.Request(
            self.base_url + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)


class NemotronRouter:
    def __init__(self, client: TokenFactory, models: dict[str, str]) -> None:
        self.client = client
        self.models = models

    @classmethod
    def from_env(cls, tiers: tuple[str, ...] = TIERS) -> NemotronRouter:
        missing = [MODEL_ENV[t] for t in tiers if not os.environ.get(MODEL_ENV[t])]
        if missing:
            raise RuntimeError(
                f"set {', '.join(missing)} in .env; `loadbearing models` lists the exact IDs"
            )
        return cls(TokenFactory(), {t: os.environ[MODEL_ENV[t]] for t in tiers})

    def classify_diff(self, mutation: Mutation, baseline: RunResult, fork: RunResult) -> str:
        """Nano. Anything short of an explicit 'noise' counts as meaningful."""
        prompt = (
            f"Mutation: {mutation.kind} on input field '{mutation.field}'.\n"
            f"Exit codes: baseline {baseline.exit_code}, mutated {fork.exit_code}.\n\n"
            f"Baseline output:\n{baseline.stdout[:_CLIP]}\n\n"
            f"Mutated output:\n{fork.stdout[:_CLIP]}"
        )
        answer = self._ask("nano", CLASSIFY_SYSTEM, prompt, max_tokens=512)
        return "noise" if answer.lower().startswith("noise") else "meaningful"

    def reconcile(self, verdict: FieldVerdict) -> str:
        """Super. One defect statement per field, from every fork on that field."""
        prompt = (
            f"Field: {verdict.field}\nSupposed to matter: {verdict.intent}\n"
            f"Output moved, per mutation: {json.dumps(verdict.moved)}"
        )
        return self._ask("super", RECONCILE_SYSTEM, prompt)

    def explain(self, verdict: FieldVerdict, source: str) -> str:
        """Ultra. The long-horizon 'why' over the pipeline's source."""
        prompt = f"Defect: {verdict.verdict} on field '{verdict.field}'.\n\nSource:\n{source}"
        return self._ask("ultra", EXPLAIN_SYSTEM, prompt, max_tokens=2048)

    def write_fix(self, verdict: FieldVerdict, sources: dict[str, str]) -> tuple[dict[str, str], str]:
        """Ultra. The smallest change that removes one defect: (path -> new content, rationale)."""
        lines = [
            f"Defect: {verdict.verdict} on input field '{verdict.field}', "
            f"which is supposed to be {verdict.intent}.",
            f"Output moved, per mutation: {json.dumps(verdict.moved)}",
        ]
        if verdict.explanation:
            lines.append(f"Why, from reading the code: {verdict.explanation}")
        if verdict.evidence:
            lines.append(f'Intended behaviour, from {verdict.evidence.url}: "{verdict.evidence.quote}"')
        for path, content in sources.items():
            lines.append(f"\n--- {path}\n{content}")
        reply = _json_object(self._ask("ultra", FIX_SYSTEM, "\n".join(lines), max_tokens=4096))
        files, rationale = reply.get("files"), reply.get("rationale")
        if not isinstance(files, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in files.items()
        ):
            raise ValueError("the fix reply has no files mapping path to content")
        if not isinstance(rationale, str):
            raise ValueError("the fix reply has no rationale")
        return files, rationale

    def _ask(self, tier: str, system: str, prompt: str, max_tokens: int = 1024) -> str:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        return self.client.chat(self.models[tier], messages, max_tokens=max_tokens)


def _json_object(text: str) -> dict:
    """The JSON object in a reply, tolerating a code fence or a sentence around it."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("the reply holds no JSON object")
    return json.loads(text[start : end + 1])


def _strip_reasoning(text: str) -> str:
    """Drop reasoning traces: whole <think> blocks, a trace whose opening tag the
    chat template supplied, and one cut off before its closing tag."""
    text = _THINK.sub("", text)
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    if "<think>" in text:
        text = text.split("<think>", 1)[0]
    return text.strip()
