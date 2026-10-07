"""The noise floor: which output keys move with no mutation at all.

An LLM pipeline's output varies on its own. Running the unmutated record
several times shows which keys do, so a fork's change in one of them is never
mistaken for the mutated field mattering. Every other key is still judged.
"""

from __future__ import annotations

from loadbearing.backends.base import RunResult
from loadbearing.compare import EXIT, STDOUT, compare


def unstable_keys(baselines: list[RunResult]) -> list[str]:
    """Output keys that differ between any two runs of the same, unmutated record."""
    first, *others = baselines
    unstable: set[str] = set()
    for other in others:
        unstable.update(compare(first, other).changed)
    return sorted(unstable)


def void(unstable: list[str], baseline: RunResult) -> bool:
    """True when nothing stable is left to judge, so no verdict can be trusted."""
    if EXIT in unstable or STDOUT in unstable:
        return True
    output = baseline.output()
    return isinstance(output, dict) and bool(output) and set(output) <= set(unstable)
