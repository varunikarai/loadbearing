"""Nemotron on Nebius Token Factory, routed by job.

Nano judges each fork (one cheap call per moved diff), Super reconciles across
forks into a defect class, Ultra explains why a code path does or does not read
a field. Token Factory speaks the standard chat-completions HTTP API, so this
uses the standard library rather than an SDK.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from loadbearing.backends.base import RunResult
    from loadbearing.mutations import Mutation
    from loadbearing.verdict import Evidence, FieldVerdict

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
TIERS = ("nano", "super", "ultra")
# Exact model IDs come from the environment: `loadbearing models` lists the
# Nemotron IDs your key can call.
MODEL_ENV = {
    "nano": "NEMOTRON_NANO_MODEL",
    "super": "NEMOTRON_SUPER_MODEL",
    "ultra": "NEMOTRON_ULTRA_MODEL",
}

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
    '{"rationale": "<one paragraph>", "edits": [{"path": "<path>", "old": "<text copied '
    'exactly from the file>", "new": "<what replaces it>"}]}. Each old text must appear in its '
    "file exactly once and hold only the lines you change. Every line you do not quote stays "
    "as it is."
)

INTENT_SYSTEM = (
    "You decide, from a pipeline's own documentation, whether each named input field should "
    "change the pipeline's output. Answer 'relevant' when the docs say or clearly imply the "
    "output depends on the field, 'irrelevant' when they say or clearly imply it must not "
    "affect the output (for example an id or a timestamp kept only for logging), and "
    "'unknown' when they do not settle it. Back every relevant or irrelevant answer with one "
    "sentence copied word for word from an excerpt, and that excerpt's URL. Never paraphrase "
    'a quote. Reply with one JSON object and nothing around it: {"fields": {"<field>": '
    '{"intent": "relevant|irrelevant|unknown", "quote": "<verbatim>", "url": "<url>"}}}.'
)
_EXCERPT_CLIP = 6000


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
        """Ultra. The smallest change that removes one defect: (path -> new content, rationale).

        Ultra quotes the lines it changes instead of retyping whole files, so a line it
        never quoted cannot come back altered."""
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
        rationale = reply.get("rationale")
        if not isinstance(rationale, str):
            raise ValueError("the fix reply has no rationale")
        return _apply_edits(reply.get("edits"), sources), rationale

    def infer_intent(
        self, fields: list[str], excerpts: list[Any], record: dict | None = None
    ) -> dict[str, Evidence]:
        """Super. For each field, whether the docs say it should matter, with a quote and URL.
        Only relevant and irrelevant answers come back; checking the quotes is the caller's job."""
        from loadbearing.verdict import IRRELEVANT, RELEVANT, Evidence

        lines = ["Fields, with their current values:"]
        for field in fields:
            value = _value_at(record, field) if record else None
            lines.append(f"- {field}: {json.dumps(value)[:200]}")
        lines.append("\nDocumentation excerpts:")
        for n, excerpt in enumerate(excerpts, 1):
            lines.append(f"\n[{n}] {excerpt.url}\n{excerpt.content[:_EXCERPT_CLIP]}")
        reply = _json_object(self._ask("super", INTENT_SYSTEM, "\n".join(lines), max_tokens=2048))
        answers = reply.get("fields")
        if not isinstance(answers, dict):
            raise ValueError("the intent reply has no fields mapping")
        out = {}
        for field, item in answers.items():
            if not isinstance(item, dict) or item.get("intent") not in (RELEVANT, IRRELEVANT):
                continue
            out[field] = Evidence(item["intent"], str(item.get("quote", "")), str(item.get("url", "")))
        return out

    def _ask(self, tier: str, system: str, prompt: str, max_tokens: int = 1024) -> str:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        return self.client.chat(self.models[tier], messages, max_tokens=max_tokens)


def _json_object(text: str) -> dict:
    """The JSON object in a reply, tolerating a code fence or a sentence around it."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("the reply holds no JSON object")
    return json.loads(text[start : end + 1])


def _apply_edits(edits: Any, sources: dict[str, str]) -> dict[str, str]:
    """The files an edit list produces: each edit swaps one exact, unique quote for new text."""
    if not isinstance(edits, list) or not edits:
        raise ValueError("the fix reply has no edits")
    files: dict[str, str] = {}
    for edit in edits:
        if not isinstance(edit, dict) or not all(isinstance(edit.get(k), str) for k in ("path", "old", "new")):
            raise ValueError("an edit needs a path, the old text and the new text")
        path, old = edit["path"], edit["old"]
        if path not in sources:
            raise ValueError(f"an edit names {path}, which is not among the target's sources")
        text = files.get(path, sources[path])
        found = text.count(old) if old else 0
        if found != 1:
            raise ValueError(f"an edit's old text appears {found} times in {path}, not once")
        files[path] = text.replace(old, edit["new"], 1)
    return files


def _strip_reasoning(text: str) -> str:
    """Drop the reasoning trace in front of an answer: a whole <think> block, one whose
    opening tag the chat template supplied, and one cut off before its closing tag.
    Tags inside the answer itself, such as code a fix edits, are left alone."""
    close = text.find("</think>")
    if text.lstrip().startswith("<think>") or (close >= 0 and "<think>" not in text[:close]):
        if close < 0:
            return ""
        text = text[close + len("</think>") :]
    opened = text.rfind("<think>")
    if opened >= 0 and "</think>" not in text[opened:]:
        text = text[:opened]
    return text.strip()


def _value_at(record: dict, path: str) -> Any:
    node: Any = record
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node
