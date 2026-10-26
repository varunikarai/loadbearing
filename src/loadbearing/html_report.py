"""Render a probe report as one self-contained HTML page.

No scripts, fonts or stylesheets are fetched, so a saved report still opens
offline and a hosted one cannot rot. Every string that came out of a run is
escaped: a pipeline's output is untrusted and lands in this page verbatim.
"""

from __future__ import annotations

import json
import re
from html import escape
from typing import Any

from loadbearing.mutations import KINDS
from loadbearing.verdict import PHANTOM_SENSITIVITY, SILENT_PASSTHROUGH

_CLIP = 160

CSS = """
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
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
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
.note{border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:16px 0 0;font-weight:600;color:var(--dim)}
.note b{color:var(--text)}
.model{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.model .who{font-size:12px;font-weight:900;letter-spacing:.02em;color:var(--dim);margin-bottom:4px}
.model p{margin:0 0 10px}
blockquote{margin:0 0 6px;padding:8px 14px;border-left:4px solid var(--moved);font-weight:600}
.src{font-size:13px;color:var(--dim);word-break:break-all;margin-bottom:14px}
code{font:.88em ui-monospace,"SF Mono",Menlo,Consolas,monospace;background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:1px 5px}
pre.code{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:0 0 12px;max-width:70ch;overflow-x:auto;white-space:pre}
.src a{color:inherit}
.card.proof{border-left-color:var(--ok)}
.card.proof.bad{border-left-color:var(--silent)}
.verdicts{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 14px;font-weight:800}
.arrow{color:var(--dim);font-size:20px}
.diff{font:13px/1.55 ui-monospace,"SF Mono",Menlo,Consolas,monospace;border:1px solid var(--line);
border-radius:12px;padding:10px 0;margin:0 0 14px;overflow-x:auto;white-space:pre}
.diff div{padding:0 14px}
.diff .add{background:color-mix(in srgb,var(--ok) 22%,transparent)}
.diff .del{background:color-mix(in srgb,var(--silent) 22%,transparent)}
.diff .hunk{color:var(--dim)}
.badge.ok{background:var(--ok);color:#0b0b0c}
.rejected{color:var(--dim);font-weight:600;margin:6px 0}
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
        f"<title>{escape(data['target'])} · Loadbearing</title><style>{CSS}</style></head><body><main>",
        '<div class="brand"><b>Loadbearing</b> · checkpoint once, fork per mutation</div>',
        f"<h1>{escape(data['target'])}</h1>",
        f'<p class="lede">{lede}</p>',
    ]
    if data.get("void"):
        parts.append(
            '<div class="warn">Every output key varied on its own across the baseline runs, '
            "so no verdict below is sound.</div>"
        )
    parts += [
        _stats(data),
        _noise_note(data),
        "<h2>One checkpoint, every fork</h2>",
        f'<div class="panel">{fork_tree_svg(data)}</div>',
        "<h2>Every field, every mutation</h2>",
        f'<div class="panel">{_matrix(data)}</div>',
    ]
    if defects:
        parts.append("<h2>The evidence</h2>")
        parts += [_evidence(v, data) for v in defects]
    if data.get("fixes") or data.get("rejected_fixes"):
        parts.append("<h2>The fix, proven</h2>")
        parts += [_fix_card(f, data) for f in data.get("fixes", [])]
        parts += [
            f'<p class="rejected">No fix applied for <b>{escape(r["field"])}</b>: {escape(r["reason"])}</p>'
            for r in data.get("rejected_fixes", [])
        ]
    parts += [
        "<h2>Baseline</h2>",
        '<div class="pair">',
        f'<div class="out"><div class="t">input</div>{_value_block(data["record"])}</div>',
        f'<div class="out"><div class="t">output</div>{_value_block(data["baseline"]["output"])}</div>',
        "</div>",
        f"<footer>Backend: {escape(data['backend'])} · {_floor_summary(data)} · "
        f"report schema {data['schema']}</footer>",
        "</main></body></html>",
    ]
    return "\n".join(parts)


def _stats(data: dict[str, Any]) -> str:
    t = data["timing"]
    wall, total = t["fork_wall_seconds"], t["fork_total_seconds"]
    speed = f"{total / wall:.1f}x" if wall > 0 else "-"
    n = len(data["defects"])
    proven = sum(1 for p in data.get("proofs", []) if p["clean"])
    tiles = [
        (str(len(data["forks"])), "forks from one checkpoint", ""),
        (f"{wall:.2f}s", f"all {t['runs']} runs, in parallel ({total:.2f}s one after another)", ""),
        (speed, "faster than running them in sequence", ""),
        (str(n), "defect" if n == 1 else "defects", "bad" if n else ""),
    ]
    if data.get("proofs"):
        tiles.append((f"{proven}/{n}", "defects fixed by Ultra and proven in a fresh fork", ""))
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
        if v.get("intent_source") == "inferred":
            intent += " · from docs"
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
    # An inferred intent was never declared: its docs, quoted below, say what it should do.
    source = (
        "Not declared, but its docs say it is an input"
        if verdict.get("intent_source") == "inferred"
        else "Declared as an input"
    )
    if verdict["verdict"] == SILENT_PASSTHROUGH:
        tried = ", ".join(f["kind"] for f in forks)
        text = (
            f"{source} that should change the output. It was {_past(tried)} "
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
            f"{source} that should not matter. "
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
        f"</div>{_model_text(verdict)}</div>"
    )


def _model_text(verdict: dict[str, Any]) -> str:
    """What Super, Ultra and Tavily said about this field, when they ran."""
    blocks = []
    ev = verdict.get("evidence")
    if ev:
        link = escape(ev["url"])
        blocks.append(
            '<div class="who">INTENDED BEHAVIOUR · TAVILY</div>'
            f'<blockquote>{escape(ev["quote"])}</blockquote>'
            f'<div class="src"><a href="{link}" rel="noopener">{link}</a></div>'
        )
    if verdict.get("reconciliation"):
        blocks.append(f'<div class="who">ACROSS ALL FORKS · NEMOTRON SUPER</div>{_prose(verdict["reconciliation"])}')
    if verdict.get("explanation"):
        blocks.append(f'<div class="who">WHY · NEMOTRON ULTRA</div>{_prose(verdict["explanation"])}')
    for note in verdict.get("citations") or []:
        blocks.append(f'<div class="who">LINE CHECK · AGAINST THE SOURCE</div><p>{escape(note)}</p>')
    return f'<div class="model">{"".join(blocks)}</div>' if blocks else ""


_FENCE = re.compile(r"```[\w+-]*\n?(.*?)```", re.S)
_INLINE = [
    (re.compile(r"`([^`\n]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*\n]+)\*\*"), r"<b>\1</b>"),
    (re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])"), r"<i>\1</i>"),
]


def _prose(text: str) -> str:
    """A model's prose as HTML: paragraphs, fenced code, `code`, **bold** and *italics*.

    Everything is escaped first, so the only tags that can appear are the ones made here."""
    text = text.strip()
    if text.count("```") % 2:  # cut off inside a code block, at the model's length limit
        text += "\n```"
    out = []
    for i, part in enumerate(_FENCE.split(escape(text))):
        if i % 2:  # inside a fence
            out.append(f'<pre class="code">{part.strip(chr(10))}</pre>')
            continue
        for para in re.split(r"\n\s*\n", part.strip()):
            if not para.strip():
                continue
            for pattern, repl in _INLINE:
                para = pattern.sub(repl, para)
            out.append("<p>" + "<br>".join(line.strip() for line in para.strip().splitlines()) + "</p>")
    return "".join(out)


def _floor_summary(data: dict[str, Any]) -> str:
    runs = data.get("baseline_runs", 2)
    if data.get("void"):
        return f"baseline ran {runs} times and nothing was stable: report void"
    if data.get("unstable_keys"):
        return f"baseline ran {runs} times; {len(data['unstable_keys'])} key(s) varied and were set aside"
    return f"baseline ran {runs} times, identical every time"


def _noise_note(data: dict[str, Any]) -> str:
    keys = data.get("unstable_keys") or []
    if not keys or data.get("void"):
        return ""
    return (
        f'<p class="note">Noise floor: the unmodified input ran <b>{data.get("baseline_runs", 2)}</b> times. '
        f'<b>{escape(", ".join(keys))}</b> changed with no mutation at all, so '
        f'{"it is" if len(keys) == 1 else "they are"} left out of every comparison. '
        "Everything else is judged." + _confirm_note(data) + "</p>"
    )


def _confirm_note(data: dict[str, Any]) -> str:
    """The forks re-run to confirm a move, and any that moved too rarely to count."""
    rerun = [f for f in data["forks"] if f.get("runs", 1) > 1]
    if not rerun:
        return ""
    runs = rerun[0]["runs"]
    flukes = [f for f in rerun if not f["moved"]]
    text = (f" Every fork that moved on a field that should not matter ran {runs} times, and counts only"
            " if most of its runs moved")
    if flukes:
        names = ", ".join(f'<b>{escape(f["label"])}</b> ({f["moves"]} of {f["runs"]})' for f in flukes)
        text += f"; {names} moved too rarely and {'was' if len(flukes) == 1 else 'were'} not counted"
    return text + "."


def _fix_card(fix: dict[str, Any], data: dict[str, Any]) -> str:
    field = fix["field"]
    proof = next((p for p in data.get("proofs", []) if p["field"] == field), None)
    before_v = next((v for v in data["verdicts"] if v["field"] == field), {})
    parts = [f"<h3>{escape(field)} · fixed by Nemotron Ultra</h3>", _prose(fix['rationale'])]
    if fix.get("diff"):
        parts.append(_diff_block(fix["diff"]))
    if proof is None:
        parts.append('<p class="rejected">Written, not yet proven. Run with --prove.</p>')
        return f'<div class="card proof">{"".join(parts)}</div>'
    after = proof["after"]
    after_v = next((v for v in after["verdicts"] if v["field"] == field), {})
    parts.append(
        '<div class="verdicts">'
        f'{_badge(before_v)}<span class="arrow">→</span>{_badge(after_v, fixed=True) if after_v else "gone"}</div>'
    )
    if proof["clean"]:
        verdict = (
            "Applied in a fresh fork of the same checkpoint and probed again: the defect is gone, "
            "and no other field gained one."
        )
    elif not proof["fixed"]:
        verdict = "Applied in a fresh fork and probed again: the defect is still there."
    else:
        verdict = "The defect is gone, but the fix adds defects on " + ", ".join(proof["new_defects"]) + "."
    parts.append(f"<p><b>{escape(verdict)}</b></p>")
    changed = sorted(
        k for k in set(data["baseline"]["output"] or {}) | set(after["baseline"]["output"] or {})
        if isinstance(data["baseline"]["output"], dict) and isinstance(after["baseline"]["output"], dict)
        and data["baseline"]["output"].get(k) != after["baseline"]["output"].get(k)
        and k not in (data.get("unstable_keys") or [])
    )
    parts.append(
        '<div class="pair">'
        f'<div class="out"><div class="t">output before the fix</div>{_value_block(data["baseline"]["output"], changed)}</div>'
        f'<div class="out"><div class="t">output after the fix</div>{_value_block(after["baseline"]["output"], changed)}</div>'
        "</div>"
    )
    cls = "proof" if proof["clean"] else "proof bad"
    return f'<div class="card {cls}">{"".join(parts)}</div>'


def _diff_block(diff: str) -> str:
    rows = []
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            cls = "hunk"
        elif line.startswith("@@"):
            cls = "hunk"
        elif line.startswith("+"):
            cls = "add"
        elif line.startswith("-"):
            cls = "del"
        else:
            cls = ""
        rows.append(f'<div class="{cls}">{escape(line) or " "}</div>')
    return f'<div class="diff">{"".join(rows)}</div>'


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


def _badge(verdict: dict[str, Any], fixed: bool = False) -> str:
    cls = {SILENT_PASSTHROUGH: "silent", PHANTOM_SENSITIVITY: "phantom"}.get(verdict["verdict"], "ok" if fixed else "plain")
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
