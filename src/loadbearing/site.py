"""The demo's front page: what Loadbearing does, shown on a real run, then every target to try.

Written for someone who has never heard of a probe. It leads with the outcome (a bot
giving a confident wrong answer, then the right one), explains the mechanism in four
plain steps, and lets the visitor run any free target and check the result against the
bug that was planted in it. Every number on the page is read from a recorded run or
bench/results.json at render time, never typed in. No fonts, scripts or styles are
fetched; the small script only upgrades the run buttons, which work without it.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any, Optional

from loadbearing.html_report import fork_tree_svg
from loadbearing.target import load_target

REPO = "https://github.com/varunikarai/loadbearing"
HERO = "support_answerer"  # the recorded LLM run the page is built around
STARTER = "ticket_triage"

# The two examples have no truth.json; say in plain words what is planted in each.
EXAMPLES = {
    "ticket_triage": (
        "Support-ticket triage",
        "Sorts tickets by urgency. Two bugs are planted: the ticket body is read under a misspelled "
        "name, so an outage is filed as low priority, and the second the ticket arrived picks its queue.",
        {"body": "silent passthrough", "submitted_at": "phantom sensitivity"},
    ),
    "support_answerer": (
        "AI support bot, on Nemotron",
        "Answers refund questions from retrieved policy. The retriever hands over the policy, the "
        "prompt never includes it, and the bot makes up a return window.",
        {"passages": "silent passthrough"},
    ),
}

DOMAINS = {
    "triage": "Support-ticket triage",
    "loan": "Loan pre-screen",
    "shipping": "Shipping quote",
    "moderation": "Content moderation",
    "limit": "Edge case",
}

# What each benchmark operator plants, in words; {f} is the field it touches.
PLANTED = {
    "typo": "reads <b>{f}</b> under a misspelled name, so it never sees the value",
    "stale key": "reads <b>{f}</b> under the name it had before an upstream rename",
    "overwritten": "reads <b>{f}</b>, then overwrites it with a default before using it",
    "timestamp leak": "lets the second <b>{f}</b> arrived decide the result",
    "id bucketing": "lets a hash of the id <b>{f}</b> pick which answer you get",
    "id echoed": "copies the id <b>{f}</b> into its answer",
    "value-specific leak": "changes its answer only when <b>{f}</b> starts with TEST-",
    "clean": "nothing: a correct pipeline, here to catch false alarms",
    "threshold-only field (correct code)": "nothing: correct code that only uses a field above a threshold",
}


def render_index(demo: Any) -> str:
    hero = demo.cached(HERO) if HERO in demo.targets else None
    starter_runnable = STARTER in demo.targets and demo.can_run(STARTER)
    body = "".join([
        _nav(),
        _hero(hero, starter_runnable),
        _story(hero),
        _how(hero),
        _two_bugs(),
        _try(demo),
        _benchmark(),
        _stack(),
        _use(),
        _footer(),
    ])
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        "<title>Loadbearing · find the inputs your AI ignores</title>"
        '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect x=%279%27 y=%279%27 width=%2720%27 height=%2720%27 rx=%275%27 fill=%27%23ff4d4d%27/%3E%3Crect x=%273%27 y=%273%27 width=%2720%27 height=%2720%27 rx=%275%27 fill=%27%23c8ff3d%27/%3E%3C/svg%3E">'
        '<meta name="description" content="Loadbearing breaks each input of an AI pipeline on purpose, '
        'one at a time, finds the ones it silently ignores, and proves the fix.">'
        f"<style>{CSS}</style></head><body>{body}<script>{JS}</script></body></html>"
    )


# --- sections ---------------------------------------------------------------------------


def _nav() -> str:
    return (
        '<header class="nav"><div class="wrap nav-in">'
        '<a class="logo" href="/"><span class="mark" aria-hidden="true"></span>Loadbearing</a>'
        '<nav><a href="#how">How it works</a><a href="#try">Try it</a><a href="#benchmark">Benchmark</a>'
        f'<a href="{REPO}">GitHub</a></nav></div></header>'
    )


def _hero(data: Optional[dict], starter: bool) -> str:
    chat = _chat(data) if data else ""
    second = ('<a class="btn ghost" href="#try">Run one yourself</a>' if starter else "")
    first = (f'<a class="btn" href="/t/{HERO}">See the real run</a>' if data else "")
    return (
        '<section class="hero"><div class="wrap hero-in"><div class="hero-copy">'
        '<p class="eyebrow">For anyone shipping an AI pipeline</p>'
        "<h1>Your AI was handed the answer.<br><span>It never read it.</span></h1>"
        '<p class="sub">Loadbearing tests every input of a pipeline by breaking it on purpose, one at a '
        "time, and shows you which ones the answer really depends on. Then NVIDIA Nemotron writes the "
        "fix, and Loadbearing proves it works.</p>"
        f'<div class="ctas">{first}{second}</div>'
        '<p class="meta">Live on Nebius Token Factory · Nemotron 3 Nano, Super and Ultra · Tavily</p>'
        f"</div>{chat}</div></section>"
    )


def _chat(data: dict) -> str:
    record = data.get("record", {})
    question = str(record.get("question", ""))
    passages = record.get("passages") or []
    policy = str(passages[0].get("text", "")) if passages and isinstance(passages[0], dict) else ""
    before = _answer(data.get("baseline", {}).get("output"))
    proof = next((p for p in data.get("proofs", []) if p.get("clean")), None)
    after = _answer(proof["after"]["baseline"]["output"]) if proof else ""
    return (
        '<div class="chat" aria-label="The same question, before and after the fix">'
        f'<div class="msg user"><span class="who">Customer</span>{escape(question)}</div>'
        + (f'<div class="policy"><span class="who">Policy the bot was given</span>{escape(_short(policy, 220))}</div>'
           if policy else "")
        + f'<div class="msg bot bad"><span class="who">Bot, as shipped <i>wrong</i></span>{escape(before)}</div>'
        + (f'<div class="msg bot good"><span class="who">Bot, after the proven fix <i>right</i></span>{escape(after)}</div>'
           if after else "")
        + "</div>"
    )


def _story(data: Optional[dict]) -> str:
    if not data:
        return ""
    return (
        '<section class="band"><div class="wrap story">'
        '<div><p class="big">No error. Every test passed.<br>The bot was confidently wrong.</p></div>'
        '<div class="story-side"><p>The retriever found the right policy. The code that builds the '
        "prompt looked for it under a different name, got nothing, and the model filled the gap from "
        "memory. Reading the code, you would have to spot one word. Running it, Loadbearing sees it in "
        "seconds: wipe the policy, and the answer does not change.</p>"
        '<p class="cite">Wrong answers like this cost real money: in 2024 a tribunal ordered Air Canada '
        "to pay for what its support chatbot told a customer "
        '(<a href="https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html">Moffatt v. Air Canada, 2024 BCCRT 149</a>).</p>'
        "</div></div></section>"
    )


def _how(data: Optional[dict]) -> str:
    forks = len(data["forks"]) if data else 14
    tree = f'<div class="tree">{fork_tree_svg(data)}</div>' if data else ""
    steps = [
        ("Snapshot", "Start the pipeline once, with one real input, and freeze it. Every test that "
         "follows starts from exactly this point, so the only thing that ever differs is the input."),
        ("Break one thing at a time", f"Make {forks} copies. Each gets one input changed: <b>wiped</b>, "
         "<b>removed</b>, or <b>nudged</b> a tiny bit. All of them run at once."),
        ("Watch the answer", "An input that should matter but never changes the answer is being ignored. "
         "An input that should not matter but changes it is leaking in. Rules decide which, never a model."),
        ("Fix it, then prove it", "Nemotron Ultra writes the smallest fix. A fresh copy of the same snapshot "
         "runs every test again: the bug must be gone, and nothing else may break."),
    ]
    items = "".join(
        f'<li><span class="n">{i}</span><h3>{t}</h3><p>{d}</p></li>' for i, (t, d) in enumerate(steps, 1)
    )
    return (
        '<section id="how"><div class="wrap">'
        '<p class="eyebrow">How it works</p><h2>Break it on purpose. Watch what changes.</h2>'
        f'<ol class="steps">{items}</ol>'
        + (f'<figure class="fig">{tree}<figcaption><span class="swipe">Swipe sideways to see the whole tree. </span>The real run: one snapshot, {forks} copies. Lime lines '
           "changed the answer. The policy's copies (red) never did.</figcaption></figure>" if tree else "")
        + "</div></section>"
    )


def _two_bugs() -> str:
    return (
        '<section class="band"><div class="wrap">'
        '<p class="eyebrow">What it finds</p><h2>Two kinds of bug that never throw an error</h2>'
        '<div class="bugs">'
        '<div class="bug silent"><span class="pill">Silent passthrough</span>'
        "<h3>It should matter. It is ignored.</h3>"
        "<p>The policy, the ticket body, the applicant's income: wipe it out and the answer stays the "
        "same. Usually a renamed field, a typo, or a value overwritten by a default.</p></div>"
        '<div class="bug phantom"><span class="pill">Phantom sensitivity</span>'
        "<h3>It should not matter. It changes the answer.</h3>"
        "<p>An order id, a timestamp, a user's name: nudge it and the result moves. Usually leaked "
        "into routing, bucketing, or the prompt by accident.</p></div>"
        "</div></div></section>"
    )


def _try(demo: Any) -> str:
    featured, cases = [], []
    for name in (STARTER, HERO):
        if name in demo.targets:
            featured.append(_card(demo, name, featured=True))
    for label, names in demo.groups:
        for name in names:
            if name in EXAMPLES:
                continue
            cases.append(_card(demo, name))
    chips = "".join(
        f'<button class="chip" data-domain="{k}" type="button">{escape(v)}</button>'
        for k, v in DOMAINS.items()
        if any(n.startswith(k + "-") for _, ns in demo.groups for n in ns)
    )
    grid = ""
    if cases:
        grid = (
            f'<h3 class="sub-h">The benchmark: {len(cases)} pipelines, each with one bug planted (or none)</h3>'
            '<p class="note">Every card says what was planted. Run one, or run them all: the page checks '
            "each result against the planted bug, including the cases Loadbearing gets wrong.</p>"
            '<div class="runall" data-total="' + str(len(cases)) + '">'
            f'<button class="btn" id="runall" type="button" hidden>Run all {len(cases)}, live</button>'
            '<div class="score" aria-live="polite"><div class="score-bar"><span class="s-ok"></span>'
            '<span class="s-miss"></span></div><p class="score-text"></p></div></div>'
            f'<div class="chips"><button class="chip on" data-domain="" type="button">All</button>{chips}</div>'
            f'<div class="grid folded">{"".join(cases)}</div>'
            f'<button class="btn ghost more" type="button" hidden>Show all {len(cases)} cases</button>'
        )
    return (
        '<section id="try"><div class="wrap">'
        '<p class="eyebrow">Try it</p><h2>Run it yourself. It takes about a second.</h2>'
        '<p class="lead">Free runs happen right here, on this server. The AI bot shows its recorded live '
        "run, because running it again would spend credits.</p>"
        f'<div class="featured">{"".join(featured)}</div>{grid}</div></section>'
    )


def _card(demo: Any, name: str, featured: bool = False) -> str:
    title, planted, truth = _describe(demo, name)
    data = demo.cached(name)
    runnable = demo.can_run(name)
    paid = bool(load_target(demo.targets[name]).env)
    if data is None:
        status = '<span class="muted">not run yet</span>'
    else:
        status = _status(data, truth)
        if data.get("backend") != demo.backend:
            status += f'<p class="muted">recorded on {escape(data.get("backend", ""))}</p>'
        elif paid:
            status += '<p class="muted">recorded live on Nebius Token Factory</p>'

    if runnable:
        action = (f'<form class="run" method="post" action="/t/{escape(name)}/run">'
                  '<button class="btn sm">Run probe</button></form>')
    elif data is not None:
        action = f'<a class="btn sm ghost" href="/t/{escape(name)}">View the recorded run</a>'
    else:
        action = '<span class="muted">needs keys</span>'
    domain = name.split("-", 1)[0] if "-" in name else ""
    tags = '<span class="tag">Nemotron · Tavily</span>' if paid else ""
    return (
        f'<article class="card{" feat" if featured else ""}" data-domain="{escape(domain)}" '
        f"data-truth='{escape(json.dumps(truth))}' data-name=\"{escape(name)}\">"
        f'<div class="card-top"><span class="kicker">{escape("Example" if featured else title)}</span>{tags}</div>'
        + (f'<h3><a href="/t/{escape(name)}">{escape(title if featured else _headline(demo, name))}</a></h3>'
           f'<p class="slug">{escape(name)}</p>')
        +         f'<p class="planted"><span>Planted:</span> {planted}</p>'
        f'<div class="result">{status}</div>'
        f'<div class="card-foot">{action}</div></article>'
    )


def _describe(demo: Any, name: str) -> tuple[str, str, dict]:
    if name in EXAMPLES:
        title, text, truth = EXAMPLES[name]
        return title, escape(text), truth
    path = Path(demo.targets[name]).parent / "truth.json"
    truth, operator = {}, ""
    if path.is_file():
        raw = json.loads(path.read_text())
        truth, operator = raw.get("defects", {}), raw.get("operator", "")
    field = escape(next(iter(truth), "") or "")
    template = PLANTED.get(operator, escape(operator) or "unknown")
    title = DOMAINS.get(name.split("-", 1)[0], "Pipeline")
    return title, template.format(f=field) if "{f}" in template else template, truth


HEADLINES = {
    "typo": "A typo hides {f}",
    "stale key": "{f} was renamed upstream",
    "overwritten": "{f} is overwritten",
    "timestamp leak": "The clock picks the answer",
    "id bucketing": "The id picks the answer",
    "id echoed": "The id leaks into the answer",
    "value-specific leak": "Only test ids behave differently",
    "clean": "Nothing wrong here",
    "threshold-only field (correct code)": "Correct, but subtle",
}


def _headline(demo: Any, name: str) -> str:
    """A plain-English title for a benchmark case, from its truth file."""
    path = Path(demo.targets[name]).parent / "truth.json"
    if not path.is_file():
        return name
    raw = json.loads(path.read_text())
    field = next(iter(raw.get("defects", {})), "")
    text = HEADLINES.get(raw.get("operator", ""), name)
    text = text.format(f=field.replace("_", " ")) if "{f}" in text else text
    return text[:1].upper() + text[1:]


def _status(data: dict, truth: dict) -> str:
    found = {v["field"]: v["verdict"] for v in data.get("verdicts", []) if v.get("defect")}
    if found == truth:
        verdict = ('<span class="ok">✓ Found the planted bug</span>' if truth
                   else '<span class="ok">✓ No bug, no false alarm</span>')
    else:
        missed = [f for f in truth if found.get(f) != truth[f]]
        extra = [f for f in found if f not in truth]
        bits = ([f"missed {', '.join(missed)}"] if missed else []) + (
            [f"false alarm on {', '.join(extra)}"] if extra else [])
        verdict = f'<span class="miss">✗ {escape("; ".join(bits))}</span>'
    if found:
        items = "".join(
            f'<li><b>{escape(f)}</b> <span class="v {_cls(v)}">{escape(v)}</span></li>' for f, v in found.items()
        )
        n = len(found)
        listing = f'<p class="count">{n} defect{"s" if n != 1 else ""} found</p><ul class="found">{items}</ul>'
    else:
        listing = '<p class="muted">No defects found.</p>'
    return f"{verdict}{listing}"


def _benchmark() -> str:
    results = _results()
    if not results:
        return ""
    total = results.get("cases", 0)
    right = results.get("cases_right", {})
    seconds = results.get("seconds", {})
    ours = next((v for k, v in right.items() if k.startswith("Loadbearing")), None)
    static = next((v for k, v in right.items() if k.startswith("Static")), None)
    model_key = next((k for k in right if k.startswith("Nemotron")), None)
    # The model was run more than once and scored differently; show every run, not the first.
    model = [right[model_key], *results.get("cases_right_repeats", {}).values()] if model_key else []
    rows = []
    for label, key, values, note in [
        ("Loadbearing", "Loadbearing", [ours] if ours is not None else [],
         "runs the pipeline · same answer every run"),
        ("Nemotron 3 Super", model_key or "", model,
         f"reads the code · {len(model)} runs, a different set wrong on each" if len(model) > 1
         else "reads the code"),
        ("Static name check", "Static", [static] if static is not None else [], "reads the code for field names"),
    ]:
        if not values:
            continue
        lo, hi = min(values), max(values)
        secs = next((s for k, s in seconds.items() if k.startswith(key)), None)
        pct = (lambda v: 100 * v / total) if total else (lambda v: 0)
        spread = f'<div class="fill spread" style="width:{pct(hi):.1f}%"></div>' if hi > lo else ""
        rows.append(
            f'<div class="bar{" us" if label == "Loadbearing" else ""}"><div class="bar-label">'
            f"<b>{label}</b><span>{note}</span></div>"
            f'<div class="track">{spread}<div class="fill" style="width:{pct(lo):.1f}%"></div></div>'
            f'<div class="bar-num">{lo if lo == hi else f"{lo}–{hi}"}<small>/{total}</small>'
            + (f'<span>{_secs(secs)}</span>' if secs is not None else "") + "</div></div>"
        )
    return (
        '<section id="benchmark" class="band"><div class="wrap">'
        '<p class="eyebrow">Measured, not claimed</p>'
        f"<h2>{total} pipelines with planted bugs. Who gets each one fully right?</h2>"
        f'<div class="bars">{"".join(rows)}</div>'
        '<p class="note">Being honest about it: on pipelines this small, a strong model reading the code '
        "does about as well. What it cannot do is give the same answer twice, show the evidence, or prove "
        "its fix. Loadbearing's misses and false alarms are listed case by case in "
        f'<a href="{REPO}/tree/main/bench">bench/</a>, and you can run every case above.</p>'
        "</div></section>"
    )


def _stack() -> str:
    parts = [
        ("Nebius Token Factory", "Serves all three Nemotron models. Its Sandboxes hold the snapshot and the copies: the backend is built and tested, and its live run is waiting on beta access."),
        ("Nemotron 3 Nano", "Looks at each changed answer: a real change, or just rewording?"),
        ("Nemotron 3 Super", "Reads the docs and every copy of a field, and states the defect in one line."),
        ("Nemotron 3 Ultra", "Reads the code, names the line, and writes the smallest fix."),
        ("Tavily", "Finds the docs that say what each input is supposed to do, with a quote and a link."),
    ]
    cells = "".join(f"<div><h3>{t}</h3><p>{d}</p></div>" for t, d in parts)
    return (
        '<section><div class="wrap"><p class="eyebrow">Built on</p>'
        f'<h2>Every model has one job</h2><div class="stack">{cells}</div></div></section>'
    )


def _use() -> str:
    cli = (f"git clone {REPO} && cd loadbearing\n"
           "pip install -e .\n"
           "loadbearing probe examples/ticket_triage/target.json")
    action = ("- uses: varunikarai/loadbearing@main\n"
              "  with:\n"
              "    target: path/to/target.json")
    return (
        '<section class="band"><div class="wrap use">'
        '<div><p class="eyebrow">Use it</p><h2>Three lines in a terminal. Three in CI.</h2>'
        "<p>Point it at a pipeline and one real input. It fails the build when an input stops doing what "
        "it should, and the run page shows the evidence and the proven fix.</p>"
        f'<div class="ctas"><a class="btn" href="{REPO}">Read the code</a></div></div>'
        f'<div class="code"><span>Terminal</span><pre>{escape(cli)}</pre>'
        f'<span>GitHub Actions</span><pre>{escape(action)}</pre></div>'
        "</div></section>"
    )


def _footer() -> str:
    return (
        '<footer class="foot"><div class="wrap foot-in">'
        '<span><b>Loadbearing</b> · Apache 2.0 · built by Varunika Rai and Aeshvarya Awasthi</span>'
        f'<span><a href="{REPO}">GitHub</a> · <a href="/healthz">status</a></span>'
        "</div></footer>"
    )


# --- helpers ----------------------------------------------------------------------------


def _answer(output: Any) -> str:
    if isinstance(output, dict):
        return str(output.get("answer", json.dumps(output)))
    return str(output or "")


def _short(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def _cls(verdict: str) -> str:
    return "silent" if verdict.startswith("silent") else "phantom"


def _secs(s: float) -> str:
    return f"{s:.0f} s" if s >= 1 else "under 1 s"


def _results() -> Optional[dict]:
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        path = base / "bench" / "results.json"
        if path.is_file():
            try:
                return json.loads(path.read_text())
            except ValueError:
                return None
    return None


CSS = """
:root{--bg:#09090b;--bg2:#0f0f12;--panel:#141418;--line:#24242a;--text:#f4f4f0;--dim:#9a9aa2;
--lime:#c8ff3d;--red:#ff4d4d;--amber:#ffb020;--ink:#09090b;--moved:#c8ff3d;--same:#3a3a40;
--silent:#ff4d4d;--phantom:#ffb020;--ok:#c8ff3d}
@media (prefers-color-scheme:light){:root{--bg:#fbfbf8;--bg2:#f3f3ee;--panel:#fff;--line:#e3e3dc;
--text:#0c0c0e;--dim:#62626a;--lime:#4c8a00;--red:#d62828;--amber:#c77700;--ink:#fff;--moved:#4c8a00;
--same:#cfcfca;--silent:#d62828;--phantom:#c77700;--ok:#4c8a00}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);
font:17px/1.6 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
section{padding:96px 0}.band{background:var(--bg2);border-block:1px solid var(--line)}
.eyebrow{font-size:13px;font-weight:900;letter-spacing:.02em;color:var(--lime);margin:0 0 12px;text-transform:uppercase}
h1,h2,h3{letter-spacing:-.03em;margin:0}
h2{font-size:clamp(30px,4.4vw,52px);font-weight:900;line-height:1.05;max-width:22ch;margin-bottom:28px}
h3{font-size:20px;font-weight:850}
.nav{position:sticky;top:0;z-index:5;backdrop-filter:saturate(1.4) blur(14px);
background:color-mix(in srgb,var(--bg) 82%,transparent);border-bottom:1px solid var(--line)}
.nav-in{display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{display:flex;align-items:center;gap:10px;font-weight:900;font-size:18px;letter-spacing:-.02em;text-decoration:none}
.mark{width:18px;height:18px;border-radius:5px;background:var(--lime);
box-shadow:6px 6px 0 -2px var(--red)}
.nav nav{display:flex;gap:22px;font-size:15px;font-weight:700;color:var(--dim)}
.nav nav a{text-decoration:none}.nav nav a:hover{color:var(--text)}
.hero{padding:80px 0 96px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;inset:-30% -10% auto auto;width:720px;height:720px;
background:radial-gradient(closest-side,color-mix(in srgb,var(--lime) 16%,transparent),transparent);pointer-events:none}
.hero-in{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:center;position:relative}
.hero h1{font-size:clamp(40px,5.6vw,70px);font-weight:900;line-height:.98;letter-spacing:-.045em;margin-bottom:24px}
.hero h1 span{color:var(--dim)}
.sub{font-size:clamp(18px,1.6vw,21px);color:var(--dim);max-width:34em;margin:0 0 30px}
.ctas{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;border:0;cursor:pointer;font:inherit;font-size:16px;font-weight:900;
padding:13px 22px;border-radius:999px;background:var(--lime);color:var(--ink);text-decoration:none;white-space:nowrap;
transition:transform .15s ease,filter .15s ease}
.btn:hover{transform:translateY(-1px);filter:brightness(1.06)}
.btn.ghost{background:transparent;color:var(--text);box-shadow:inset 0 0 0 1.5px var(--line)}
.btn.sm{font-size:14px;padding:9px 16px}
.meta{margin:26px 0 0;font-size:14px;font-weight:700;color:var(--dim)}
.chat{display:flex;flex-direction:column;gap:12px;background:var(--panel);border:1px solid var(--line);
border-radius:22px;padding:22px;box-shadow:0 30px 80px rgba(0,0,0,.35)}
.msg,.policy{border-radius:16px;padding:12px 16px;font-size:15.5px;line-height:1.5;max-width:92%}
.who{display:block;font-size:12px;font-weight:900;letter-spacing:.02em;color:var(--dim);margin-bottom:4px;text-transform:uppercase}
.who i{font-style:normal;margin-left:6px;padding:1px 8px;border-radius:999px;font-size:11px}
.user{align-self:flex-end;background:var(--bg2);border:1px solid var(--line)}
.policy{align-self:center;max-width:100%;border:1.5px dashed var(--line);color:var(--dim);font-size:14px}
.bot{background:var(--bg2);border:1px solid var(--line)}
.bot.bad{border-color:color-mix(in srgb,var(--red) 55%,var(--line))}
.bot.bad i{background:var(--red);color:#fff}
.bot.good{border-color:color-mix(in srgb,var(--lime) 55%,var(--line))}
.bot.good i{background:var(--lime);color:var(--ink)}
.story{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}
.big{font-size:clamp(28px,3.6vw,44px);font-weight:900;letter-spacing:-.035em;line-height:1.08;margin:0}
.story-side p{margin:0 0 18px;color:var(--dim);font-size:18px}.cite{font-size:15px!important}
.steps{list-style:none;padding:0;margin:0 0 48px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px;counter-reset:s}
.steps li{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:22px}
.steps .n{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:9px;background:var(--lime);
color:var(--ink);font-weight:900;margin-bottom:16px}
.steps h3{margin-bottom:8px}.steps p{margin:0;color:var(--dim);font-size:15.5px}
.steps b{color:var(--text)}
.fig{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:18px 18px 12px;overflow:hidden}
.tree{overflow-x:auto;-webkit-overflow-scrolling:touch}
.swipe{display:none}
.fig figcaption{color:var(--dim);font-size:14px;font-weight:600;padding:8px 6px 4px}
.tree svg{display:block;width:100%;height:auto;min-width:560px}.tree svg text{font-family:inherit}
.bugs{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.bug{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:26px;border-top:5px solid var(--red)}
.bug.phantom{border-top-color:var(--amber)}
.pill{display:inline-block;font-size:12px;font-weight:900;padding:4px 10px;border-radius:999px;background:var(--red);
color:#fff;margin-bottom:14px;text-transform:uppercase;letter-spacing:.02em}
.bug.phantom .pill{background:var(--amber);color:#111}
.bug h3{font-size:24px;margin-bottom:10px}.bug p{color:var(--dim);margin:0}
.lead{color:var(--dim);font-size:18px;max-width:44em;margin:-12px 0 32px}
.featured{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:56px}
.sub-h{font-size:24px;margin-bottom:8px}
.note{color:var(--dim);font-size:15.5px;max-width:52em;margin:0 0 20px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
.chip{font:inherit;font-size:14px;font-weight:800;padding:7px 14px;border-radius:999px;cursor:pointer;
background:transparent;color:var(--dim);border:1.5px solid var(--line)}
.chip.on{background:var(--text);color:var(--bg);border-color:var(--text)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--line);border-radius:16px;
padding:16px 16px 14px;min-width:0;transition:border-color .2s}
.card.feat{padding:24px;border-radius:20px}.card.feat h3{font-size:24px}
.card.feat .planted{font-size:16px}
.card.hit{border-color:color-mix(in srgb,var(--lime) 60%,var(--line))}
.card.missed{border-color:color-mix(in srgb,var(--amber) 70%,var(--line))}
.card-top{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px}
.kicker{font-size:12px;font-weight:900;color:var(--dim);text-transform:uppercase;letter-spacing:.02em}
.tag{font-size:11px;font-weight:900;color:var(--dim);border:1px solid var(--line);border-radius:999px;padding:2px 8px;white-space:nowrap}
.card h3{font-size:18px;margin-bottom:2px;line-height:1.25}.card h3 a{text-decoration:none}
.slug{margin:0 0 10px;font:12.5px ui-monospace,"SF Mono",Menlo,monospace;color:var(--dim);word-break:break-all}
.planted{font-size:14.5px;color:var(--dim);margin:0 0 12px}.planted span{font-weight:900;color:var(--text)}
.planted b{color:var(--text)}
.result{font-size:14px;margin-bottom:12px;min-height:0}
.result .ok{color:var(--lime);font-weight:900}.result .miss{color:var(--amber);font-weight:900}
.count{margin:8px 0 0;font-weight:800}.found{list-style:none;margin:6px 0 0;padding:0}.found li{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:4px 0;font-size:13.5px}
.v{font-size:11px;font-weight:900;padding:2px 8px;border-radius:999px;text-transform:uppercase}
.v.silent{background:var(--red);color:#fff}.v.phantom{background:var(--amber);color:#111}
.card-foot{margin-top:auto;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.card-foot form{margin:0}.muted{color:var(--dim);font-size:14px}
.card.running .btn{opacity:.6;pointer-events:none}
.card.running .result:before{content:"Running every copy…";color:var(--dim);font-weight:800}
.runall{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin:6px 0 22px}
.score{flex:1;min-width:260px}.score-bar{display:none;height:10px;border-radius:999px;background:var(--bg2);
border:1px solid var(--line);overflow:hidden}.score.on .score-bar{display:flex}
.s-ok{background:var(--lime);width:0;transition:width .3s}.s-miss{background:var(--amber);width:0;transition:width .3s}
.score-text{margin:8px 0 0;font-weight:800;font-size:15px}.score-text small{color:var(--dim);font-weight:700}
.grid.folded .card:nth-child(n+9){display:none}.more{margin:18px auto 0;display:flex}
.bars{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
.bar{display:grid;grid-template-columns:260px 1fr 120px;gap:18px;align-items:center;background:var(--panel);
border:1px solid var(--line);border-radius:16px;padding:16px 20px}
.bar-label b{display:block;font-size:17px}.bar-label span{font-size:13.5px;color:var(--dim)}
.track{position:relative;height:14px;border-radius:999px;background:var(--bg2);overflow:hidden;border:1px solid var(--line)}
.fill{position:absolute;inset:0 auto 0 0;border-radius:999px;background:var(--dim)}.bar.us .fill{background:var(--lime)}
.fill.spread{opacity:.4}
.bar.us{border-color:color-mix(in srgb,var(--lime) 45%,var(--line))}
.bar-num{text-align:right;font-size:30px;font-weight:900;letter-spacing:-.03em;line-height:1}
.bar-num small{font-size:15px;color:var(--dim)}.bar-num span{display:block;font-size:12.5px;color:var(--dim);font-weight:700;margin-top:4px}
.stack{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.stack div{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px}
.stack h3{font-size:16px;margin-bottom:6px}.stack p{margin:0;color:var(--dim);font-size:14.5px}
.use{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center}.use p{color:var(--dim);margin:0 0 24px}
.code{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px 20px}
.code span{font-size:12px;font-weight:900;color:var(--dim);text-transform:uppercase;letter-spacing:.02em}
.code pre{margin:8px 0 16px;font:14px/1.7 ui-monospace,"SF Mono",Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
.foot{padding:28px 0;border-top:1px solid var(--line);color:var(--dim);font-size:14px}
.foot-in{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.reveal{opacity:0;transform:translateY(14px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
@media (max-width:900px){.hero-in,.story,.use,.bugs,.featured{grid-template-columns:1fr}
.steps{grid-template-columns:1fr 1fr}.stack{grid-template-columns:1fr 1fr}
.bar{grid-template-columns:1fr auto}.track{grid-column:1/-1;order:3}section{padding:72px 0}
.nav nav a:not(:last-child){display:none}}
@media (max-width:560px){.steps,.stack{grid-template-columns:1fr}.hero{padding-top:48px}.swipe{display:inline}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}
.reveal{opacity:1;transform:none}html{scroll-behavior:auto}}
"""

JS = """
(() => {
  document.querySelectorAll('.tree').forEach(t => { t.scrollLeft = t.scrollWidth; });
  const io = 'IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches
    ? new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), {rootMargin: '0px 0px -8% 0px'})
    : null;
  if (io) document.querySelectorAll('section:not(.hero) .wrap > *').forEach(el => { el.classList.add('reveal'); io.observe(el); });

  document.querySelectorAll('.chip').forEach(chip => chip.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === chip));
    const d = chip.dataset.domain;
    document.querySelectorAll('.grid .card').forEach(card => { card.hidden = !!d && card.dataset.domain !== d; });
  }));

  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const cls = v => v.startsWith('silent') ? 'silent' : 'phantom';
  function verdict(found, truth) {
    const fk = Object.keys(found), tk = Object.keys(truth);
    const same = fk.length === tk.length && tk.every(k => found[k] === truth[k]);
    if (same) return tk.length ? '<span class="ok">✓ Found the planted bug</span>' : '<span class="ok">✓ No bug, no false alarm</span>';
    const missed = tk.filter(k => found[k] !== truth[k]), extra = fk.filter(k => !(k in truth));
    const bits = [];
    if (missed.length) bits.push('missed ' + missed.join(', '));
    if (extra.length) bits.push('false alarm on ' + extra.join(', '));
    return '<span class="miss">✗ ' + esc(bits.join('; ')) + '</span>';
  }
  document.querySelectorAll('form.run').forEach(form => form.addEventListener('submit', async ev => {
    const card = form.closest('.card');
    if (!card || !window.fetch || form.dataset.ran === '1') return;
    ev.preventDefault();
    await runCard(card);
  }));
  async function runCard(card) {
    const form = card.querySelector('form.run');
    if (!form || form.dataset.ran === '1') return;
    card.classList.add('running');
    const result = card.querySelector('.result');
    result.innerHTML = '';
    try {
      const res = await fetch(form.action + '?format=json', {method: 'POST', headers: {Accept: 'application/json'}});
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const found = {};
      (data.verdicts || []).forEach(v => { if (v.defect) found[v.field] = v.verdict; });
      const truth = JSON.parse(card.dataset.truth || '{}');
      const list = Object.keys(found).length
        ? '<p class="count">' + Object.keys(found).length + ' defect' + (Object.keys(found).length === 1 ? '' : 's') + ' found</p><ul class="found">' + Object.entries(found).map(([f, v]) => '<li><b>' + esc(f) + '</b> <span class="v ' + cls(v) + '">' + esc(v) + '</span></li>').join('') + '</ul>'
        : '<p class="muted">No defects found.</p>';
      const t = data.timing || {};
      const took = t.runs ? '<p class="muted">' + t.runs + ' runs in ' + (t.fork_wall_seconds || 0).toFixed(2) + ' s</p>' : '';
      result.innerHTML = verdict(found, truth) + list + took;
      card.classList.toggle('hit', result.querySelector('.ok') !== null);
      card.classList.toggle('missed', result.querySelector('.miss') !== null);
      const btn = form.querySelector('button');
      btn.textContent = 'Open the full report';
      btn.classList.add('ghost');
      form.dataset.ran = '1';
    } catch (err) {
      result.innerHTML = '<span class="miss">Could not run: ' + esc(err.message) + '</span>';
    } finally {
      card.classList.remove('running');
    }
  }
  const grid = document.querySelector('.grid');
  const more = document.querySelector('.more');
  if (grid && more) {
    more.hidden = false;
    more.addEventListener('click', () => { grid.classList.remove('folded'); more.remove(); });
  }
  const chipsUnfold = () => { if (grid) grid.classList.remove('folded'); if (more) more.remove(); };
  document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', chipsUnfold));

  const all = document.getElementById('runall');
  if (all && window.fetch) {
    all.hidden = false;
    all.addEventListener('click', async () => {
      chipsUnfold();
      const cards = [...document.querySelectorAll('.grid .card')].filter(c => c.querySelector('form.run'));
      const score = document.querySelector('.score'), text = score.querySelector('.score-text');
      const ok = score.querySelector('.s-ok'), miss = score.querySelector('.s-miss');
      score.classList.add('on'); all.disabled = true; all.textContent = 'Running…';
      let done = 0, right = 0, wrong = [];
      const total = cards.length, started = performance.now();
      const draw = () => {
        ok.style.width = (100 * right / total) + '%';
        miss.style.width = (100 * (done - right) / total) + '%';
        text.innerHTML = right + ' of ' + done + ' exactly right <small>· ' + done + '/' + total + ' run · ' +
          ((performance.now() - started) / 1000).toFixed(1) + ' s</small>' +
          (wrong.length ? '<br><small>Not right: ' + wrong.map(esc).join(', ') + '</small>' : '');
      };
      const queue = cards.slice();
      const worker = async () => {
        while (queue.length) {
          const card = queue.shift();
          await runCard(card);
          done++;
          if (card.classList.contains('hit')) right++; else wrong.push(card.dataset.name);
          draw();
        }
      };
      draw();
      await Promise.all([worker(), worker(), worker(), worker()]);
      all.textContent = 'Done: ' + right + ' of ' + total + ' exactly right';
    });
  }
  // After a run, the button opens the full report: a plain form post, no script involved.
})();
"""
