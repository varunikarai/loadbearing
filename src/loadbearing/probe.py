"""The engine: checkpoint once, fork per mutation in parallel, compare, judge."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Optional

from loadbearing.backends.base import Backend, RunResult
from loadbearing.compare import Diff, compare
from loadbearing.mutations import Mutation, plan
from loadbearing.target import Target
from loadbearing.verdict import FieldVerdict, intent_of, judge

# Given (mutation, baseline, fork) for a fork whose output moved,
# return "meaningful" or "noise". Nemotron Nano fills this role.
Classifier = Callable[[Mutation, RunResult, RunResult], str]


@dataclass
class Fork:
    mutation: Mutation
    result: RunResult
    diff: Diff
    label: Optional[str] = None  # the classifier's call on a moved diff

    @property
    def moved(self) -> bool:
        # The classifier can only veto a move it was shown, never invent one.
        return self.diff.moved and self.label != "noise"


@dataclass
class Report:
    target: str
    backend: str
    deterministic: bool
    baseline: RunResult
    forks: list[Fork]
    verdicts: list[FieldVerdict]

    @property
    def defects(self) -> list[FieldVerdict]:
        return [v for v in self.verdicts if v.defect]


def probe(
    target: Target,
    backend: Backend,
    classify: Optional[Classifier] = None,
    workers: int = 8,
) -> Report:
    mutations = plan(target.record)
    checkpoint = backend.checkpoint(target)

    # The baseline runs twice. If it disagrees with itself, no comparison below means anything.
    records = [target.record, target.record] + [m.apply(target.record) for m in mutations]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda rec: backend.run(checkpoint, target, rec), records))
    first, second, *rest = results

    forks = [Fork(m, r, compare(first, r)) for m, r in zip(mutations, rest)]
    if classify is not None:
        for fork in forks:
            if fork.diff.moved:
                fork.label = classify(fork.mutation, first, fork.result)

    verdicts = []
    for field in dict.fromkeys(m.field for m in mutations):
        moved = {f.mutation.kind: f.moved for f in forks if f.mutation.field == field}
        verdicts.append(judge(field, intent_of(field, target.expects), moved))

    return Report(
        target=target.name,
        backend=backend.name,
        deterministic=not compare(first, second).moved,
        baseline=first,
        forks=forks,
        verdicts=verdicts,
    )
