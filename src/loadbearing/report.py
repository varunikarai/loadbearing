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
    proofs                     [{"field", "fixed", "new_defects", "after"}]  (A4)

Schema-1 caches are refused on load and re-run, never upgraded in place.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loadbearing.mutations import DROP, get
from loadbearing.probe import Fork, Report

SCHEMA = 1


def to_dict(report: Report) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "target": report.target,
        "backend": report.backend,
        "deterministic": report.deterministic,
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
            }
            for v in report.verdicts
        ],
        "defects": [v.field for v in report.defects],
    }


def save(report: Report, path: str | Path) -> dict[str, Any]:
    data = to_dict(report)
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
