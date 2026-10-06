"""Render a probe report as one self-contained HTML page.

No scripts, fonts or stylesheets are fetched, so a saved report still opens
offline and a hosted one cannot rot. Every string that came out of a run is
escaped: a pipeline's output is untrusted and lands in this page verbatim.
"""

from __future__ import annotations

import json
from html import escape
from typing import Any

from loadbearing.mutations import KINDS
from loadbearing.verdict import PHANTOM_SENSITIVITY, SILENT_PASSTHROUGH

_CLIP = 160

_CSS = """
:root{--bg:#0b0b0c;--panel:#141416;--line:#26262a;--text:#f3f3f1;--dim:#8d8d93;
--moved:#c8ff3d;--same:#3a3a40;--silent:#ff4d4d;--phantom:#ffb020;--ok:#c8ff3d}
@media (prefers-color-scheme:light){:root{--bg:#fafaf7;--panel:#fff;--line:#e4e4df;--text:#111;
--dim:#6b6b70;--moved:#4c8a00;--same:#cfcfca;--silent:#d62828;--phantom:#c77700;--ok:#4c8a00}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:16px/1.5 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
main{max-width:1040px;margin:0 auto;padding:40px 16px 80px}
.brand{font-weight:900;letter-spacing:-.02em;font-size:15px;color:var(--dim)}
.brand b{color:var(--text)}
h1{font-size:clamp(34px,6vw,64px);font-weight:900;letter-spacing:-.035em;line-height:1;margin:14px 0 12px}
.lede{font-size:clamp(18px,2.4vw,24px);font-weight:700;letter-spacing:-.01em;margin:0 0 32px;max-width:46ch}
.lede .n{color:var(--silent)}
h2{font-size:22px;font-weight:850;letter-spacing:-.02em;margin:48px 0 14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.stat .v{font-size:34px;font-weight:900;letter-spacing:-.03em;line-height:1.1}
.stat .k{color:var(--dim);font-weight:600;font-size:14px;margin-top:4px}
.stat.bad .v{color:var(--silent)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;overflow-x:auto}
svg{display:block;width:100%;height:auto;min-width:560px}
svg text{font-family:inherit}
table{border-collapse:collapse;width:100%;font-size:15px}
th{text-align:left;color:var(--dim);font-weight:700;font-size:13px;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:10px;border-bottom:1px solid var(--line);font-weight:600}
td.f{font-weight:800}
.cell{display:inline-block;min-width:64px;text-align:center;border-radius:8px;padding:2px 8px;font-size:13px;font-weight:800}
.cell.moved{background:var(--moved);color:#0b0b0c}
.cell.same{background:transparent;border:1.5px solid var(--same);color:var(--dim)}
.badge{font-weight:900;font-size:13px;letter-spacing:.01em;border-radius:999px;padding:3px 10px;white-space:nowrap}
.badge.silent{background:var(--silent);color:#fff}
.badge.phantom{background:var(--phantom);color:#111}
.badge.plain{color:var(--dim);border:1.5px solid var(--same)}
.card{background:var(--panel);border:1px solid var(--line);border-left:6px solid var(--silent);
border-radius:16px;padding:20px 22px;margin:14px 0}
.card.phantom{border-left-color:var(--phantom)}
.card h3{margin:0 0 6px;font-size:22px;font-weight:900;letter-spacing:-.02em}
.card p{margin:0 0 14px;color:var(--text);font-weight:500;max-width:70ch}
.pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.out{border:1px solid var(--line);border-radius:12px;padding:12px 14px;min-width:0}
.out .t{color:var(--dim);font-weight:700;font-size:13px;margin-bottom:6px}
.kv{font:13px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,monospace;word-break:break-word}
.kv .hit{background:color-mix(in srgb,var(--phantom) 28%,transparent);border-radius:4px;padding:0 3px}
.kv .key{color:var(--dim)}
pre{margin:0;white-space:pre-wrap;word-break:break-word;font:13px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,monospace}
details{margin-top:12px}summary{cursor:pointer;font-weight:800}
.warn{background:var(--silent);color:#fff;font-weight:800;border-radius:12px;padding:12px 16px;margin:0 0 24px}
footer{margin-top:56px;color:var(--dim);font-size:13px;font-weight:600}
"""


def render_html(data: dict[str, Any]) -> str:
    defects = [v for v in data["verdicts"] if v["defect"]]
    n = len(defects)
    if n:
        lede = (
            f'<span class="n">{n} input{"s" if n != 1 else ""}</span> '
            f'{"do" if n != 1 else "does"} not do what the pipeline claims. '
            "Found by running it, not by reading it."
        )
    else:
        lede = "Every declared input does what the pipeline claims. Found by running it."
    parts = [
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        '<meta name=viewport content="width=device-width,initial-scale=1">',
        f"<title>{escape(data['target'])} · Loadbearing</title><style>{_CSS}</style></head><body><main>",
        '<div class="brand"><b>Loadbearing</b> · checkpoint once, fork per mutation</div>',
        f"<h1>{escape(data['target'])}</h1>",
        f'<p class="lede">{lede}</p>',
    ]
    if not data["deterministic"]:
        parts.append(
            '<div class="warn">The baseline disagreed with itself, so no verdict below is sound.</div>'
        )
    parts += [
        _stats(data),
        "<h2>One checkpoint, every fork</h2>",
        f'<div class="panel">{fork_tree_svg(data)}</div>',
        "<h2>Every field, every mutation</h2>",
        f'<div class="panel">{_matrix(data)}</div>',
    ]
    if defects:
        parts.append("<h2>The evidence</h2>")
        parts += [_evidence(v, data) for v in defects]
    parts += [
        "<h2>Baseline</h2>",
        '<div class="pair">',
        f'<div class="out"><div class="t">input</div>{_value_block(data["record"])}</div>',
        f'<div class="out"><div class="t">output</div>{_value_block(data["baseline"]["output"])}</div>',
        "</div>",
        f"<footer>Backend: {escape(data['backend'])} · "
        f"baseline {'deterministic' if data['deterministic'] else 'NOT deterministic'} · "
        f"report schema {data['schema']}</footer>",
        "</main></body></html>",
    ]
    return "\n".join(parts)


def _stats(data: dict[str, Any]) -> str:
    t = data["timing"]
    wall, total = t["fork_wall_seconds"], t["fork_total_seconds"]
    speed = f"{total / wall:.1f}x" if wall > 0 else "-"
    n = len(data["defects"])
    tiles = [
        (str(len(data["forks"])), "forks from one checkpoint", ""),
        (f"{wall:.2f}s", f"all {t['runs']} runs, in parallel ({total:.2f}s one after another)", ""),
        (speed, "faster than running them in sequence", ""),
        (str(n), "defect" if n == 1 else "defects", "bad" if n else ""),
    ]
    cells = "".join(
        f'<div class="stat {cls}"><div class="v">{escape(v)}</div><div class="k">{escape(k)}</div></div>'
        for v, k, cls in tiles
    )
    return f'<div class="stats">{cells}</div>'


def fork_tree_svg(data: dict[str, Any]) -> str:
    """The checkpoint on the left, every fork on the right, grouped by field."""
    verdicts = {v["field"]: v for v in data["verdicts"]}
    groups: dict[str, list[dict]] = {}
    for fork in data["forks"]:
        groups.setdefault(fork["field"], []).append(fork)

    row, gap, top = 30, 18, 16
    height = top * 2 + row * len(data["forks"]) + gap * max(len(groups) - 1, 0)
    root_x, root_y, node_x = 120, height / 2, 470
    out = [
        f'<svg viewBox="0 0 960 {height:.0f}" role="img" '
        f'aria-label="One checkpoint forked into {len(data["forks"])} runs">'
    ]
    nodes, y = [], top
    for field, forks in groups.items():
        v = verdicts.get(field, {})
        colour = _verdict_colour(v.get("verdict", ""))
        first_y = y
        for fork in forks:
            cy = y + row / 2
            stroke = "var(--moved)" if fork["moved"] else "var(--same)"
            dash = "" if fork["moved"] else ' stroke-dasharray="4 5"'
            out.append(
                f'<path d="M{root_x + 56} {root_y:.1f} C{root_x + 200} {root_y:.1f},'
                f'{node_x - 150} {cy:.1f},{node_x} {cy:.1f}" fill="none" stroke="{stroke}" '
                f'stroke-width="{2.2 if fork["moved"] else 1.4}"{dash}/>'
            )
            fill = "var(--moved)" if fork["moved"] else "var(--panel)"
            ink = "#0b0b0c" if fork["moved"] else "var(--dim)"
            nodes.append(
                f'<rect x="{node_x}" y="{cy - 11:.1f}" width="96" height="22" rx="11" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="1.5"/>'
                f'<text x="{node_x + 48}" y="{cy + 4.5:.1f}" text-anchor="middle" font-size="12.5" '
                f'font-weight="800" fill="{ink}">{escape(fork["kind"])}</text>'
            )
            y += row
        mid = (first_y + y) / 2
        nodes.append(
            f'<rect x="{node_x + 116}" y="{first_y + 4:.1f}" width="4" height="{y - first_y - 8:.1f}" '
            f'rx="2" fill="{colour}"/>'
            f'<text x="{node_x + 132}" y="{mid - 2:.1f}" font-size="17" font-weight="900" '
            f'fill="var(--text)">{escape(field)}</text>'
            f'<text x="{node_x + 132}" y="{mid + 17:.1f}" font-size="13" font-weight="800" '
            f'fill="{colour}">{escape(v.get("verdict", ""))}</text>'
        )
        y += gap
    out += nodes
    out.append(
        f'<rect x="{root_x - 56}" y="{root_y - 22:.1f}" width="112" height="44" rx="22" '
        f'fill="var(--text)"/>'
        f'<text x="{root_x}" y="{root_y + 5:.1f}" text-anchor="middle" font-size="14" '
        f'font-weight="900" fill="var(--bg)">checkpoint</text></svg>'
    )
    return "".join(out)


def _matrix(data: dict[str, Any]) -> str:
    head = "".join(f"<th>{k}</th>" for k in ("field", "should matter?", *KINDS, "verdict"))
    rows = []
    for v in data["verdicts"]:
        cells = []
        for kind in KINDS:
            moved = v["moved"].get(kind)
            if moved is None:
                cells.append("<td>–</td>")
            else:
                cls = "moved" if moved else "same"
                cells.append(f'<td><span class="cell {cls}">{cls}</span></td>')
        intent = {"relevant": "yes", "irrelevant": "no"}.get(v["intent"], "undeclared")
        rows.append(
            f'<tr><td class="f">{escape(v["field"])}</td><td>{intent}</td>{"".join(cells)}'
            f"<td>{_badge(v)}</td></tr>"
        )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _evidence(verdict: dict[str, Any], data: dict[str, Any]) -> str:
    field = verdict["field"]
    forks = [f for f in data["forks"] if f["field"] == field]
    before = data["baseline"]["output"]
    original = _quoted(_lookup(data["record"], field))
    if verdict["verdict"] == SILENT_PASSTHROUGH:
        tried = ", ".join(f["kind"] for f in forks)
        text = (
            f"Declared as an input that should change the output. It was {_past(tried)} "
            f"in {len(forks)} separate forks, and the output never moved. "
            "The pipeline does not read it."
        )
        shown = next((f for f in forks if f["kind"] == "destroy"), forks[0])
        cls = "silent"
    else:
        moved = [f for f in forks if f["moved"]]
        shown = next((f for f in moved if f["kind"] == "nudge"), moved[0])
        keys = ", ".join(shown["changed"]) or "the output"
        text = (
            "Declared as an input that should not matter. "
            f"{_describe(shown, original)}, and {keys} changed."
        )
        cls = "phantom"
    after = shown["output"]
    label = f"after {shown['kind']}" + ("" if shown["moved"] else " (identical)")
    return (
        f'<div class="card {cls}"><h3>{escape(field)} · {escape(verdict["verdict"])}</h3>'
        f"<p>{escape(text)}</p>"
        '<div class="pair">'
        f'<div class="out"><div class="t">baseline output</div>{_value_block(before, shown["changed"])}</div>'
        f'<div class="out"><div class="t">{escape(label)}</div>{_value_block(after, shown["changed"])}</div>'
        "</div></div>"
    )


def _describe(fork: dict[str, Any], original: str) -> str:
    if fork["kind"] == "drop":
        return "Dropping it"
    verb = {"nudge": "Nudging", "destroy": "Destroying"}.get(fork["kind"], fork["kind"])
    return f"{verb} it from {original} to {_quoted(fork['value'])}"


def _past(kinds: str) -> str:
    for verb, done in (("destroy", "destroyed"), ("drop", "dropped"), ("nudge", "nudged")):
        kinds = kinds.replace(verb, done)
    head, _, last = kinds.rpartition(", ")
    return f"{head} and {last}" if head else last


def _value_block(value: Any, highlight: list[str] | None = None) -> str:
    hits = set(highlight or [])
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            row = f'<span class="key">{escape(str(k))}:</span> {escape(_clip(v))}'
            lines.append(f'<div class="hit">{row}</div>' if k in hits else f"<div>{row}</div>")
        return f'<div class="kv">{"".join(lines) or "{}"}</div>'
    return f"<pre>{escape(value if isinstance(value, str) else json.dumps(value, indent=2))}</pre>"


def _badge(verdict: dict[str, Any]) -> str:
    cls = {SILENT_PASSTHROUGH: "silent", PHANTOM_SENSITIVITY: "phantom"}.get(verdict["verdict"], "plain")
    text = verdict["verdict"].upper() if verdict["defect"] else verdict["verdict"]
    return f'<span class="badge {cls}">{escape(text)}</span>'


def _verdict_colour(verdict: str) -> str:
    return {SILENT_PASSTHROUGH: "var(--silent)", PHANTOM_SENSITIVITY: "var(--phantom)"}.get(
        verdict, "var(--same)"
    )


def _lookup(record: dict, path: str) -> Any:
    node: Any = record
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _quoted(value: Any) -> str:
    """JSON form, so a nudge that only adds a space is still visible."""
    return _clip(json.dumps(value, ensure_ascii=False))


def _clip(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value)
    return text if len(text) <= _CLIP else text[: _CLIP - 1] + "…"
