"""Closing the loop, part two: prove a fix by re-running the probe from the same checkpoint.

The fixed files are applied to a checkpoint derived from the original, so the
only difference between the probe before and the probe after is the fix. The
proof then compares verdicts field by field: the fixed field must no longer
carry its defect, and no other field may gain one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from loadbearing.backends.base import Backend, RunResult
from loadbearing.fix import Fix
from loadbearing.probe import Classifier, Report, probe
from loadbearing.target import Target


@dataclass
class Proof:
    fix: Fix
    after: Report  # the probe re-run on the patched checkpoint
    fixed: bool  # the fix's field no longer carries the defect
    new_defects: list[str]  # fields that are defects after the fix but were not before

    @property
    def clean(self) -> bool:
        """The fix removed its defect and introduced none: the claim worth showing."""
        return self.fixed and not self.new_defects


class Pinned:
    """A backend that builds one checkpoint and reuses it for every probe.

    Used for the probe before a fix, so the proof can derive from that exact
    checkpoint, and for the probe after, on the derived one. Given no
    checkpoint, it builds one on first use, so the first probe still times the
    real build. The wrapped backend is closed by whoever opened it, not here.
    """

    def __init__(self, backend: Backend, checkpoint: Optional[Any] = None) -> None:
        self.backend = backend
        self.pinned = checkpoint
        self.name = backend.name

    def checkpoint(self, target: Target) -> Any:
        if self.pinned is None:
            self.pinned = self.backend.checkpoint(target)
        return self.pinned

    def run(self, checkpoint: Any, target: Target, record: dict) -> RunResult:
        return self.backend.run(checkpoint, target, record)

    def apply(self, checkpoint: Any, files: dict[str, str]) -> Any:
        return self.backend.apply(checkpoint, files)

    def close(self) -> None:
        pass


def prove(
    target: Target,
    backend: Backend,
    fix: Fix,
    before: Report,
    checkpoint: Optional[Any] = None,
    classify: Optional[Classifier] = None,
    workers: int = 8,
    baseline_runs: Optional[int] = None,
) -> Proof:
    """Apply `fix` to `checkpoint` (or a fresh one) and probe again.

    Pass the checkpoint `before` was probed on to prove from the identical
    snapshot. Without it, a new checkpoint is built from the same target.
    """
    outside = sorted(set(fix.files) - set(target.sources))
    if outside:
        raise ValueError(f"the fix writes {', '.join(outside)}, which the target does not list in sources")
    base = checkpoint if checkpoint is not None else backend.checkpoint(target)
    patched = backend.apply(base, fix.files)
    after = probe(
        target, Pinned(backend, patched), classify=classify, workers=workers, baseline_runs=baseline_runs
    )

    verdict = next((v for v in after.verdicts if v.field == fix.field), None)
    fixed = verdict is not None and verdict.verdict != fix.defect
    was = {v.field for v in before.defects}
    new_defects = [v.field for v in after.defects if v.field not in was]
    return Proof(fix=fix, after=after, fixed=fixed, new_defects=new_defects)
