"""Command line: `loadbearing probe <target.json>` and `loadbearing models`."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Optional

from loadbearing.backends import make_backend
from loadbearing.config import load_dotenv
from loadbearing.mutations import KINDS
from loadbearing.probe import Report, probe
from loadbearing.target import load_target


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="loadbearing",
        description="Find which inputs a pipeline is actually load-bearing on, by running it.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("probe", help="checkpoint a pipeline, fork it per mutation, report defects")
    p.add_argument("target", help="path to a target.json")
    p.add_argument("--backend", choices=("local", "sandbox"), default="local")
    p.add_argument("--nano", action="store_true", help="have Nemotron Nano judge each moved diff")
    p.add_argument("--workers", type=int, default=8, help="forks run in parallel")
    p.add_argument("--json", action="store_true", help="print the full report as JSON")

    m = sub.add_parser("models", help="list the Nemotron model IDs your Token Factory key can call")
    m.add_argument("--all", action="store_true", help="list every model, not only Nemotron")

    args = parser.parse_args(argv)
    try:
        if args.command == "models":
            return _models(args.all)
        return _probe(args)
    except RuntimeError as exc:
        print(f"loadbearing: {exc}", file=sys.stderr)
        return 2


def _probe(args: argparse.Namespace) -> int:
    target = load_target(args.target)
    classify = None
    if args.nano:
        from loadbearing.nemotron import NemotronRouter

        classify = NemotronRouter.from_env(tiers=("nano",)).classify_diff
    backend = make_backend(args.backend)
    try:
        report = probe(target, backend, classify=classify, workers=args.workers)
    finally:
        backend.close()

    if args.json:
        out = asdict(report)
        out["defects"] = [v.field for v in report.defects]
        print(json.dumps(out, indent=2))
    else:
        print(render(report))
    # Non-zero on any defect, so this can gate CI.
    return 1 if report.defects else 0


def _models(show_all: bool) -> int:
    from loadbearing.nemotron import TokenFactory

    ids = TokenFactory().list_models()
    for model_id in ids:
        if show_all or "nemotron" in model_id.lower():
            print(model_id)
    return 0


def render(report: Report) -> str:
    lines = [f"{report.target}: {len(report.forks)} forks from one checkpoint ({report.backend})"]
    lines.append(timing_line(report))
    if not report.deterministic:
        lines.append("WARNING: the baseline disagrees with itself, so no verdict below is sound.")

    rows = [("field", "intent", *KINDS, "verdict")]
    for v in report.verdicts:
        cells = ["-" if v.moved.get(k) is None else ("moved" if v.moved[k] else "same") for k in KINDS]
        rows.append((v.field, v.intent, *cells, v.verdict.upper() if v.defect else v.verdict))
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines.append("")
    lines += ["  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip() for row in rows]

    lines.append("")
    if report.defects:
        found = ", ".join(f"{v.field} ({v.verdict})" for v in report.defects)
        lines.append(f"{len(report.defects)} defect(s): {found}")
    else:
        lines.append("No defects found.")
    return "\n".join(lines)


def timing_line(report: Report) -> str:
    """Checkpoint once, then every run in parallel: the line that shows what that buys."""
    wall, total = report.fork_wall_seconds, report.fork_total_seconds
    speedup = f", {total / wall:.1f}x parallel" if wall > 0 else ""
    return (
        f"checkpoint {report.checkpoint_seconds:.2f}s, then {len(report.forks) + 2} runs "
        f"in {wall:.2f}s wall ({total:.2f}s one after another{speedup})"
    )
