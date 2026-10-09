"""A probe report as GitHub-flavoured Markdown: what a CI job summary or a PR comment shows.

Short on purpose. The verdict per field, the defects in one line each, the
proof of each fix, and how the run was timed. The full report is the HTML
page; this is what a reviewer reads without leaving the pull request.
"""

from __future__ import annotations

from typing import Any

from loadbearing.mutations import KINDS
from loadbearing.verdict import PHANTOM_SENSITIVITY, SILENT_PASSTHROUGH

_MARK = {SILENT_PASSTHROUGH: "🔴", PHANTOM_SENSITIVITY: "🟠"}


def render_markdown(data: dict[str, Any]) -> str:
    defects = [v for v in data["verdicts"] if v["defect"]]
    head = (
        f"### Loadbearing · `{_cell(data['target'])}`: "
        + (f"{len(defects)} defect{'s' if len(defects) != 1 else ''}" if defects else "no defects")
    )
    lines = [head, ""]
    if data.get("void"):
        lines += ["> **Void:** every output key varied on its own, so no verdict below is sound.", ""]
    t = data["timing"]
    lines += [
        f"{len(data['forks'])} forks from one checkpoint on `{data['backend']}`: {t['runs']} runs in "
        f"{t['fork_wall_seconds']:.2f}s wall, {t['fork_total_seconds']:.2f}s one after another."
        + (f" Set aside as noise: {', '.join(f'`{k}`' for k in data['unstable_keys'])}."
           if data.get("unstable_keys") else ""),
        "",
        "| field | should matter? | " + " | ".join(KINDS) + " | verdict |",
        "|---|---|" + "---|" * len(KINDS) + "---|",
    ]
    for v in data["verdicts"]:
        intent = {"relevant": "yes", "irrelevant": "no"}.get(v["intent"], "undeclared")
        if v.get("intent_source") == "inferred":
            intent += " (from docs)"
        cells = []
        for kind in KINDS:
            moved = v["moved"].get(kind)
            cells.append("–" if moved is None else ("moved" if moved else "same"))
        verdict = f"{_MARK.get(v['verdict'], '')} **{v['verdict']}**" if v["defect"] else v["verdict"]
        lines.append(f"| `{_cell(v['field'])}` | {intent} | " + " | ".join(cells) + f" | {verdict.strip()} |")
    if defects:
        lines.append("")
        for v in defects:
            why = v.get("explanation") or v.get("reconciliation") or _plain(v)
            lines.append(f"- **`{_cell(v['field'])}`**, {v['verdict']}: {_line(why)}")
            ev = v.get("evidence")
            if ev:
                lines.append(f"  - intended behaviour, quoted from [{_cell(ev['url'])}]({ev['url']}): “{_line(ev['quote'])}”")
    for proof in data.get("proofs", []):
        status = ("✅ proven: the defect is gone and no other field gained one" if proof["clean"]
                  else "❌ not fixed" if not proof["fixed"]
                  else "⚠️ fixed, but adds defects on " + ", ".join(f"`{f}`" for f in proof["new_defects"]))
        lines += ["", f"**Fix for `{_cell(proof['field'])}`:** {status}."]
        fix = next((f for f in data.get("fixes", []) if f["field"] == proof["field"]), None)
        if fix and fix.get("diff"):
            lines += ["", "<details><summary>diff</summary>", "", "```diff", fix["diff"].rstrip(), "```", "", "</details>"]
    for r in data.get("rejected_fixes", []):
        lines += ["", f"No fix applied for `{_cell(r['field'])}`: {_line(r['reason'])}"]
    return "\n".join(lines) + "\n"


def _plain(v: dict[str, Any]) -> str:
    if v["verdict"] == SILENT_PASSTHROUGH:
        return "should change the output, and destroying it never did."
    return "should not matter, and changing it moved the output."


def _cell(text: Any) -> str:
    """Safe inside a table cell or inline code: no pipes, no backticks, one line."""
    return str(text).replace("|", "\\|").replace("`", "'").replace("\n", " ")


def _line(text: Any) -> str:
    return " ".join(str(text).split())
