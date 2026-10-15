"""The engine: checkpoint once, fork per mutation in parallel, compare, judge."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from loadbearing.backends.base import Backend, RunResult
from loadbearing import noise
from loadbearing.compare import Diff, compare
from loadbearing.fix import read_sources
from loadbearing.mutations import Mutation, plan
from loadbearing.target import Target
from loadbearing.verdict import INFERRED, IRRELEVANT, UNDECLARED, Evidence, FieldVerdict, intent_of, judge

# Given (mutation, baseline, fork) for a fork whose output moved,
# return "meaningful" or "noise". Nemotron Nano fills this role.
Classifier = Callable[[Mutation, RunResult, RunResult], str]

# On a pipeline the noise floor shows is not deterministic, a fork that moved on a field that
# should not matter runs this many more times, and counts as moved only if most of its runs
# moved. One sampling fluke is then not reported as a phantom sensitivity. Only those forks:
# on a field that should matter a move is not a defect claim, and demanding a majority there
# would turn a real but unreliable reading into a silent passthrough.
CONFIRM_RUNS = 2


@dataclass
class Fork:
    mutation: Mutation
    result: RunResult
    diff: Diff
    label: Optional[str] = None  # the classifier's call on a moved diff
    runs: int = 1  # how often this mutation ran: more than once when a move was confirmed
    moves: int = 1  # how many of those runs moved

    @property
    def moved(self) -> bool:
        # The classifier can only veto a move it was shown, never invent one.
        return self.diff.moved and self.label != "noise" and 2 * self.moves > self.runs


@dataclass
class Report:
    target: str
    backend: str
    deterministic: bool
    baseline: RunResult
    forks: list[Fork]
    verdicts: list[FieldVerdict]
    checkpoint_seconds: float = 0.0
    # Wall time of the parallel phase: both baselines and every fork.
    fork_wall_seconds: float = 0.0
    # The sum of every run in that phase: what it would cost one after another.
    fork_total_seconds: float = 0.0
    record: dict = field(default_factory=dict)  # the baseline input every fork mutated
    baseline_runs: int = 2  # how often the unmutated record ran
    unstable_keys: list[str] = field(default_factory=list)  # output keys that vary on their own

    @property
    def defects(self) -> list[FieldVerdict]:
        return [v for v in self.verdicts if v.defect]

    @property
    def void(self) -> bool:
        """Nothing stable was left to judge, so no verdict in this report can be trusted."""
        return noise.void(self.unstable_keys, self.baseline)


def probe(
    target: Target,
    backend: Backend,
    classify: Optional[Classifier] = None,
    workers: int = 8,
    baseline_runs: Optional[int] = None,
    explain_with: Optional[Any] = None,
    inferred: Optional[dict[str, Evidence]] = None,
) -> Report:
    """`baseline_runs` overrides the target's own setting (the --baseline-runs flag).
    `explain_with` is a Nemotron router: each defect gets Super's statement and
    Ultra's account of the code path (the --explain flag). `inferred` maps
    undeclared fields to intents drawn from the docs (the --intent flag); a
    declared intent always wins over an inferred one."""
    runs = baseline_runs if baseline_runs is not None else target.baseline_runs
    if runs < 2:
        raise ValueError("baseline_runs must be 2 or more: one run cannot show what varies")
    mutations = plan(target.record)
    started = time.perf_counter()
    checkpoint = backend.checkpoint(target)
    checkpointed = time.perf_counter()

    def run(record: dict) -> RunResult:
        start = time.perf_counter()
        result = backend.run(checkpoint, target, record)
        result.seconds = time.perf_counter() - start
        return result

    # The unmutated record runs `runs` times alongside the forks. Output keys that
    # differ between those runs vary on their own, so the forks are judged without them.
    records = [target.record] * runs + [m.apply(target.record) for m in mutations]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, records))
        baselines, rest = results[:runs], results[runs:]
        first = baselines[0]
        unstable = noise.unstable_keys(baselines)
        forks = []
        for m, r in zip(mutations, rest):
            diff = compare(first, r, ignore=unstable)
            forks.append(Fork(m, r, diff, moves=int(diff.moved)))
        if unstable:
            suspect = [
                f for f in forks
                if f.diff.moved and _intent(f.mutation.field, target, inferred)[0] == IRRELEVANT
            ]
            results += _confirm(suspect, target, first, unstable, run, pool)
    forked = time.perf_counter()
    if classify is not None:
        for fork in forks:
            if fork.diff.moved:
                fork.label = classify(fork.mutation, first, fork.result)

    verdicts = []
    for field in dict.fromkeys(m.field for m in mutations):
        moved = {f.mutation.kind: f.moved for f in forks if f.mutation.field == field}
        intent, evidence = _intent(field, target, inferred)
        verdict = judge(field, intent, moved)
        if evidence:
            verdict.intent_source, verdict.evidence = INFERRED, evidence
        verdicts.append(verdict)
    if explain_with is not None:
        explain_defects(verdicts, target, explain_with)

    return Report(
        target=target.name,
        backend=backend.name,
        deterministic=not unstable,
        baseline=first,
        forks=forks,
        verdicts=verdicts,
        checkpoint_seconds=checkpointed - started,
        fork_wall_seconds=forked - checkpointed,
        fork_total_seconds=sum(r.seconds for r in results),
        record=target.record,
        baseline_runs=runs,
        unstable_keys=unstable,
    )


def _intent(field: str, target: Target, inferred: Optional[dict[str, Evidence]]) -> tuple[str, Optional[Evidence]]:
    """What a field is judged against: its declared intent, else one inferred from the docs."""
    intent = intent_of(field, target.expects)
    evidence = (inferred or {}).get(field) if intent == UNDECLARED else None
    return (evidence.intent if evidence else intent), evidence


def _confirm(moved: list[Fork], target: Target, first: RunResult, unstable: list[str], run, pool) -> list[RunResult]:
    """Run each moved fork CONFIRM_RUNS more times and count how often it moves again."""
    again = list(pool.map(run, [f.mutation.apply(target.record) for f in moved for _ in range(CONFIRM_RUNS)]))
    for i, fork in enumerate(moved):
        reruns = again[i * CONFIRM_RUNS : (i + 1) * CONFIRM_RUNS]
        fork.runs += len(reruns)
        fork.moves += sum(compare(first, r, ignore=unstable).moved for r in reruns)
    return again


def explain_defects(verdicts: list[FieldVerdict], target: Target, router: Any) -> None:
    """Super's statement and Ultra's account of the code path, for defects only:
    a field that behaves as intended needs no explaining, and every call costs."""
    defects = [v for v in verdicts if v.defect]
    if not defects:
        return
    source = "\n\n".join(f"--- {rel}\n{text}" for rel, text in read_sources(target).items())
    for verdict in defects:
        verdict.reconciliation = router.reconcile(verdict)
        verdict.explanation = router.explain(verdict, source)
