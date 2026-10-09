"""Write every benchmark case to bench/cases/: a pipeline, its record, its target, its truth.

Deterministic: running it twice writes identical files, and a test checks the
committed cases match, so what a reader sees is exactly what was measured.

    python3 bench/generate.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from string import Template

import domains as d

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
SILENT, PHANTOM = "silent passthrough", "phantom sensitivity"
# Real pipelines often log the request id; harmless, since stderr is not output.
LOGS_ID = {"triage", "shipping"}


def typo(name: str) -> str:
    """Swap the two middle letters: body -> bdoy, the kind of slip review misses."""
    i = len(name) // 2 - 1
    return name[:i] + name[i + 1] + name[i] + name[i + 2:]


def phantom_line(kind: str, id_field: str, ts_field: str) -> str:
    return {
        "ts_leak": f'out["queue"] = out["queue"] + "-" + str(datetime.fromisoformat(r["{ts_field}"]).second % 3)',
        "id_bucket": f'out["variant"] = "A" if sum(map(ord, r["{id_field}"])) % 2 else "B"',
        "echo": f'out["ref"] = r.get("{id_field}")',
    }[kind]


def cases() -> dict[str, dict]:
    out = {}
    for name, (template, record, relevant, id_field, ts_field, alias) in d.DOMAINS.items():
        base = {f"K_{f}": repr(f) for f in relevant} | {f"OVER_{f}": "" for f in relevant}
        base["PHANTOM"] = ""
        base["LOG"] = f'print("handling", r.get("{id_field}"), file=sys.stderr)' if name in LOGS_ID else ""
        variants = {"clean": ({}, {}, "clean")}
        for f in relevant:
            variants[f"typo_{f}"] = ({f"K_{f}": repr(typo(f))}, {f: SILENT}, "typo")
            variants[f"stale_{f}"] = ({f"K_{f}": repr(alias[f])}, {f: SILENT}, "stale key")
            variants[f"overwrite_{f}"] = ({f"OVER_{f}": f"{d.VARIABLE[f]} = {d.OVERWRITE[f]}  # normalised upstream"},
                                          {f: SILENT}, "overwritten")
        for kind, field in (("ts_leak", ts_field), ("id_bucket", id_field), ("echo", id_field)):
            variants[kind] = ({"PHANTOM": phantom_line(kind, id_field, ts_field)}, {field: PHANTOM},
                              {"ts_leak": "timestamp leak", "id_bucket": "id bucketing", "echo": "id echoed"}[kind])
        for variant, (slots, truth, operator) in variants.items():
            source = Template(template).substitute(base | slots)
            source = "\n".join(line for line in source.splitlines() if line.strip() != "") + "\n"
            out[f"{name}-{variant}"] = dict(source=source, record=record, relevant=relevant,
                                            irrelevant=[id_field, ts_field], truth=truth, operator=operator)
    for label, (source, record, relevant, id_field, _), truth, operator in (
        ("limit-threshold", d.LIMIT_THRESHOLD, {}, "threshold-only field (correct code)"),
        ("limit-keyword", d.LIMIT_KEYWORD, {"ticket_id": PHANTOM}, "value-specific leak"),
    ):
        out[label] = dict(source=source, record=record, relevant=relevant, irrelevant=[id_field],
                          truth=truth, operator=operator)
    return out


def write() -> int:
    if CASES.exists():
        shutil.rmtree(CASES)
    for name, case in cases().items():
        folder = CASES / name
        folder.mkdir(parents=True)
        (folder / "pipeline.py").write_text(case["source"])
        (folder / "record.json").write_text(json.dumps(case["record"], indent=2) + "\n")
        (folder / "target.json").write_text(json.dumps({
            "name": name, "files": ["pipeline.py"], "command": "python3 pipeline.py input.json",
            "record": "record.json",
            "expects": {"relevant": case["relevant"], "irrelevant": case["irrelevant"]},
        }, indent=2) + "\n")
        (folder / "truth.json").write_text(json.dumps(
            {"defects": case["truth"], "operator": case["operator"]}, indent=2) + "\n")
    return len(list(CASES.iterdir()))


if __name__ == "__main__":
    print(f"wrote {write()} cases to {CASES.relative_to(HERE.parent)}")
