"""A target file says how to run a pipeline and what its inputs are supposed to mean."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


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


def load_target(path: str | Path) -> Target:
    path = Path(path).resolve()
    spec = json.loads(path.read_text())
    root = path.parent
    expects = spec.get("expects", {})
    return Target(
        name=spec.get("name", root.name),
        root=root,
        image=spec.get("image", "python:3.12-slim"),
        setup=spec.get("setup", ""),
        files=list(spec.get("files", [])),
        command=spec["command"],
        record=json.loads((root / spec["record"]).read_text()),
        expects={
            "relevant": list(expects.get("relevant", [])),
            "irrelevant": list(expects.get("irrelevant", [])),
        },
        timeout=float(spec.get("timeout", 60)),
    )
