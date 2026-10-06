# Work plan

Who does what, by when, through submission on **Sun 2026-10-25** (hard deadline Fri 2026-10-30 10:00 PT, 22:30 IST).

Every task below is written so either builder can pick it up cold: why it exists, which files it owns, what it needs first, the steps, and the test for done. The work is split evenly: each builder has core engine work, Nemotron and Sandboxes work, a judged writing piece, half the video, a feedback file, and a review duty.

## How to use this file

1. Read the **Board** and your own tasks. Read the other builder's tasks only where yours depend on them.
2. When you finish a task, set its Status on the Board to `done` and add a Log entry in [PROGRESS.md](PROGRESS.md).
3. Due dates are hand-off dates: the other builder may start depending on your output that day.
4. If a date will slip, say so in PROGRESS.md the day you know, not the day it is due.

## Board

| ID | Task | Type | Pts | Due | Status |
|---|---|---|---|---|---|
| V1 | Sandboxes live run | tech | 4 | Sat 10-10 | todo |
| V2 | Nemotron layer verified | tech | 6 | Sun 10-11 | todo |
| V3 | Noise floor | tech | 3 | Sat 10-10 | todo |
| V4 | Tavily intent inference | tech | 5 | Sat 10-17 | todo |
| V5 | Fix writer | tech | 4 | contract Fri 10-09, done Sat 10-17 | todo |
| V6 | Pre-public audit and the public flip | tech | 2 | Sun 10-18 | todo |
| V7 | Prior art and evidence | non-tech | 3 | Tue 10-20 | todo |
| V8 | README narrative ✍ | non-tech | 3 | Sun 10-18 | todo |
| V9 | Visual identity | non-tech | 4 | palette Sat 10-10, rest Tue 10-20 | todo |
| V10 | Video script and voice ✍ | non-tech | 3 | outline Sun 10-11, voice Sun 10-18 | todo |
| V11 | Feedback: Sandboxes and Tavily ✍ | non-tech | 1.5 | Fri 10-23 | todo |
| V12 | Judging self-review | non-tech | 2 | Tue 10-20 and Fri 10-23 | todo |
| A1 | Contracts | tech | 2 | Fri 10-09 | todo |
| A2 | Secrets into forks | tech | 2 | Sat 10-10 | todo |
| A3 | LLM demo target | tech | 6 | shortlist Fri 10-09, done Sat 10-17 | todo |
| A4 | Fix and prove | tech | 5 | toy Tue 10-13, done Sat 10-17 | todo |
| A5 | Report and UI v2 | tech | 5 | Sat 10-17 | todo |
| A6 | Hosted demo | tech | 4 | live Sun 10-11, final Sat 10-17 | todo |
| A7 | CI and clean-clone check | tech | 2 | Sun 10-18 | todo |
| A8 | Field scan | non-tech | 2 | Tue 10-13 | todo |
| A9 | Video production | non-tech | 5 | uploaded Wed 10-21 | todo |
| A10 | Devpost page ✍ | non-tech | 3 | draft Tue 10-20, final Fri 10-23 | todo |
| A11 | Feedback: Token Factory and Nemotron ✍ | non-tech | 1.5 | Fri 10-23 | todo |
| A12 | Compliance and submission | non-tech | 2 | checklist Tue 10-20, submit Sun 10-25 | todo |

V = Varunika, A = Aeshvarya. One point is roughly one focused hour; the points are estimates for balance, not promises. ✍ marks text that judges read as ours: its final words are the owner's own.

## Rules

1. **One branch per task:** `varunika/v3-noise-floor`, `aeshvarya/a4-prove`.
2. **Smallest possible commits, pushed as they happen.** The message says why. Each builder commits as themselves. No trailers.
3. **Merge with a merge commit** (`git merge --no-ff`), never a squash, so authorship survives.
4. **Self-merge** when CI is green and the branch touches only your own paths (see Ownership). A branch that touches the other's paths needs their review; no reply within 24 hours counts as approval.
5. **Contracts C1 to C7 are frozen from Sun 2026-10-11.** Changing one needs the other builder's OK in PROGRESS.md first.
6. **Tests run offline:** no network, no keys. Live calls sit behind CLI flags, and tests use the fakes in `tests/fakes.py`.
7. **Secrets never land** in the repo, a checkpoint, a report, or a log.
8. **Feature freeze Fri 2026-10-23.** After that, only fixes. No pushes to `main` between the deadline and the results, so judges see what was submitted.

## Ownership

| Path | Owner |
|---|---|
| `src/loadbearing/mutations.py`, `verdict.py`, `compare.py`, `noise.py`, `nemotron.py`, `tavily.py`, `intent.py`, `fix.py` | Varunika |
| `src/loadbearing/probe.py` | Shared. Varunika owns the baseline and judging steps; Aeshvarya owns timing and run orchestration. Rebase before merging. |
| `src/loadbearing/target.py`, `backends/`, `prove.py`, `report.py`, `html_report.py`, `serve.py`, `cli.py` | Aeshvarya |
| `examples/ticket_triage/` | Varunika |
| `examples/<llm target>/` | Aeshvarya |
| `tests/` | Each builder owns the tests for their own modules. `tests/fakes.py` is Varunika's. |
| `scripts/` | Varunika |
| `Dockerfile`, `.dockerignore`, `.github/` | Aeshvarya |
| `SPEC.md`, `docs/prior-art.md`, `assets/` | Varunika |
| README: top pitch, why it matters, prior art, team | Varunika |
| README: status, quickstart, Sandboxes, target format, layout, demo, tests | Aeshvarya |
| `docs/feedback/` | Each builder their own file |
| `PROGRESS.md`, `WORKPLAN.md` | Both. Log entries are append-only and name who did the work. |

**One exception:** during V1, Varunika may fix `backends/contree.py` on the spot if the live run breaks it; Aeshvarya reviews afterwards.

## Contracts

These are the seams between the two halves. They land first, so neither builder waits on the other.

### C1 · `target.json` v2 keys (A1, Fri 10-09)

All optional. The defaults keep today's targets working unchanged.

| Key | Type | Default | Used by |
|---|---|---|---|
| `baseline_runs` | int, 2 or more | `2` | V3 noise floor |
| `env` | list of variable names | `[]` | A2: values are read from the host at run time and passed to baseline and fork runs only, never to setup |
| `docs` | `{"query": str, "urls": [str]}` | none | V4 Tavily intent inference |
| `sources` | list of paths under the target directory | same as `files` | V5 (files Ultra may read and rewrite), A4 |

### C2 · `Backend.apply` (signature A1, implementations A4)

```python
def apply(self, checkpoint, files: dict[str, str]):
    """A new checkpoint derived from `checkpoint`, with `files` (path -> full content) written.
    The original checkpoint is never changed."""
```

### C3 · `Fix` (V5, Fri 10-09) in `src/loadbearing/fix.py`

```python
@dataclass
class Fix:
    field: str             # the field the defect is on
    defect: str            # "silent passthrough" or "phantom sensitivity"
    files: dict[str, str]  # path under the target directory -> full new content
    rationale: str         # why this change removes the defect

    def diff(self, target) -> str:
        """Unified diff of `files` against the target's current files."""
```

### C4 · `Proof` (A4) in `src/loadbearing/prove.py`

```python
@dataclass
class Proof:
    fix: Fix
    after: Report           # the probe re-run on the patched checkpoint
    fixed: bool             # the fix's field no longer carries the defect
    new_defects: list[str]  # fields that are defects after the fix but were not before
```

### C5 · New verdict and report fields

Varunika adds them to the dataclasses; Aeshvarya serialises them in report schema 2. Cached schema-1 runs are simply re-run.

| Field | Set by |
|---|---|
| `FieldVerdict.reconciliation: str or None` (Super) | V2 |
| `FieldVerdict.explanation: str or None` (Ultra) | V2 |
| `FieldVerdict.intent_source`: `"declared"`, `"inferred"` or `"undeclared"` | V4 |
| `FieldVerdict.evidence: Evidence or None`, where `Evidence(intent, quote, url)` | V4 |
| `Report.baseline_runs: int` and `Report.unstable_keys: list[str]` | V3 |
| report JSON `fixes` and `proofs` lists | A4, serialised by A5 |

### C6 · CLI flags (reserved by A1, wired by Aeshvarya as each function lands)

| Flag | Does |
|---|---|
| `--baseline-runs N` | overrides `baseline_runs` |
| `--explain` | Super reconciliation and Ultra explanation per field |
| `--intent` | Tavily intent inference for undeclared fields |
| `--fix` | writes a fix per defect (implies `--explain`) |
| `--prove` | applies each fix in a fresh fork and re-probes (implies `--fix`) |

Every function behind a flag must also be callable without the CLI, so it can be tested before it is wired.

### C7 · Router methods (Varunika, `nemotron.py`)

`classify_diff` (Nano), `reconcile(verdict)` (Super), `explain(verdict, source)` (Ultra), `write_fix(verdict, sources) -> (files, rationale)` (Ultra), `infer_intent(fields, excerpts) -> dict[field, Evidence]` (Super). Aeshvarya calls these and never edits `nemotron.py`.
