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
from loadbearing.prove import Loop, Pinned, close_loop
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
    p.add_argument("--markdown", metavar="FILE", help="also append a Markdown summary (e.g. $GITHUB_STEP_SUMMARY)")
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
# Every flag reserved in contract C6 is built now.
NOT_BUILT: dict[str, str] = {}


def _probe(args: argparse.Namespace) -> int:
    for flag, task in NOT_BUILT.items():
        if getattr(args, flag) not in (None, False):
            raise RuntimeError(f"--{flag.replace('_', '-')} is not built yet ({task})")
    target = load_target(args.target)
    explain = args.explain or args.fix or args.prove  # C6: --fix implies --explain
    # One router, with exactly the tiers these flags use, built before any run so a
    # missing model ID or key fails before a single credit is spent.
    tiers = sorted(
        ({"nano"} if args.nano else set())
        | ({"super", "ultra"} if explain else set())
        | ({"super"} if args.intent else set())
        | ({"ultra"} if args.fix or args.prove else set())
    )
    router = None
    if tiers:
        from loadbearing.nemotron import NemotronRouter

        router = NemotronRouter.from_env(tiers=tuple(tiers))
    classify = router.classify_diff if args.nano else None
    inferred = None
    if args.intent:
        from loadbearing.intent import infer_expects

        inferred = infer_expects(target, router)  # Tavily, then Super; cached under runs/
    backend = make_backend(args.backend)
    loop = None
    try:
        # One checkpoint for the probe and every proof, so a fix is the only difference.
        pinned = Pinned(backend)
        report = probe(
            target, pinned, classify=classify, workers=args.workers, baseline_runs=args.baseline_runs,
            explain_with=router if explain else None, inferred=inferred,
        )
        if (args.fix or args.prove) and report.defects:
            loop = close_loop(
                target, backend, report, router, checkpoint=pinned.pinned, prove_fixes=args.prove,
                classify=classify, workers=args.workers, baseline_runs=args.baseline_runs,
                inferred=inferred,
            )
    finally:
        backend.close()

    data = report_json.to_dict(report, loop, target)
    if args.out:
        Path(args.out).write_text(json.dumps(data, indent=2))
    if args.html:
        _write_html(data, args.html)
    if args.markdown:
        from loadbearing.markdown_report import render_markdown

        with open(args.markdown, "a") as fh:  # append: a job summary may hold several probes
            fh.write(render_markdown(data) + "\n")
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(render(report))
        if loop is not None:
            print(render_loop(loop, target))
    # Non-zero on any defect in the pipeline as given, so this can gate CI.
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
    if report.void:
        lines.append("WARNING: every output key varies on its own, so no verdict below is sound.")
    elif report.unstable_keys:
        # An LLM target is expected to land here: the noise floor removed these, the rest is judged.
        lines.append(
            f"noise floor: {report.baseline_runs} baseline runs; varies on its own, not judged: "
            + ", ".join(report.unstable_keys)
        )

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


def render_loop(loop: Loop, target) -> str:
    """The fix and its proof per defect, then whatever could not be fixed."""
    lines = []
    for fix in loop.fixes:
        lines += ["", f"fix for {fix.field} ({fix.defect}): {fix.rationale}", fix.diff(target).rstrip()]
        proof = next((p for p in loop.proofs if p.fix is fix), None)
        if proof is None:
            continue
        after = next((v.verdict for v in proof.after.verdicts if v.field == fix.field), "gone")
        if proof.clean:
            lines.append(f"proof: {fix.field} is now {after}, and no other field gained a defect.")
        elif not proof.fixed:
            lines.append(f"proof: FAILED, {fix.field} is still {after}.")
        else:
            lines.append(
                f"proof: {fix.field} is now {after}, but the fix adds defects on "
                + ", ".join(proof.new_defects)
            )
    for field, reason in loop.rejected:
        lines += ["", f"no fix for {field}: {reason}"]
    return "\n".join(lines)


def timing_line(report: Report) -> str:
    """Checkpoint once, then every run in parallel: the line that shows what that buys."""
    wall, total = report.fork_wall_seconds, report.fork_total_seconds
    speedup = f", {total / wall:.1f}x parallel" if wall > 0 else ""
    return (
        f"checkpoint {report.checkpoint_seconds:.2f}s, then {len(report.forks) + report.baseline_runs} runs "
        f"in {wall:.2f}s wall ({total:.2f}s one after another{speedup})"
    )
