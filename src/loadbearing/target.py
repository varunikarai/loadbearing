"""A target file says how to run a pipeline and what its inputs are supposed to mean."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from loadbearing.mutations import leaf_paths


@dataclass
class Target:
    name: str
    root: Path  # directory the target file lives in; `files` and `record` resolve against it
    image: str  # OCI image the sandbox backend starts from
    setup: str  # runs once, before the checkpoint is taken
    files: list[str]  # copied into the checkpoint
    command: str  # runs in every fork, reads the record from input.json
    record: dict  # the baseline input
    expects: dict[str, list[str]]  # "relevant" / "irrelevant" -> field paths
    timeout: float = 60.0
    # Version 2 keys (contract C1). All optional; their defaults keep v1 targets unchanged.
    baseline_runs: int = 2  # how often the unmutated record runs, for the noise floor
    # Variable names read from the host at run time and passed to baseline and
    # fork runs only, never to setup, so a secret is never baked into a checkpoint.
    env: list[str] = field(default_factory=list)
    docs: Optional[dict[str, Any]] = None  # {"query": str, "urls": [str]} for Tavily intent
    sources: list[str] = field(default_factory=list)  # files a fix may read and rewrite


def load_target(path: str | Path) -> Target:
    path = Path(path).resolve()
    spec = json.loads(path.read_text())
    root = path.parent
    expects = spec.get("expects", {})
    files = list(spec.get("files", []))
    target = Target(
        name=spec.get("name", root.name),
        root=root,
        image=spec.get("image", "python:3.12-slim"),
        setup=spec.get("setup", ""),
        files=files,
        command=spec["command"],
        record=json.loads((root / spec["record"]).read_text()),
        expects={
            "relevant": list(expects.get("relevant", [])),
            "irrelevant": list(expects.get("irrelevant", [])),
        },
        timeout=float(spec.get("timeout", 60)),
        baseline_runs=spec.get("baseline_runs", 2),
        env=list(spec.get("env", [])),
        docs=spec.get("docs"),
        sources=list(spec.get("sources", files)),
    )
    _check(target, path)
    return target


def _check(target: Target, path: Path) -> None:
    """Fail at load time with the key's name, not mid-probe with a stack trace."""
    if not isinstance(target.record, dict):
        raise RuntimeError(f"{path}: the record must be a JSON object of field names to values")
    try:
        fields = list(leaf_paths(target.record))
    except ValueError as exc:  # a key with a dot in it
        raise RuntimeError(f"{path}: {exc}") from None
    for intent, declared in target.expects.items():
        for name in declared:
            # A typo here would leave the real field undeclared, so it could never be flagged.
            if not any(f == name or f.startswith(name + ".") for f in fields):
                raise RuntimeError(f"{path}: expects.{intent} names {name!r}, which is not a field of the record")
    runs = target.baseline_runs
    if isinstance(runs, bool) or not isinstance(runs, int) or runs < 2:
        raise RuntimeError(f"{path}: baseline_runs must be an integer, 2 or more")
    if not all(isinstance(name, str) and name for name in target.env):
        raise RuntimeError(f"{path}: env must be a list of variable names")
    if target.docs is not None:
        if not isinstance(target.docs, dict) or not isinstance(target.docs.get("query", ""), str):
            raise RuntimeError(f'{path}: docs must look like {{"query": "...", "urls": ["..."]}}')
        if not all(isinstance(u, str) for u in target.docs.get("urls", [])):
            raise RuntimeError(f"{path}: docs.urls must be a list of URLs")
    for rel in target.sources:
        resolved = (target.root / rel).resolve()
        if not resolved.is_relative_to(target.root) or not resolved.is_file():
            raise RuntimeError(f"{path}: source {rel!r} is not a file inside the target directory")
