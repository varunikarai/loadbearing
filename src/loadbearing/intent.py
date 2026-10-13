"""Intent inference: which undeclared fields should matter, quoted from the pipeline's docs.

Tavily finds and reads the upstream docs: a search for the target's
`docs.query`, and an extract of any `docs.urls`. Super reads the excerpts and
says, for each field nobody declared, whether it should change the output,
backed by a sentence and its URL. The target's own pages are read first; the
search results settle only the fields those leave open, so when the pipeline's
own spec has an answer, that is what gets quoted. A quote that is not actually
in the excerpt it cites is thrown away, so every inferred intent can be checked
by opening the link.

Both steps are cached under `runs/`, so a demo or a re-run never pays twice.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from loadbearing import tavily
from loadbearing.mutations import leaf_paths
from loadbearing.target import Target
from loadbearing.verdict import UNDECLARED, Evidence, intent_of


# Bumped whenever what a cache entry means changes, so an older entry is fetched again, not trusted.
CACHE_VERSION = 2


@dataclass
class Excerpt:
    url: str
    title: str
    content: str
    declared: bool = False  # one of the target's own docs.urls, not a search hit


def undeclared_fields(target: Target) -> list[str]:
    return [f for f in leaf_paths(target.record) if intent_of(f, target.expects) == UNDECLARED]


def gather(
    target: Target,
    search: Callable[..., dict] = tavily.search,
    extract: Callable[..., dict] = tavily.extract,
    cache_dir: str | Path = "runs",
) -> list[Excerpt]:
    """The docs excerpts for a target, from cache when they have been fetched before."""
    cache = Path(cache_dir) / f"{target.name}.docs.json"
    key = {"version": CACHE_VERSION, "docs": target.docs}
    if cache.is_file():
        saved = json.loads(cache.read_text())
        if isinstance(saved, dict) and saved.get("key") == key:
            return [Excerpt(**e) for e in saved["excerpts"]]
    docs = target.docs or {}
    excerpts = []
    if docs.get("query"):
        for r in search(docs["query"]).get("results", []):
            text = r.get("raw_content") or r.get("content") or ""
            excerpts.append(Excerpt(r.get("url", ""), r.get("title", ""), text))
    if docs.get("urls"):
        for r in extract(docs["urls"]).get("results", []):
            excerpts.append(Excerpt(r.get("url", ""), "", r.get("raw_content") or "", declared=True))
    excerpts = [e for e in excerpts if e.url and e.content]
    if excerpts:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"key": key, "excerpts": [asdict(e) for e in excerpts]}, indent=2))
    return excerpts


def infer_expects(
    target: Target,
    router: Any,
    search: Callable[..., dict] = tavily.search,
    extract: Callable[..., dict] = tavily.extract,
    cache_dir: str | Path = "runs",
) -> dict[str, Evidence]:
    """Inferred intents for the target's undeclared fields, each backed by a checked quote."""
    fields = undeclared_fields(target)
    if not fields or not target.docs:
        return {}
    cache = Path(cache_dir) / f"{target.name}.intent.json"
    if cache.is_file():
        saved = json.loads(cache.read_text())
        if saved.get("fields") == fields:
            return {f: Evidence(**e) for f, e in saved["intents"].items()}
    excerpts = gather(target, search, extract, cache_dir)
    if not excerpts:
        return {}
    own = [e for e in excerpts if e.declared]
    intents = _settle(router, fields, own, target.record)
    left = [f for f in fields if f not in intents]
    intents.update(_settle(router, left, [e for e in excerpts if not e.declared], target.record))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({"fields": fields, "intents": {f: asdict(e) for f, e in intents.items()}}, indent=2)
    )
    return intents


def _settle(router: Any, fields: list[str], excerpts: list[Excerpt], record: dict) -> dict[str, Evidence]:
    """One Super call over one set of excerpts, keeping only answers quoted from that set."""
    if not fields or not excerpts:
        return {}
    answers = router.infer_intent(fields, excerpts, record)
    return {f: ev for f, ev in answers.items() if f in fields and quoted(ev, excerpts)}


def quoted(evidence: Evidence, excerpts: list[Excerpt]) -> bool:
    """True when the quote appears in the excerpt it cites. Whitespace is not held against it."""
    quote = _squash(evidence.quote)
    if not quote:
        return False
    return any(e.url == evidence.url and quote in _squash(e.content) for e in excerpts)


def _squash(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", text or "").strip()
