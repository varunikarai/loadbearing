"""Did a fork's output move away from the baseline, and where."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from loadbearing.backends.base import RunResult

_GONE = object()

# Stand-ins for a change that is not one output key.
EXIT = "<exit>"  # the exit code differs
STDOUT = "<stdout>"  # the output is not a JSON object, and it differs


@dataclass
class Diff:
    moved: bool
    # Output keys that changed when both sides are JSON objects, otherwise EXIT or STDOUT.
    changed: list[str] = field(default_factory=list)


def compare(baseline: RunResult, fork: RunResult, ignore: Iterable[str] = ()) -> Diff:
    """`ignore` lists output keys that vary on their own; a change there is never a move."""
    # stderr is deliberately ignored: logging noise is not behaviour.
    if baseline.exit_code != fork.exit_code:
        return Diff(True, [EXIT])
    skip = set(ignore)
    a, b = baseline.output(), fork.output()
    if isinstance(a, dict) and isinstance(b, dict):
        changed = sorted(
            k for k in a.keys() | b.keys() if k not in skip and a.get(k, _GONE) != b.get(k, _GONE)
        )
        return Diff(bool(changed), changed)
    if a != b and STDOUT not in skip:
        return Diff(True, [STDOUT])
    return Diff(False)
