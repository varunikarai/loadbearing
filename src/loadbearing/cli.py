"""Command line: `loadbearing probe`, `report`, `serve` and `models`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from loadbearing import report as report_json
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
    p.add_argument("--out", metavar="FILE", help="also save the full report as JSON")
    p.add_argument("--html", metavar="FILE", help="also save the report as a self-contained web page")
    # Contract C6: reserved now, wired as each function lands on main.
    p.add_argument("--baseline-runs", type=int, metavar="N", help="override the target's baseline_runs")
    p.add_argument("--explain", action="store_true", help="Super reconciliation and Ultra explanation per field")
    p.add_argument("--intent", action="store_true", help="Tavily intent inference for undeclared fields")
    p.add_argument("--fix", action="store_true", help="write a fix per defect (implies --explain)")
    p.add_argument("--prove", action="store_true", help="apply each fix in a fresh fork and re-probe (implies --fix)")

    r = sub.add_parser("report", help="render a saved JSON report as a web page")
    r.add_argument("report", help="a report saved with `probe --out`")
    r.add_argument("-o", "--output", metavar="FILE", help="where to write it (default: next to the report)")

    s = sub.add_parser("serve", help="the demo: list targets, run probes, serve the reports")
    s.add_argument("--targets", default="examples", help="directory of <name>/target.json")
    s.add_argument("--cache", default="runs", help="where finished runs are kept")
    s.add_argument("--backend", choices=("local", "sandbox"), default="local")
    s.add_argument("--nano", action="store_true", help="have Nemotron Nano judge each moved diff")
    s.add_argument("--readonly", action="store_true", help="serve recorded runs only, never run")
    s.add_argument("--host", default="127.0.0.1")
    # Hosting platforms say which port to bind through $PORT.
    s.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))

    m = sub.add_parser("models", help="list the Nemotron model IDs your Token Factory key can call")
    m.add_argument("--all", action="store_true", help="list every model, not only Nemotron")

    args = parser.parse_args(argv)
    try:
        if args.command == "models":
            return _models(args.all)
        if args.command == "report":
            return _report(args.report, args.output)
        if args.command == "serve":
            return _serve(args)
        return _probe(args)
    except RuntimeError as exc:
        print(f"loadbearing: {exc}", file=sys.stderr)
        return 2


# Flag -> the task that builds it. A flag leaves this map when its function is on main.
NOT_BUILT = {
    "baseline_runs": "V3",
    "explain": "V2",
    "intent": "V4",
    "fix": "V5",
    "prove": "A4",
}


def _probe(args: argparse.Namespace) -> int:
    for flag, task in NOT_BUILT.items():
        if getattr(args, flag) not in (None, False):
            raise RuntimeError(f"--{flag.replace('_', '-')} is not built yet ({task})")
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

    data = report_json.to_dict(report)
    if args.out:
        report_json.save(report, args.out)
    if args.html:
        _write_html(data, args.html)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(render(report))
    # Non-zero on any defect, so this can gate CI.
    return 1 if report.defects else 0


def _report(path: str, output: Optional[str]) -> int:
    out = output or str(Path(path).with_suffix(".html"))
    _write_html(report_json.load(path), out)
    print(out)
    return 0


def _write_html(data: dict, path: str) -> None:
    from loadbearing.html_report import render_html

    Path(path).write_text(render_html(data))


def _serve(args: argparse.Namespace) -> int:
    from loadbearing.serve import Demo, serve

    classify_factory = None
    if args.nano:
        from loadbearing.nemotron import NemotronRouter

        classify_factory = lambda: NemotronRouter.from_env(tiers=("nano",)).classify_diff  # noqa: E731
    demo = Demo(args.targets, args.cache, args.backend, args.readonly, classify_factory)
    server = serve(demo, args.host, args.port)
    mode = "read only" if args.readonly else f"runs on {args.backend}"
    print(f"loadbearing: {len(demo.targets)} target(s), {mode}, http://{args.host}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


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
