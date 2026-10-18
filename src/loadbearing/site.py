"""The demo's front page: what Loadbearing does, shown on a real run, then every target to try.

Written for someone who has never heard of a probe. The hero replays the recorded support
answerer run, copy by copy: each input broken in turn, the answer moving or not, the
ignored policy caught, Nemotron's fix, and the proof. Then the mechanism in four steps,
and every free target to run and check against the bug planted in it. Every number on
the page is read from a recorded run or bench/results.json at render time, never typed
in. No fonts, scripts or styles are fetched; the run buttons work without the script.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any, Optional

from loadbearing._site_css import CSS
from loadbearing._site_js import JS
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


def render_index(demo: Any) -> str:
    hero = demo.cached(HERO) if HERO in demo.targets else None
    starter = STARTER in demo.targets and demo.can_run(STARTER)
    cases = sum(1 for _, names in demo.groups for n in names if n not in EXAMPLES)
    body = "".join([
        '<div class="bg" aria-hidden="true"><i class="aur a1"></i><i class="aur a2"></i><i class="aur a3"></i></div>',
        '<div class="progress" aria-hidden="true"></div>',
        _nav(),
        _hero(hero, cases),
        _stats(hero),
        _story(hero),
        _how(hero),
        _two_bugs(),
        _try(demo),
        _benchmark(),
        _stack(),
        _use(starter),
        _cta(cases),
        _footer(),
    ])
    replay = ""
    if hero:
        payload = json.dumps(_replay(hero), ensure_ascii=False).replace("</", "<\\/")
        replay = f'<script type="application/json" id="replay-data">{payload}</script>'
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        "<title>Loadbearing · find the inputs your AI ignores</title>"
        '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect x=%279%27 y=%279%27 width=%2720%27 height=%2720%27 rx=%275%27 fill=%27%23ff4d4d%27/%3E%3Crect x=%273%27 y=%273%27 width=%2720%27 height=%2720%27 rx=%275%27 fill=%27%23c8ff3d%27/%3E%3C/svg%3E">'
        '<meta name="description" content="Loadbearing breaks each input of an AI pipeline on purpose, '
        'one at a time, finds the ones it silently ignores, and proves the fix.">'
        '<meta name="theme-color" content="#07070a">'
        f"<style>{CSS}</style></head><body>{body}{replay}<script>{JS}</script></body></html>"
    )


# --- sections ---------------------------------------------------------------------------


def _nav() -> str:
    return (
        '<header class="nav"><div class="nav-in">'
        '<a class="logo" href="/"><span class="mark" aria-hidden="true"></span>Loadbearing</a>'
        '<nav><a href="#how">How it works</a><a href="#try">Try it</a><a href="#benchmark">Benchmark</a>'
        f'<a href="{REPO}">GitHub</a></nav>'
        '<a class="btn sm glow" href="#try">Run it live</a></div></header>'
    )


def _words(text: str, start: int = 0) -> str:
    return "".join(
        f'<span class="w" style="--i:{start + i}"><span>{escape(w)}</span></span> '
        for i, w in enumerate(text.split())
    )


def _hero(data: Optional[dict], cases: int) -> str:
    first = f'<a class="btn glow" href="/t/{HERO}">See the real run <span aria-hidden="true">→</span></a>' if data else ""
    second = f'<a class="btn ghost" href="#try">Run all {cases} yourself</a>' if cases else ""
    scribble = (
        '<svg class="scribble" viewBox="0 0 400 24" preserveAspectRatio="none" aria-hidden="true">'
        '<path d="M3 15 C 70 5, 140 21, 210 11 S 330 5, 397 14"/></svg>'
    )
    return (
        '<section class="hero"><div class="wrap">'
        '<p class="badge"><i></i>Live on Nebius Token Factory · NVIDIA Nemotron 3</p>'
        f'<h1><span class="l1">{_words("Your AI was handed the answer.")}</span>'
        f'<span class="l2">{_words("It never read it.", 6)}{scribble}</span></h1>'
        '<p class="sub">Loadbearing breaks every input of your AI pipeline on purpose, one at a time, '
        "and shows you which ones the answer really depends on. Then NVIDIA Nemotron writes the fix, "
        "and Loadbearing proves it works.</p>"
        f'<div class="ctas">{first}{second}</div>'
        "</div>"
        + (_machine(data) if data else "")
        + "</section>"
    )


def _machine(data: dict) -> str:
    """The replay window. Rendered in its starting state; the script plays the recorded run."""
    r = _replay(data)
    rows = []
    for f in r["fields"]:
        kinds = [k for k in ("destroy", "drop", "nudge") if k in f["kinds"]]
        pips = "".join(f'<i data-kind="{k}" title="{k}"></i>' for k in kinds)
        rows.append(
            f'<li class="row" data-field="{escape(f["name"])}" data-orig="{escape(f["value"])}">'
            f'<span class="f">{escape(f["name"])}</span>'
            f'<span class="val">{escape(f["value"])}</span>'
            f'<span class="pips">{pips}</span><span class="row-tag"></span></li>'
        )
    cells = "".join("<i></i>" for _ in r["forks"])
    fix = r.get("fix")
    fixcard = ""
    if fix:
        lines = "".join(f'<span class="del">- {escape(x)}</span>' for x in fix["del"]) + "".join(
            f'<span class="add">+ {escape(x)}</span>' for x in fix["add"])
        fixcard = (
            '<div class="fixcard"><p class="m-h">Nemotron 3 Ultra · the fix<span>'
            f'{len(fix["add"])} line{"s" if len(fix["add"]) != 1 else ""}</span></p>'
            f"<pre>{lines}</pre></div>"
        )
    base = r["baseline"]
    return (
        '<div class="machine-wrap"><div class="machine" id="machine">'
        '<div class="m-bar"><span class="dots"><i></i><i></i><i></i></span>'
        f'<span class="m-title">loadbearing probe <b>{escape(data.get("target", HERO))}</b></span>'
        '<span class="m-live"><i></i>Replay of the recorded live run</span></div>'
        '<div class="m-body">'
        '<div class="m-in"><p class="m-h">The input<span>one real customer request</span></p>'
        f'<ul class="rows">{"".join(rows)}</ul></div>'
        '<div class="m-link" aria-hidden="true"><span></span></div>'
        '<div class="m-out"><p class="m-h">The answer<span>Nemotron 3 Nano</span></p>'
        '<div class="answer" data-state="base"><span class="a-badge">Original answer</span>'
        f'<p class="a-text">{escape(base["answer"])}</p>'
        f'<div class="a-keys">{_keys_html(base["keys"])}</div></div>{fixcard}</div>'
        "</div>"
        f'<div class="m-foot"><div class="strip" aria-hidden="true">{cells}</div>'
        '<p class="narr">One real request, frozen once. Then every input gets broken, one copy at a time.</p>'
        '<button class="replay" type="button" hidden>Replay</button></div>'
        "</div></div>"
    )


def _keys_html(keys: list) -> str:
    return "".join(f"<span><small>{escape(k)}</small>{escape(v)}</span>" for k, v in keys)


def _stats(data: Optional[dict]) -> str:
    results = _results() or {}
    total = results.get("cases", 0)
    ours = next((v for k, v in results.get("cases_right", {}).items() if k.startswith("Loadbearing")), None)
    items = []
    if data:
        r = _replay(data)
        items.append((str(len(data["forks"])), "", "copies of one real run, each with one input broken"))
        secs = (data.get("timing") or {}).get("fork_wall_seconds")
        if secs:
            items.append((f"{secs:.0f}", " s", "for all of them on Nemotron, side by side"))
        if r.get("fix"):
            n = len(r["fix"]["add"])
            items.append((str(n), f" line{'s' if n != 1 else ''}", "in the fix Nemotron 3 Ultra wrote, then proved"))
    if ours is not None and total:
        items.append((str(ours), f" / {total}", "benchmark pipelines found exactly right"))
    if not items:
        return ""
    cells = "".join(
        f'<div><b data-count="{n}">{n}<small>{escape(u)}</small></b><p>{escape(t)}</p></div>'
        for n, u, t in items
    )
    return f'<section class="stats-s"><div class="wrap stats">{cells}</div></section>'


def _chat(data: dict) -> str:
    record = data.get("record", {})
    question = str(record.get("question", ""))
    passages = record.get("passages") or []
    policy = str(passages[0].get("text", "")) if passages and isinstance(passages[0], dict) else ""
    before = _answer(data.get("baseline", {}).get("output"))
    proof = next((p for p in data.get("proofs", []) if p.get("clean")), None)
    after = _answer(proof["after"]["baseline"]["output"]) if proof else ""
    return (
        '<div class="chat spot" aria-label="The same question, before and after the fix">'
        '<div class="chat-top"><span class="av">S</span><b>ShopCo support</b><span>AI assistant</span></div>'
        f'<div class="msg user"><span class="who">Customer</span>{escape(question)}</div>'
        + (f'<div class="policy"><span class="who">Policy the bot was handed</span>{escape(_short(policy, 150))}</div>'
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
        '<section class="story-s"><div class="wrap story">'
        '<div class="story-copy"><p class="eyebrow">The bug nobody sees</p>'
        '<h2>No error. Every test passed. The bot was confidently wrong.</h2>'
        "<p>The retriever found the right policy: 14 days, then warranty only. The code that builds "
        "the prompt looked for it under an old name, got nothing, and the model filled the gap from "
        "memory with a 30-day window that does not exist.</p>"
        "<p>Reading the code, you would have to spot one word. Running it, Loadbearing sees it in "
        "seconds: wipe the policy, and the answer does not change.</p>"
        '<blockquote class="quote spot"><p>Wrong answers like this cost real money. In 2024 a tribunal '
        "ordered Air Canada to pay for what its support chatbot told a customer.</p>"
        '<a href="https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html">'
        "Moffatt v. Air Canada, 2024 BCCRT 149 →</a></blockquote></div>"
        f"{_chat(data)}</div></section>"
    )


def _how(data: Optional[dict]) -> str:
    forks = len(data["forks"]) if data else 14
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
        f'<li data-step="{i}"><span class="n">0{i}</span><h3>{t}</h3><p>{d}</p></li>'
        for i, (t, d) in enumerate(steps, 1)
    )
    fig = ""
    if data:
        proof = next((p for p in data.get("proofs", []) if p.get("clean")), None)
        after = proof["after"] if proof and proof.get("after", {}).get("forks") else None
        caps = [
            "One snapshot of the real run.",
            f"{forks} copies, one broken input each.",
            "Lime lines changed the answer. The policy's copies never did: it is ignored.",
            "After the fix: the same copies, and now the policy moves the answer.",
        ]
        cap = "".join(f'<span data-for="{i}">{escape(c)}</span>' for i, c in enumerate(caps, 1))
        fig = (
            '<figure class="how-fig spot" data-step="3"><div class="trees">'
            f'<div class="tree t-before">{fork_tree_svg(data)}</div>'
            + (f'<div class="tree t-after">{fork_tree_svg(after)}</div>' if after else "")
            + f'</div><figcaption><span class="swipe">Swipe sideways to see the whole tree. </span>{cap}</figcaption></figure>'
        )
    return (
        '<section id="how"><div class="wrap">'
        '<p class="eyebrow">How it works</p><h2>Break it on purpose. Watch what changes.</h2>'
        f'<div class="how"><ol class="steps">{items}</ol><div class="how-side">{fig}</div></div>'
        "</div></section>"
    )


def _two_bugs() -> str:
    return (
        '<section class="band"><div class="wrap">'
        '<p class="eyebrow">What it finds</p><h2>Two kinds of bug that never throw an error</h2>'
        '<div class="bugs">'
        '<div class="bug silent spot"><span class="pill">Silent passthrough</span>'
        "<h3>It should matter. It is ignored.</h3>"
        '<div class="demo" aria-hidden="true"><div class="d-in"><small>policy</small><span class="d-bar"><i></i></span></div>'
        '<span class="d-arrow">→</span><div class="d-out"><small>answer</small><b>30 days</b><em>never moves</em></div></div>'
        "<p>The policy, the ticket body, the applicant's income: wipe it out and the answer stays the "
        "same. Usually a renamed field, a typo, or a value overwritten by a default.</p></div>"
        '<div class="bug phantom spot"><span class="pill">Phantom sensitivity</span>'
        "<h3>It should not matter. It changes the answer.</h3>"
        '<div class="demo" aria-hidden="true"><div class="d-in"><small>order id</small><span class="d-flip"><b>#4821</b><b>#4822</b></span></div>'
        '<span class="d-arrow">→</span><div class="d-out"><small>queue</small><span class="d-flip"><b>Urgent</b><b>Low</b></span><em>jumps</em></div></div>'
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
        n = len(cases)
        grid = (
            '<div class="arena spot"><div class="arena-copy">'
            f'<p class="eyebrow">The benchmark</p><h3>{n} pipelines. Each has one bug planted, or none.</h3>'
            "<p>Every card says what was planted. Run them all and this page checks each result against "
            "the planted bug, live, including the cases Loadbearing gets wrong.</p>"
            f'<button class="btn glow" id="runall" type="button" hidden>Run all {n}, live</button></div>'
            f'<div class="runall score" data-total="{n}" aria-live="polite">'
            '<svg class="ring" viewBox="0 0 120 120" aria-hidden="true"><circle class="r-bg" cx="60" cy="60" r="52"/>'
            '<circle class="r-miss" cx="60" cy="60" r="52"/><circle class="r-ok" cx="60" cy="60" r="52"/></svg>'
            f'<div class="ring-num"><b class="ring-right">0</b><small>/{n}</small><span>exactly right</span></div>'
            '<p class="score-text"></p></div></div>'
            f'<div class="chips"><button class="chip on" data-domain="" type="button">All</button>{chips}</div>'
            f'<div class="grid folded">{"".join(cases)}</div>'
            f'<button class="btn ghost more" type="button" hidden>Show all {n} cases</button>'
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
        f'<article class="card spot{" feat" if featured else ""}" data-domain="{escape(domain)}" '
        f"data-truth='{escape(json.dumps(truth))}' data-name=\"{escape(name)}\">"
        f'<div class="card-top"><span class="kicker">{escape("Example" if featured else title)}</span>{tags}</div>'
        + (f'<h3><a href="/t/{escape(name)}">{escape(title if featured else _headline(demo, name))}</a></h3>'
           f'<p class="slug">{escape(name)}</p>')
        + f'<p class="planted"><span>Planted:</span> {planted}</p>'
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
        spread = f'<div class="fill spread" style="--w:{pct(hi):.1f}%"></div>' if hi > lo else ""
        # A range is shown as it is: the count-up would turn "49–51" into one number.
        num = f'<div class="bar-num" data-count="{lo}">{lo}' if lo == hi else f'<div class="bar-num">{lo}–{hi}'
        rows.append(
            f'<div class="bar spot{" us" if label == "Loadbearing" else ""}"><div class="bar-label">'
            f"<b>{label}</b><span>{note}</span></div>"
            f'<div class="track">{spread}<div class="fill" style="--w:{pct(lo):.1f}%"></div></div>'
            f"{num}<small>/{total}</small>"
            + (f'<em>{_secs(secs)}</em>' if secs is not None else "") + "</div></div>"
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
    tf = (
        '<div class="tile big spot"><span class="t-k">Runs everything</span><h3>Nebius Token Factory</h3>'
        "<p>Serves all three Nemotron models. Its Sandboxes hold the snapshot and the copies: the backend "
        "is built and tested, and its live run is waiting on beta access.</p>"
        '<div class="forkviz" aria-hidden="true"><b>snapshot</b>'
        + "".join(f'<i style="--d:{i}"></i>' for i in range(14))
        + "</div></div>"
    )
    parts = [
        ("Nemotron 3 Nano", "Checks", "Looks at each changed answer: a real change, or just rewording?"),
        ("Nemotron 3 Super", "Explains", "Reads the docs and every copy of a field, and states the defect in one line."),
        ("Nemotron 3 Ultra", "Fixes", "Reads the code, names the line, and writes the smallest fix."),
        ("Tavily", "Finds the docs", "Finds the docs that say what each input is supposed to do, with a quote and a link."),
    ]
    cells = "".join(
        f'<div class="tile spot"><span class="t-k">{k}</span><h3>{t}</h3><p>{d}</p></div>' for t, k, d in parts
    )
    return (
        '<section><div class="wrap"><p class="eyebrow">Built on</p>'
        f'<h2>Every model has one job</h2><div class="bento">{tf}{cells}</div></div></section>'
    )


def _use(starter: bool) -> str:
    cli = [f"git clone {REPO} && cd loadbearing", "pip install -e .",
           "loadbearing probe examples/ticket_triage/target.json"]
    action = ("- uses: varunikarai/loadbearing@main\n"
              "  with:\n"
              "    target: path/to/target.json")
    lines = "".join(f'<span class="t-cmd">{escape(c)}</span>' for c in cli)
    run = f' data-run="/t/{STARTER}/run"' if starter else ""
    return (
        '<section class="band"><div class="wrap use">'
        '<div><p class="eyebrow">Use it</p><h2>Three lines in a terminal. Three in CI.</h2>'
        "<p>Point it at a pipeline and one real input. It fails the build when an input stops doing what "
        "it should, and the run page shows the evidence and the proven fix.</p>"
        + ('<p class="live-note"><i></i>The terminal on this page is real: when it comes into view it runs '
           "the probe on this server.</p>" if starter else "")
        + f'<div class="ctas"><a class="btn glow" href="{REPO}">Read the code</a></div></div>'
        f'<div class="terms"><div class="term spot" id="term"{run}>'
        '<div class="m-bar"><span class="dots"><i></i><i></i><i></i></span><span class="m-title">Terminal</span></div>'
        f'<pre class="t-body">{lines}</pre></div>'
        '<div class="term spot"><div class="m-bar"><span class="dots"><i></i><i></i><i></i></span>'
        '<span class="m-title">.github/workflows/ci.yml</span></div>'
        f'<pre class="t-body">{escape(action)}</pre></div></div>'
        "</div></section>"
    )


def _cta(cases: int) -> str:
    return (
        '<section class="cta-s"><div class="wrap cta">'
        "<h2>Your pipeline has an input it ignores. Find it before a customer does.</h2>"
        '<div class="ctas">'
        + (f'<a class="btn glow" href="#try">Run all {cases}, live</a>' if cases else "")
        + f'<a class="btn ghost" href="{REPO}">Star it on GitHub</a></div></div></section>'
    )


def _footer() -> str:
    return (
        '<footer class="foot"><div class="wrap foot-in">'
        '<span><b>Loadbearing</b> · Apache 2.0 · built by Varunika Rai and Aeshvarya Awasthi</span>'
        f'<span><a href="{REPO}">GitHub</a> · <a href="/healthz">status</a></span>'
        "</div></footer>"
    )


# --- the replay -------------------------------------------------------------------------


def _replay(data: dict) -> dict:
    """What the hero window plays: the recorded run, reduced to what a person can read."""
    record = data.get("record", {})
    unstable = set(data.get("unstable_keys") or [])
    verdicts = {v["field"]: v for v in data.get("verdicts", [])}
    order: list[str] = []
    kinds: dict[str, list[str]] = {}
    for fork in data.get("forks", []):
        if fork["field"] not in order:
            order.append(fork["field"])
        kinds.setdefault(fork["field"], []).append(fork["kind"])

    def out(output: Any) -> dict:
        return {"answer": _answer(output), "keys": _keys(output, unstable)}

    proof = next((p for p in data.get("proofs", []) if p.get("clean")), None)
    fix = next((f for f in data.get("fixes", []) if proof and f.get("field") == proof.get("field")), None)
    after = proof.get("after") if proof else None
    replay = {
        "fields": [
            {"name": n, "value": _show(_lookup(record, n)), "kinds": kinds[n],
             "verdict": verdicts.get(n, {}).get("verdict", ""), "defect": bool(verdicts.get(n, {}).get("defect"))}
            for n in order
        ],
        "baseline": out(data.get("baseline", {}).get("output")),
        "forks": [
            {"field": f["field"], "kind": f["kind"], "value": _mutated(f), "moved": bool(f.get("moved")),
             **out(f.get("output"))}
            for f in data.get("forks", [])
        ],
        "fix": None,
        "after": None,
    }
    if fix and fix.get("diff"):
        lines = fix["diff"].splitlines()
        replay["fix"] = {
            "field": fix["field"],
            "del": [x[1:].strip() for x in lines if x.startswith("-") and not x.startswith("---")],
            "add": [x[1:].strip() for x in lines if x.startswith("+") and not x.startswith("+++")],
        }
    if after and after.get("forks"):
        replay["after"] = {
            "forks": [{"field": f["field"], "kind": f["kind"], "moved": bool(f.get("moved"))} for f in after["forks"]],
            "verdicts": {v["field"]: v["verdict"] for v in after.get("verdicts", [])},
            **out(after.get("baseline", {}).get("output")),
        }
    return replay


def _lookup(record: Any, field: str) -> Any:
    value = record
    for part in field.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _show(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, list):
        first = value[0] if value else None
        if isinstance(first, dict) and "text" in first:
            return _short(f'{len(value)} passages: "{first["text"]}"', 64)
        return _short(json.dumps(value, ensure_ascii=False), 64)
    if isinstance(value, dict):
        return _short(json.dumps(value, ensure_ascii=False), 64)
    return _short(str(value), 64)


def _mutated(fork: dict) -> str:
    if fork["kind"] == "drop":
        return "removed"
    value = fork.get("value")
    if value in ("", [], {}, None):
        return "empty"
    return _show(value)


def _keys(output: Any, unstable: set) -> list:
    if not isinstance(output, dict):
        return []
    keys = []
    for k, v in output.items():
        if k == "answer" or k in unstable:
            continue
        shown = {True: "yes", False: "no", None: "unknown"}.get(v, v) if isinstance(v, (bool, type(None))) else v
        keys.append([k.replace("_", " "), str(shown)])
    return keys


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
