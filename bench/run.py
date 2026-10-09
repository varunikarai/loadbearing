"""Run every detector on every benchmark case and write bench/RESULTS.md.

    PYTHONPATH=src python3 bench/run.py            Loadbearing and the static check, offline
    PYTHONPATH=src python3 bench/run.py --llm      also Nemotron reading the code (needs keys)

Scoring unit: one declared field in one case. Its truth is "silent passthrough",
"phantom sensitivity" or nothing. A detector is right on a unit when its call
matches the truth exactly; calling the wrong defect class counts as both a
false positive and a false negative.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from loadbearing.backends.local import LocalBackend  # noqa: E402
from loadbearing.probe import probe  # noqa: E402
from loadbearing.target import load_target  # noqa: E402

SILENT, PHANTOM = "silent passthrough", "phantom sensitivity"
CLASSES = (SILENT, PHANTOM)


def loadbearing(case: Path) -> dict[str, str]:
    backend = LocalBackend()
    try:
        report = probe(load_target(case / "target.json"), backend)
    finally:
        backend.close()
    return {v.field: v.verdict for v in report.defects}


def static(case: Path) -> dict[str, str]:
    """The cheap check a reviewer might script: is each field's name referenced in the code?

    A relevant field never named is a silent passthrough; an irrelevant field that is
    named somewhere is a phantom sensitivity.
    """
    source = (case / "pipeline.py").read_text()
    expects = json.loads((case / "target.json").read_text())["expects"]
    named = lambda f: f"'{f}'" in source or f'"{f}"' in source  # noqa: E731
    calls = {f: SILENT for f in expects["relevant"] if not named(f)}
    calls |= {f: PHANTOM for f in expects["irrelevant"] if named(f)}
    return calls


LLM_SYSTEM = (
    "You review a data pipeline's source code. You are told which input fields should change "
    "its output and which should not. Report every field that should matter but whose value "
    "can never reach the output (silent passthrough), and every field that should not matter "
    "but can change the output (phantom sensitivity). Reply with one JSON object and nothing "
    'else: {"defects": [{"field": "<name>", "defect": "silent passthrough" | "phantom sensitivity"}]}'
)


def llm_review(case: Path, client, model: str) -> dict[str, str]:
    """Nemotron reads the code instead of running it: the baseline that matters most."""
    expects = json.loads((case / "target.json").read_text())["expects"]
    prompt = (
        f"Should change the output: {', '.join(expects['relevant'])}\n"
        f"Should not change the output: {', '.join(expects['irrelevant'])}\n\n"
        f"--- pipeline.py\n{(case / 'pipeline.py').read_text()}"
    )
    reply = client.chat(model, [{"role": "system", "content": LLM_SYSTEM},
                                {"role": "user", "content": prompt}], max_tokens=1024)
    start, end = reply.find("{"), reply.rfind("}")
    try:
        items = json.loads(reply[start:end + 1]).get("defects", [])
    except ValueError:
        return {}
    return {i["field"]: i["defect"] for i in items
            if isinstance(i, dict) and i.get("defect") in CLASSES and isinstance(i.get("field"), str)}


def units(case: Path) -> list[tuple[str, str]]:
    expects = json.loads((case / "target.json").read_text())["expects"]
    truth = json.loads((case / "truth.json").read_text())["defects"]
    return [(f, truth.get(f, "")) for f in expects["relevant"] + expects["irrelevant"]]


def score(results: dict[str, dict[str, str]], cases: list[Path]) -> dict:
    out = {}
    for cls in CLASSES + ("all",):
        tp = fp = fn = 0
        for case in cases:
            calls = results[case.name]
            for field, truth in units(case):
                call = calls.get(field, "")
                if cls != "all" and cls not in (truth, call):
                    continue
                if call and call == truth:
                    tp += 1
                else:
                    fp += bool(call)
                    fn += bool(truth)
        p = tp / (tp + fp) if tp + fp else 1.0
        r = tp / (tp + fn) if tp + fn else 1.0
        out[cls] = dict(tp=tp, fp=fp, fn=fn, precision=p, recall=r)
    return out


def mcnemar(a: dict, b: dict, cases: list[Path]) -> tuple[int, int, float]:
    """Exact two-sided McNemar test on paired per-field calls: (a right & b wrong, the reverse, p)."""
    only_a = only_b = 0
    for case in cases:
        for field, truth in units(case):
            ra, rb = a[case.name].get(field, "") == truth, b[case.name].get(field, "") == truth
            only_a += ra and not rb
            only_b += rb and not ra
    n, k = only_a + only_b, min(only_a, only_b)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return only_a, only_b, p


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="also run Nemotron reading the code")
    args = parser.parse_args()
    cases = sorted(p for p in (HERE / "cases").iterdir() if p.is_dir())
    detectors = {"Loadbearing (runs it)": loadbearing, "Static name check (reads it)": static}
    if args.llm:
        from loadbearing.config import load_dotenv
        from loadbearing.nemotron import TokenFactory

        load_dotenv()
        client, model = TokenFactory(), os.environ["NEMOTRON_SUPER_MODEL"]
        detectors[f"Nemotron reads the code ({model})"] = lambda c: llm_review(c, client, model)
    results, seconds = {}, {}
    for name, fn in detectors.items():
        start = time.perf_counter()
        results[name] = {case.name: fn(case) for case in cases}
        seconds[name] = time.perf_counter() - start
    scores = {name: score(r, cases) for name, r in results.items()}
    lb, *others = list(results)
    tests = {other: mcnemar(results[lb], results[other], cases) for other in others}
    (HERE / "results.json").write_text(json.dumps(
        {"cases": len(cases), "scores": scores, "mcnemar": tests,
         "calls": results, "seconds": seconds}, indent=2, sort_keys=True) + "\n")
    (HERE / "RESULTS.md").write_text(render(cases, results, scores, tests, seconds))
    print((HERE / "RESULTS.md").read_text())
    return 0


def render(cases, results, scores, tests, seconds) -> str:
    n_units = sum(len(units(c)) for c in cases)
    n_bugs = sum(1 for c in cases for _, t in units(c) if t)
    lines = [
        "# Benchmark results",
        "",
        f"Generated by `bench/run.py` on {len(cases)} cases ({n_units} declared fields, {n_bugs} planted "
        "defects). See [README.md](README.md) for how the cases are built and what this does and "
        "does not show.",
        "",
        "| detector | defects found | missed | false alarms | precision | recall | seconds |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, s in scores.items():
        a = s["all"]
        lines.append(f"| {name} | {a['tp']} | {a['fn']} | {a['fp']} | {a['precision']:.0%} | "
                     f"{a['recall']:.0%} | {seconds[name]:.1f} |")
    lines += ["", "By defect class:", "", "| detector | class | found | missed | false alarms |", "|---|---|---|---|---|"]
    for name, s in scores.items():
        for cls in CLASSES:
            c = s[cls]
            lines.append(f"| {name} | {cls} | {c['tp']} | {c['fn']} | {c['fp']} |")
    lines += ["", "Paired on every field (exact McNemar test):", ""]
    lb = next(iter(results))
    for other, (a, b, p) in tests.items():
        lines.append(f"- {lb} right where {other} was wrong: **{a}** fields; the reverse: **{b}**; p = {p:.2g}.")
    lines += ["", "Every case, and what each detector called:", "",
              "| case | planted | " + " | ".join(results) + " |", "|---|---|" + "---|" * len(results)]
    for case in cases:
        truth = json.loads((case / "truth.json").read_text())
        planted = ", ".join(f"`{f}` {t}" for f, t in truth["defects"].items()) or "none"
        cells = []
        for name in results:
            calls = results[name][case.name]
            right = all(calls.get(f, "") == t for f, t in units(case))
            shown = ", ".join(f"`{f}`" for f in calls) or "none"
            cells.append(("✅ " if right else "❌ ") + shown)
        lines.append(f"| `{case.name}` | {planted} ({truth['operator']}) | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
