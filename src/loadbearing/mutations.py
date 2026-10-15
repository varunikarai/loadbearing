"""The mutation engine. Every mutation changes exactly one input field and nothing else."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterator

DESTROY = "destroy"
DROP = "drop"
NUDGE = "nudge"
KINDS = (DESTROY, DROP, NUDGE)


@dataclass(frozen=True)
class Mutation:
    kind: str
    field: str  # dotted path into the record, e.g. "customer.tier"

    def apply(self, record: dict) -> dict:
        """Return a mutated deep copy. The original record is never touched."""
        out = copy.deepcopy(record)
        parent, key = _parent(out, self.field)
        if self.kind == DROP:
            del parent[key]
        elif self.kind == DESTROY:
            parent[key] = destroy(parent[key])
        elif self.kind == NUDGE:
            parent[key] = nudge(parent[key])
        else:
            raise ValueError(f"unknown mutation kind: {self.kind}")
        return out

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.field}"


def plan(record: dict, kinds: tuple[str, ...] = KINDS) -> list[Mutation]:
    """One mutation per (leaf field, kind). Fields with no sensible nudge skip it."""
    mutations = []
    for field in leaf_paths(record):
        value = get(record, field)
        for kind in kinds:
            if kind == NUDGE and not nudgeable(value):
                continue
            mutations.append(Mutation(kind, field))
    return mutations


def destroy(value: Any) -> Any:
    """Template-replace: keep the type (and the length, for text), remove the content.

    An empty list or object has no content to remove, so it gets junk instead:
    a destroy that changes nothing would let an untested field read as unread."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return type(value)(0) if value else type(value)(1)
    if isinstance(value, str):
        filler = "y" if value and set(value) == {"x"} else "x"  # "xxx" destroyed must still change
        return filler * max(len(value), 1)
    if isinstance(value, list):
        return [] if value else ["x"]
    if isinstance(value, dict):
        return {} if value else {"x": "x"}
    return "x"


def nudgeable(value: Any) -> bool:
    return isinstance(value, (str, int, float)) and not isinstance(value, bool)


def nudge(value: Any) -> Any:
    """The smallest change a correct pipeline should not care about."""
    if isinstance(value, str):
        stamp = _parse_timestamp(value)
        if stamp is not None:
            # One step of the timestamp's own precision, written back in its own format.
            spec = _precision(value)
            return _format_like(value, stamp + _STEP.get(spec, timedelta(seconds=1)), spec)
        return value + " "
    if isinstance(value, bool):
        raise TypeError("booleans have no nudge")
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value * (1 + 1e-9) if value else 1e-9
    raise TypeError(f"no nudge for {type(value).__name__}")


def leaf_paths(record: dict, prefix: str = "") -> Iterator[str]:
    for key, value in record.items():
        if "." in key:
            # A path cannot tell "a.b" the key from "b" inside "a"; fail before any run, not mid-probe.
            where = f" under {prefix[:-1]}" if prefix else ""
            raise ValueError(f"record key {key!r}{where} contains a dot, which field paths use between levels")
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            yield from leaf_paths(value, path + ".")
        else:
            yield path


def get(record: dict, path: str) -> Any:
    parent, key = _parent(record, path)
    return parent[key]


def _parent(record: dict, path: str) -> tuple[dict, str]:
    *head, key = path.split(".")
    node = record
    for part in head:
        node = node[part]
    return node, key


def _parse_timestamp(text: str) -> datetime | None:
    # Date-only strings are left to the plain-text nudge, so their format survives.
    if len(text) <= 10 or not text[:4].isdigit() or text[4:5] != "-":
        return None
    try:
        return datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError:
        return None


_TIME = re.compile(r"[T ]\d{2}(:\d{2})?(:\d{2})?(\.\d+)?")
_STEP = {"hours": timedelta(hours=1), "minutes": timedelta(minutes=1)}


def _precision(text: str) -> str:
    """How finely a timestamp is written, as a datetime.isoformat timespec."""
    match = _TIME.search(text, 10)
    if not match or not match.group(1):
        return "hours"
    if not match.group(2):
        return "minutes"
    if not match.group(3):
        return "seconds"
    return "milliseconds" if len(match.group(3)) <= 4 else "microseconds"


def _format_like(original: str, stamp: datetime, spec: str = "seconds") -> str:
    out = stamp.isoformat(sep="T" if "T" in original else " ", timespec=spec)
    if original.endswith("Z"):
        out = out.replace("+00:00", "Z")
    return out
