"""A probe report as plain JSON: what the HTML report, the demo server and CI read.

The schema is versioned so a cached report from an older run is never
silently misread. Everything a viewer needs to check a verdict is in it:
the baseline input, what each fork changed it to, and what came out.

Schema 2 (contract C5, built in A5) adds, each null or empty when the step
did not run, so a schema-2 reader handles a plain probe unchanged:

    verdicts[].reconciliation  str or null   Super's statement for the field (V2)
    verdicts[].explanation     str or null   Ultra's account of the code path (V2)
    verdicts[].intent_source   "declared" | "inferred" | "undeclared"     (V4)
    verdicts[].evidence        {"intent", "quote", "url"} or null           (V4)
    baseline_runs              int, how often the baseline ran              (V3)
    unstable_keys              [str], output keys that vary on their own    (V3)
    fixes                      [{"field", "defect", "files", "rationale", "diff"}]   (V5, A4)
    proofs                     [{"field", "fixed", "new_defects", "clean", "after"}]  (A4)
    rejected_fixes             [{"field", "reason"}], fixes the writer refused        (A4)
    void                       bool, nothing stable was left to judge               (V3)

`after` in a proof is the re-run probe, in this same schema, without its own
fixes or proofs.

Schema-1 caches are refused on load and re-run, never upgraded in place.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Optional

from loadbearing.mutations import DROP, get
from loadbearing.probe import Fork, Report

if TYPE_CHECKING:
    from loadbearing.prove import Loop
    from loadbearing.target import Target

SCHEMA = 2


def to_dict(
    report: Report, loop: Optional[Loop] = None, target: Optional[Target] = None
) -> dict[str, Any]:
    """`loop` is what --fix or --prove produced; `target` lets each fix carry its diff."""
    data = _probe_dict(report)
    data["fixes"] = [
        {
            "field": f.field,
            "defect": f.defect,
            "files": f.files,
            "rationale": f.rationale,
            "diff": f.diff(target) if target is not None else "",
        }
        for f in (loop.fixes if loop else [])
    ]
    data["proofs"] = [
        {
            "field": p.fix.field,
            "fixed": p.fixed,
            "new_defects": p.new_defects,
            "clean": p.clean,
            "after": _probe_dict(p.after),
        }
        for p in (loop.proofs if loop else [])
    ]
    data["rejected_fixes"] = [
        {"field": field, "reason": reason} for field, reason in (loop.rejected if loop else [])
    ]
    return data


def _probe_dict(report: Report) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "target": report.target,
        "backend": report.backend,
        "deterministic": report.deterministic,
        "void": report.void,
        "baseline_runs": report.baseline_runs,
        "unstable_keys": report.unstable_keys,
        "timing": {
            "checkpoint_seconds": report.checkpoint_seconds,
            "fork_wall_seconds": report.fork_wall_seconds,
            "fork_total_seconds": report.fork_total_seconds,
            "runs": len(report.forks) + report.baseline_runs,
        },
        "record": report.record,
        "baseline": _run(report.baseline),
        "forks": [_fork(f, report.record) for f in report.forks],
        "verdicts": [
            {
                "field": v.field,
                "intent": v.intent,
                "moved": v.moved,
                "verdict": v.verdict,
                "defect": v.defect,
                "intent_source": v.intent_source,
                "evidence": asdict(v.evidence) if v.evidence else None,
                "reconciliation": v.reconciliation,
                "explanation": v.explanation,
            }
            for v in report.verdicts
        ],
        "defects": [v.field for v in report.defects],
    }


def save(
    report: Report, path: str | Path, loop: Optional[Loop] = None, target: Optional[Target] = None
) -> dict[str, Any]:
    data = to_dict(report, loop, target)
    Path(path).write_text(json.dumps(data, indent=2))
    return data


def load(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if data.get("schema") != SCHEMA:
        raise RuntimeError(f"{path}: report schema {data.get('schema')}, expected {SCHEMA}; re-run the probe")
    return data


def _fork(fork: Fork, record: dict) -> dict[str, Any]:
    m = fork.mutation
    return {
        "label": m.label,
        "kind": m.kind,
        "field": m.field,
        # What the field held in this fork. A dropped field holds nothing.
        "value": None if m.kind == DROP else get(m.apply(record), m.field),
        "moved": fork.moved,
        "changed": fork.diff.changed,
        "classifier": fork.label,
        **_run(fork.result),
    }


def _run(result) -> dict[str, Any]:
    return {
        "exit_code": result.exit_code,
        "output": result.output(),
        "seconds": result.seconds,
    }
