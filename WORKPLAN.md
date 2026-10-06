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

## Varunika's tasks

### V1 · Sandboxes live run · tech · 4 pts · prep Fri 10-09, done Sat 10-10 morning

**Why.** Everything accepted on 2026-10-06 depends on the Sandboxes path, and it has never run once. It is also the core evidence for Technological Implementation.
**Owns.** Your local `.env` (never committed). May fix `backends/contree.py` on the spot.
**Needs.** Nothing.
**Steps.**
1. Claim the hackathon credit (the promo form, activation code `NEBIUS-DEVPOST-GLOBAL26`) and the Builders Program credit. Note both balances.
2. `pip install -e '.[sandbox]'`, then `contree auth` with your token and project ID.
3. Create a Token Factory key, put `NEBIUS_API_KEY` in `.env`, run `loadbearing models`, and paste the Nano, Super and Ultra IDs into `.env`.
4. `loadbearing probe examples/ticket_triage/target.json --backend sandbox`, then again with `--nano`.
5. If it breaks, make the smallest fix in `contree.py`, one commit per fix, and keep the exact error text for V11.
6. Record checkpoint seconds, fork wall seconds, parallel speedup, and the credit balance before and after.

**Done when.** The Sandboxes run reports the same two defects as the local run, with and without `--nano`, and the numbers are in the Log.
**Hands to.** Everyone: it unblocks V2, A3, A4 and A6. The numbers go to V8, V10 and A10.

### V2 · Nemotron layer verified · tech · 6 pts · Sun 10-11

**Why.** Routing by job (Nano per fork, Super per field, Ultra for the why) is the NVIDIA half of Technological Implementation, and none of it has run live.
**Owns.** `nemotron.py`, `tests/fakes.py`, `tests/test_nemotron.py`, `tests/fixtures/diffs.json`, `scripts/eval_nano.py`, the judging step in `probe.py`, and `FieldVerdict.reconciliation` and `.explanation`.
**Needs.** V1 (model IDs).
**Steps.**
1. `tests/fakes.py`: a fake Token Factory client and a fake router with scripted answers, so every test runs offline. Aeshvarya's tests use these too.
2. `tests/fixtures/diffs.json`: 20 labelled pairs of baseline and fork output. 10 meaningful (a priority flip, a missing answer, a changed number, a crash) and 10 noise (a timestamp, a request id, key order, whitespace, a reworded but equivalent sentence).
3. `scripts/eval_nano.py`: run Nano over the 20 and print accuracy. Tune the prompt until it scores 18/20 or better, and log the score.
4. Wire `reconcile` (Super) and `explain` (Ultra) into the judging step, behind `--explain`, storing the text on each verdict.
5. Reasoning traces never reach the report.

**Done when.** Nano scores 18/20 or better (logged); `--explain` on the toy target gives one Super line and one Ultra explanation per defect; all tests pass offline.
**Hands to.** A5 renders the text; V5 builds on `explain`.

### V3 · Noise floor · tech · 3 pts · Sat 10-10 afternoon

**Why.** An LLM's output varies on its own, so the current two-run check would void every verdict on the demo target.
**Owns.** `noise.py`, the baseline step in `probe.py`, the `ignore` parameter in `compare.py`, `tests/test_noise.py`.
**Needs.** A1 (`baseline_runs`). Until A1 merges, read the key with a default of 2.
**Steps.**
1. Run the baseline `baseline_runs` times in the same parallel pool as the forks.
2. `unstable_keys(runs) -> list[str]`: the output keys whose value differs across baseline runs. If stdout is not JSON, the whole output counts as one key.
3. `compare(baseline, fork, ignore=unstable)`, so an unstable key never counts as moved.
4. `Report.deterministic` now means "no unstable keys". If every key is unstable, the report says plainly that its verdicts are void.
5. Test with a fake backend whose `request_id` changes on every run: it must still give the right verdicts on every other key.

**Done when.** The toy target is unchanged (no unstable keys, same five verdicts), and the noisy fake marks only `request_id` as unstable.
**Hands to.** A3 (the LLM target depends on it) and A5 (renders unstable keys).

### V4 · Tavily intent inference · tech · 5 pts · part 1 Fri 10-16, part 2 Sat 10-17

**Why.** The $3,000 Tavily prize needs a runtime call that does real work. This one decides which undeclared fields should matter, so they can carry a defect claim too.
**Owns.** `intent.py`, `tavily.py`, `Evidence`, `FieldVerdict.intent_source` and `.evidence`, `tests/test_intent.py`.
**Needs.** A1 (`docs`), A3 (the LLM target's `docs`), V2.
**Steps.**
1. Part 1: search with `docs.query` (and fetch any `docs.urls`), keeping title, URL and content. Cache the result in `runs/<target>.intent.json` so the demo never repeats a paid call.
2. Part 2: Super receives the excerpts and the undeclared fields, and returns JSON giving each field `relevant`, `irrelevant` or `unknown`, a verbatim quote, and its URL. Reject any quote that does not appear in the excerpt text.
3. Inferred intents feed `judge` like declared ones, marked `inferred` and carrying their evidence. A declared intent always wins over an inferred one.
4. Behind `--intent`.

**Done when.** On the LLM target, at least one undeclared field gets an inferred intent with a real quote and URL; one live Tavily call is logged; tests pass offline with a fake search.
**Hands to.** A5 (evidence links), A9 and A10 (the Tavily part of the story).

### V5 · Fix writer · tech · 4 pts · contract Fri 10-09, toy Fri 10-16, LLM target Sat 10-17

**Why.** The first half of closing the loop: Ultra writes the smallest fix for a defect.
**Owns.** `fix.py` (`Fix`, `write_fix`), `Router.write_fix`, `tests/test_fix.py`.
**Needs.** V2.
**Steps.**
1. Fri 10-09: commit the `Fix` dataclass from contract C3 on its own, so A4 can start against it.
2. `write_fix(verdict, target, router) -> Fix`: Ultra receives the files in `target.sources`, the verdict and its evidence, and returns the full new content of each changed file plus a rationale.
3. Validate before returning: only `sources` files changed; Python files compile; the change is small (reject anything that rewrites most of a file); `Fix.diff()` renders a unified diff.
4. Test with the fake router returning the `bdoy` to `body` fix for the toy target.

**Done when.** Live Ultra fixes the toy target's `body` defect with a diff touching only that line, and writes a valid fix for the LLM target's defect on 10-17.
**Hands to.** A4.

### V6 · Pre-public audit and the public flip · tech · 2 pts · Sun 10-18 morning

**Why.** The repo goes public that day. A leaked key or personal detail cannot be taken back afterwards. The flip needs repo admin, which only Varunika has.
**Owns.** The audit, the go or no-go Log entry, and the flip.
**Needs.** Everything that is going public, merged.
**Steps.**
1. Scan all history, not just the current files: `git log -p --all` for key patterns (`eyJ`, `tvly-`, `sk-`), any `.env`, tokens, and email addresses that are not ours.
2. Read every tracked file for personal detail and for anything from an employer or another project.
3. If a secret is found anywhere in history: rotate that key first, then decide on a history rewrite together before flipping.
4. On go: `gh repo edit varunikarai/loadbearing --visibility public --accept-visibility-change-consequences`, then check the repo page logged out: the licence must show as Apache-2.0.

**Done when.** "go" is in the Log and the repo is public with the licence detected.
**Hands to.** A6, A7, A10 (public links).

### V7 · Prior art and evidence · non-tech · 3 pts · Tue 10-20

**Why.** Quality of the Idea asks whether the team "shows genuine understanding of the problem space". Naming the right prior work, and saying exactly how Loadbearing differs, is that evidence.
**Owns.** `docs/prior-art.md` and the README prior-art section.
**Steps.**
1. Leads to verify. Open each source yourself before citing it:
   - metamorphic testing: Chen, Cheung and Yiu (1998), HKUST technical report; Segura et al., "A Survey on Metamorphic Testing", IEEE TSE (2016)
   - global sensitivity analysis: Saltelli et al., *Global Sensitivity Analysis: The Primer* (2008)
   - input ablation
   - how LLMs use or ignore their context: Liu et al., "Lost in the Middle", TACL (2024)
2. For each, one line on what it does and one on how Loadbearing differs: it mutates inputs, not code; one field at a time from a byte-identical checkpoint; a defect claim tied to declared or sourced intent; and a fix that is proven, not suggested.
3. Three documented real cases of a pipeline silently ignoring an input, each with a source. These feed Potential Impact.

**Done when.** Every claim links a source you opened, and the README section is at most five lines with a link to the full page.
**Hands to.** V8, V10, A10.

### V8 · README narrative ✍ · non-tech · 3 pts · Sun 10-18

**Why.** The README is the first thing a judge opens.
**Owns.** README top pitch, "Why it matters", prior art (from V7), team.
**Steps.**
1. Top: the problem in three sentences, using the LLM demo target's real defect as the example.
2. One image above the fold: the fork tree or the before and after proof (from A5 or V9).
3. "Why it matters": the V7 cases.
4. Team: who built what, matching this plan.
5. Leave Aeshvarya's sections untouched.

**Done when.** A first-time reader can say what Loadbearing does, and why it matters, within a minute.
**Hands to.** A10 reuses the framing.

### V9 · Visual identity · non-tech · 4 pts · palette Sat 10-10, the rest Tue 10-20

**Why.** Design is 25% of the score, and hand-drawn originals stand out against template graphics.
**Owns.** `assets/`.
**Steps.**
1. Sat 10-10: a palette of five colours with hex values, readable in light and dark, handed to A5.
2. A wordmark or logo, drawn by hand and digitised (SVG or a high-resolution PNG).
3. The find, explain, fix, prove diagram, drawn on the checkpoint tree: one checkpoint, the forks, the fix fork, the proof.
4. A Devpost cover image (take the size from the Devpost edit page) and a 1280×720 video thumbnail.

**Done when.** All four are in `assets/` and used in the README, the video and Devpost.
**Hands to.** A5, A9, A10, V8.

### V10 · Video script and voice ✍ · non-tech · 3 pts · outline Sun 10-11, narration Sun 10-18

**Why.** The video is a hard deliverable, and its audio must cover how Token Factory and the NVIDIA model are used.
**Owns.** The script and the narration audio.
**Steps.**
1. Sun 10-11: outline to this shape, 3:00 at most, about 400 spoken words:
   - 0:00 to 0:20, the hook: a confident, wrong answer
   - 0:20 to 0:45, the problem
   - 0:45 to 1:45, the probe on the LLM target: checkpoint, parallel forks, verdicts, Nano, Super, Ultra, Tavily evidence
   - 1:45 to 2:30, fix and prove
   - 2:30 to 2:50, what Token Factory Sandboxes and Nemotron each do, said out loud
   - 2:50 to 3:00, the close
2. Sun 10-18: record the narration in a quiet room, one take per section, as WAV or high-bitrate MP3.
3. Mon 10-19 evening: check A9's captions word for word.

**Done when.** The narration files are with A9, and every required mention is spoken.
**Hands to.** A9.

### V11 · Feedback: Sandboxes and Tavily ✍ · non-tech · 1.5 pts · draft Tue 10-20, final Fri 10-23

**Why.** Most Valuable Feedback pays ten winners, and specific, reproducible feedback is what wins it.
**Owns.** `docs/feedback/sandboxes-tavily.md`.
**Steps.** Keep notes during V1 and V4: exact errors, confusing docs, missing features, and what was excellent. In the final version, give every point steps to reproduce and a concrete suggestion.
**Done when.** The final file is merged, and A12 knows where it gets submitted.

### V12 · Judging self-review · non-tech · 2 pts · Tue 10-20 and Fri 10-23

**Why.** Find and fix the weakest criterion while there is still time.
**Owns.** Two review entries in the Log.
**Steps.** Score each of the four criteria from 1 to 10 against the evidence a judge would actually see, cross-check A12's Stage One checklist, and list the top three gaps with an owner for each.
**Done when.** Both reviews are logged and every gap has an owner.

## Aeshvarya's tasks

### A1 · Contracts · tech · 2 pts · Fri 10-09

**Why.** Everything in this plan builds on these seams. Landing them first lets both builders work without waiting on each other.
**Owns.** `target.py`, `backends/base.py`, the `report.py` docstring, CLI flag names.
**Needs.** Nothing.
**Steps.**
1. C1: the four `target.json` keys with their defaults. Today's targets must keep working unchanged.
2. C2: `apply(checkpoint, files)` on the Backend protocol. The implementations come in A4.
3. C5: list the schema-2 fields in the `report.py` docstring.
4. C6: reserve the CLI flags. Each prints "not built yet" until its function is on `main`.

**Done when.** Merged, tests pass, and Varunika has acknowledged it in PROGRESS.md.
**Hands to.** V3, V4, V5, A2, A4, A5.

### A2 · Secrets into forks · tech · 2 pts · Sat 10-10

**Why.** The LLM target calls Nemotron from inside every fork, so the key has to get in, and it must never be baked into a checkpoint: Sandboxes keeps checkpoints for 180 days.
**Owns.** Run-time `env` handling in `backends/local.py` and `backends/contree.py`, and its tests.
**Needs.** A1 (`env`).
**Steps.**
1. Variables named in `target.env` are read from the host at run time and passed only to baseline and fork runs, never to the setup run.
2. Local: the subprocess `env`. Sandbox: the run's `env` parameter.
3. Test: after a probe, no file in the local checkpoint contains the key's value; a target without `env` behaves exactly as before.

**Done when.** Tests pass, and once live, a Sandboxes fork can read the key while the checkpoint image does not contain it.
**Hands to.** A3.

### A3 · LLM demo target · tech · 6 pts · shortlist Fri 10-09, local Tue 10-13, on Sandboxes Sat 10-17

**Why.** The demo target carries Design and Potential Impact. Decided 2026-10-06: an LLM pipeline on Nemotron.
**Owns.** `examples/<target>/`.
**Needs.** A2, V3. V1 for the Sandboxes run.
**Steps.**
1. Fri 10-09: post three candidates under Open questions in PROGRESS.md, each with its planted defect and why a judge would recognise it. Shapes worth considering:
   - a retrieval answerer whose prompt template reads the retrieved passage under the wrong key, so it answers fluently from the model's priors
   - a tool-calling step whose tool result field was renamed, so the model fills the value in itself
   - a summariser whose instructions field never reaches the prompt
2. Varunika picks one on Sat 10-10 morning.
3. Build it with the standard library only: Nemotron through Token Factory, temperature 0, reading `input.json` and printing JSON.
4. Plant one real silent passthrough. Note any irrelevant field the model reacts to beyond the noise floor: that is a phantom sensitivity for free.
5. Set `docs` to public pages that state what the pipeline is supposed to read (for V4), `baseline_runs: 5`, `env: ["NEBIUS_API_KEY"]`, and `sources`.

**Done when.** A probe on Sandboxes, with the noise floor on, finds the planted defect, and that run is saved for the demo.
**Hands to.** V4, V5, A4, A6, A9.

### A4 · Fix and prove · tech · 5 pts · toy Tue 10-13, Sandboxes Fri 10-16, LLM target Sat 10-17

**Why.** The second half of closing the loop: show that the fix removed the defect and changed nothing else, starting from the same checkpoint.
**Owns.** `prove.py`, `Backend.apply` in both backends, the `--fix` and `--prove` wiring, and their tests.
**Needs.** C3 from V5 (Fri 10-09); V5's writer for the live run.
**Steps.**
1. `apply`: local copies the checkpoint directory and writes the files; Sandboxes calls `apply_files` on the checkpoint image. The original is never changed.
2. `prove(target, backend, fix, before) -> Proof`: probe again on the patched checkpoint and compare verdicts field by field.
3. `fixed` means the fix's field no longer has the defect. `new_defects` lists defects that appear only after the fix.
4. Tue 10-13: on the toy target, with a hand-written `Fix` for `body`, `body` becomes load-bearing, `submitted_at` stays a phantom sensitivity, and there are no new defects.

**Done when.** `--prove` closes the loop on the LLM target on Sandboxes on 10-17.
**Hands to.** A5, A9.

### A5 · Report and UI v2 · tech · 5 pts · Sat 10-17

**Why.** Design is 25% of the score, and the report is what judges look at in the demo and the video.
**Owns.** `report.py` (schema 2), `html_report.py`, the `serve.py` pages.
**Needs.** C5. V9's palette (Sat 10-10) and logo.
**Steps.**
1. Schema 2 with every C5 field. Build against a fixture JSON that has all of them, so live runs never block you.
2. HTML: unstable keys, the Super line and the Ultra explanation per field, Tavily evidence with its quote and link, the fix diff, and a before and after proof panel next to the fork tree.
3. Adopt V9's palette and logo. Check contrast, and check a phone-width view.
4. Still one self-contained file that loads nothing from outside.

**Done when.** The LLM target's full report (probe, evidence, fix, proof) reads clearly on a laptop and on a phone.
**Hands to.** A6, A9, V8.

### A6 · Hosted demo · tech · 4 pts · live Sun 10-11, final Sat 10-17, up through judging

**Why.** A hard deliverable. It has to work for a judge who clicks through from Devpost.
**Owns.** Hosting, deploys, uptime.
**Needs.** A3 and A5 for the final version.
**Steps.**
1. Pick the host (Render, Fly or Railway) and deploy the Dockerfile with the toy target on the local backend. Live by 10-11, URL in PROGRESS.md. If connecting the host to the repo needs owner approval, ask Varunika.
2. 10-17: add the recorded Sandboxes runs of the LLM target and serve with `--readonly`, so visits never spend credits.
3. A health check. Make sure a free tier does not sleep through a judge's visit.
4. Check it logged out on 10-18, 10-23 and 10-25.

**Done when.** The URL works logged out and shows the LLM target's full report.
**Hands to.** A10, A12, V8.

### A7 · CI and clean-clone check · tech · 2 pts · Sun 10-18

**Why.** The README commands have to work for a stranger on a fresh machine.
**Owns.** `.github/workflows/`, the README setup and usage sections.
**Steps.**
1. CI runs every new module's tests, offline.
2. A job that clones fresh, runs `pip install .`, and executes the README quickstart exactly as written.
3. README setup, Sandboxes, target format and demo sections brought up to date with every new flag and key.

**Done when.** CI is green on `main`, and the clean-clone job passes.
**Hands to.** V6 (the audit runs after this), A12.

### A8 · Field scan · non-tech · 2 pts · Tue 10-13

**Why.** It confirms nobody else is building Loadbearing, and sharpens how we describe the difference. Read only: nothing is copied, because the rules require original work.
**Owns.** Private notes, kept outside this repo since it goes public, plus one Decisions line with the conclusion.
**Steps.** Look through public GitHub repos and any visible Devpost entries for this hackathon. For each relevant one, note what it does, its track, its overlap with us, and whether it uses Tavily.
**Done when.** The Decisions line is in, and anything that changes our framing is flagged to V8 and A10.

### A9 · Video production · non-tech · 5 pts · storyboard Mon 10-12, recordings Sat 10-17, uploaded Wed 10-21

**Why.** A hard deliverable, and historically the one most often dropped.
**Owns.** Storyboard, screen recordings, edit, captions, upload.
**Needs.** V10's outline (10-11) and narration (10-18), the closed loop (10-17), V9's diagram and logo (10-20).
**Steps.**
1. Storyboard: one shot per script section, saying what is on screen.
2. 10-17: record the terminal and the report at 1080p with a large font, and no personal tabs or notifications.
3. Edit to V10's narration, add V9's diagram and logo, and add captions.
4. Upload publicly to YouTube by Wed 10-21. Confirm it runs 3:00 or less, has audio, and plays logged out.

**Done when.** The public link is in PROGRESS.md.
**Hands to.** A10, A12.

### A10 · Devpost page ✍ · non-tech · 3 pts · draft Tue 10-20, final Fri 10-23

**Why.** It is what judges read alongside the video.
**Owns.** The Devpost project page.
**Steps.**
1. By Sun 10-11: confirm both builders are on the Devpost project team.
2. Sections: Inspiration; What it does; How we built it, naming Token Factory Sandboxes, Nemotron Nano, Super and Ultra, and Tavily, each with its job; Challenges; Accomplishments; What we learned; What's next.
3. Track: Coding and Agentic Engineering. Built-with tags. Links to the repo, the demo and the video. Gallery: V9's cover, the report, the fork tree, the fix proof, the diagram.

**Done when.** The final version is saved on 10-23 and Varunika has read it.
**Hands to.** A12.

### A11 · Feedback: Token Factory and Nemotron ✍ · non-tech · 1.5 pts · Fri 10-23

**Why.** The second half of the Most Valuable Feedback entry.
**Owns.** `docs/feedback/token-factory-nemotron.md`.
**Steps.** Keep notes while building A2 to A4. In the final version, give every point steps to reproduce and a concrete suggestion: the inference API, model behaviour, the docs, and model IDs not being published.
**Done when.** Merged.

### A12 · Compliance and submission · non-tech · 2 pts · checklist Tue 10-20, submit Sun 10-25

**Why.** Stage One is pass or fail, and one missing item kills the entry.
**Owns.** The checklist (in PROGRESS.md) and the final Devpost submit.
**Steps.**
1. A checklist from the official rules: Token Factory or AI Cloud used; an NVIDIA open model used; the repo public with an OSS licence; the demo URL works; the video is public, 3:00 or less, with audio covering Token Factory and the model; the track chosen; the team listed.
2. By 10-20: find out how Most Valuable Feedback is submitted.
3. Sun 10-25: submit. Varunika checks every link logged out the same day.

**Done when.** Submitted on 10-25, and verified.

## Balance

| | Tech | Non-tech | Total |
|---|---|---|---|
| Varunika | 24 (V1 to V6) | 16.5 (V7 to V12) | 40.5 |
| Aeshvarya | 26 (A1 to A7) | 13.5 (A8 to A12) | 39.5 |

Every kind of work has one owner on each side:

| Kind of work | Varunika | Aeshvarya |
|---|---|---|
| Live platform | V1 Sandboxes live run | A6 hosted demo |
| Models | V2 Nemotron layer, V4 Tavily intent | A3 LLM target on Nemotron |
| Engine | V3 noise floor | A1 contracts, A2 secrets into forks |
| Closing the loop | V5 fix writer | A4 fix and prove |
| Quality and safety | V6 pre-public audit | A7 CI and clean clone |
| What judges look at | V9 visual identity | A5 report and UI |
| Judged writing | V8 README narrative | A10 Devpost page |
| Video | V10 script and voice | A9 production |
| Research | V7 prior art | A8 field scan |
| Feedback prize | V11 | A11 |
| Final checks | V12 self-review | A12 compliance and submission |

## Timeline

Varunika's build days are weekends, Friday evenings, Mon 10-19 evening and Tue 10-20. Aeshvarya's due dates are hand-off dates; he chooses his own hours.

| Date | Varunika | Aeshvarya | Together |
|---|---|---|---|
| Wed 10-07 | | A1 contracts | |
| Thu 10-08 | | A1 contracts | |
| Fri 10-09 | V1 prep: credits, install, `contree auth`, model IDs. V5 `Fix` contract | A1 merged. A3 shortlist posted. Own credits and `contree auth` | |
| Sat 10-10 | V1 live run (morning). V3 noise floor (afternoon). V9 palette (evening) | A2 secrets into forks. A3 build starts | Morning: Varunika picks the LLM target |
| Sun 10-11 | V2 Nemotron layer. V10 outline | A6 demo live with the toy target. Devpost team confirmed | **Contracts frozen** |
| Mon 10-12 | | A9 storyboard. A4 on the toy target | |
| Tue 10-13 | | A3 runs locally. A4 on the toy target done. A8 field scan | |
| Wed 10-14 to Thu 10-15 | | A5 report v2 against fixtures | |
| Fri 10-16 | V4 part 1. V5 on the toy target | A4 on Sandboxes. A5 | |
| Sat 10-17 | V4 part 2. V5 on the LLM target | A3 on Sandboxes. A5 palette and logo. A6 recorded runs. A9 screen recordings | **Loop closed on the LLM target, on Sandboxes** |
| Sun 10-18 | V6 audit, then the public flip. V8 README narrative. V10 narration | A7 CI and clean clone, before the audit | **Repo public** |
| Mon 10-19 | V9 logo and diagram (evening). V10 caption check | A9 edit | |
| Tue 10-20 | V9 finished. V7 prior art. V11 draft. V12 review 1 | A9 edit. A10 draft. A12 checklist | Review 1 gaps assigned |
| Wed 10-21 | | A9 video uploaded | |
| Thu 10-22 | | Fixes from review 1 | |
| Fri 10-23 | V11 final. V12 review 2 | A10 final. A11 final | **Feature freeze** |
| Sat 10-24 | Not available | Buffer | |
| Sun 10-25 | Every link checked logged out | A12 submits | **Submitted** |
| Mon 10-26 to Thu 10-29 | Buffer | Demo uptime | Fixes only |
| Fri 10-30 | | | Deadline 10:00 PT, 22:30 IST |

Two dates differ from the original deliverables list, on purpose: the video moves to Wed 10-21 because it has to show the loop closed on 10-17, and the feedback is final on Fri 10-23, two days earlier than needed.

## What each judging criterion sees

| Criterion | What a judge sees | Tasks |
|---|---|---|
| Technological Implementation (25%) | Live Sandboxes numbers, the Nemotron routing working, tests and CI, a fix proven from the same checkpoint | V1, V2, V3, V5, A2, A4, A7 |
| Design (25%) | The report and the demo, the hand-drawn identity, the video | V9, A5, A6, A9 |
| Potential Impact (25%) | A realistic LLM pipeline failing silently, real cases with sources | A3, V7, V8, A10 |
| Quality of the Idea (25%) | Find, explain, fix, prove on one checkpoint primitive; intent drawn from sources; the prior art and how this differs | V4, V5, A4, V7, SPEC.md |
| Stage One (pass or fail) | Every requirement met | A12 |
| Best Use of Tavily ($3,000) | A runtime call that decides intent, with quotes and links | V4, shown in A5 and A9 |
| Most Valuable Feedback | Two specific, reproducible feedback files | V11, A11 |

## Risks

| Risk | Early signal | Response |
|---|---|---|
| Sandboxes fails live | V1 not done by Sat 10-10 noon | Fix in `contree.py`; Builders Program office hours. Stage One still passes on Token Factory inference with Nemotron, and the local backend keeps the demo alive while it is fixed |
| The LLM target is too noisy | V3 marks most of its keys unstable | Temperature 0, structured JSON output, fewer free-text fields, `baseline_runs` up to 8 |
| Credits run out | Balances logged in V1 | Read-only demo on recorded runs, cached Tavily results, a per-run budget |
| Sat 10-17 slips | Loop not closed by Saturday night | The cut order below |
| One builder unavailable | No Log entry on their tasks for two days | The other takes the next open task on the Board; every task is written to be picked up cold |
| Merge conflicts | A branch touching the other's paths | The ownership map, and rebase before merging |

## Cut order, if behind

Hard deliverables are never cut. If time runs short, drop these in this order:

1. V4 refinements beyond the first version. Keep the live Tavily call and the cached evidence.
2. A5 polish beyond the core panels.
3. Closing the loop on the LLM target. Keep it on the toy target, still on Sandboxes.
4. Phantom sensitivity on the LLM target. Silent passthrough alone carries the demo.
