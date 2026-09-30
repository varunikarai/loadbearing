"""Did a fork's output move away from the baseline, and where."""

from __future__ import annotations

from dataclasses import dataclass, field

from loadbearing.backends.base import RunResult

_GONE = object()


@dataclass
class Diff:
    moved: bool
    # Output keys that changed when both sides are JSON objects,
    # otherwise "<exit>" or "<stdout>".
    changed: list[str] = field(default_factory=list)


def compare(baseline: RunResult, fork: RunResult) -> Diff:
    # stderr is deliberately ignored: logging noise is not behaviour.
    if baseline.exit_code != fork.exit_code:
        return Diff(True, ["<exit>"])
    a, b = baseline.output(), fork.output()
    if isinstance(a, dict) and isinstance(b, dict):
        changed = sorted(k for k in a.keys() | b.keys() if a.get(k, _GONE) != b.get(k, _GONE))
        return Diff(bool(changed), changed)
    if a != b:
        return Diff(True, ["<stdout>"])
    return Diff(False)
