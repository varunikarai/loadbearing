# Progress

Where Loadbearing is, what happens next, and what has already happened. **Now**, **Plan** and **Decisions** are enough to pick up the work. The **Log** is history; read it only when you need it.

## How to use this file

1. **Start of a session:** read Now, Plan, Decisions and Open questions.
2. **End of any session that touched the repo:** add an entry at the top of the Log and update Now if it changed. Commit it with the work, or straight after.
3. **Log output, not effort.** What shipped, what broke, what is next, who did it. Five lines at most per day.
4. **Decisions are not reopened** without new evidence. If one changes, add a new dated line below it; never edit the old one.
5. **Dates are absolute:** 2026-10-10, never "next week".
6. **Never in this file:** keys, tokens, or material from any employer or other project. This repo goes public by 2026-10-18, and so does everything written here.

## Now

_Updated 2026-10-06_

- **State:** the vertical slice runs end to end on the local backend: toy target, 15 forks from one checkpoint, both planted bugs caught. Report (JSON and HTML), demo server, Dockerfile and CI are on `main`, 34/34 tests pass. The Sandboxes backend and Nemotron Nano classification are written but have never run against a live account.
- **Next action:** Fri 2026-10-09, Aeshvarya: A1 contracts and the A3 shortlist. Sat 2026-10-10, Varunika: before 11:00, V1 prep (credits, `pip install -e '.[sandbox]'`, `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID` into `.env`, model IDs into `.env`) and the `Fix` contract (V5); from 12:00, V1 live, `loadbearing probe examples/ticket_triage/target.json --backend sandbox --nano`, pass = the same two defects, found on Nebius.
- **Waiting on:** Aeshvarya confirming the split in WORKPLAN.md by 2026-10-09.
- **Deadline:** 2026-10-30 10:00 PT (22:30 IST). **Target submission: 2026-10-25.**

## Plan

Every task, owner, contract and date is in **[WORKPLAN.md](WORKPLAN.md)**. Start with its Board. The milestones:

| Date | Milestone |
|---|---|
| Fri 2026-10-09 | Contracts on `main` (A1). LLM target shortlist posted (A3) |
| Sat 2026-10-10 | `Fix` contract (V5). Sandboxes runs live (V1). LLM target picked. Noise floor done (V3) |
| Sun 2026-10-11 | Nemotron layer verified (V2). Hosted demo live (A6). **Contracts frozen** |
| Sat 2026-10-17 | **Loop closed on the LLM target, on Sandboxes** (V4, V5, A3, A4, A5) |
| Sun 2026-10-18 | **Repo public** after the audit (V6). README narrative (V8) |
| Wed 2026-10-21 | Video public on YouTube (A9) |
| Fri 2026-10-23 | **Feature freeze.** Devpost page and both feedback files final |
| Sun 2026-10-25 | **Submitted** (A12) |
| Fri 2026-10-30 | Deadline, 10:00 PT, 22:30 IST |

### Hard deliverables

Each one missing kills the entry.

| Deliverable | Due | Status |
|---|---|---|
| Runs on Token Factory or AI Cloud, uses an NVIDIA open model | stage 1 pass/fail | Code written, not yet run live |
| Public repo, OSS licence visible at the top | 2026-10-18 (V6) | Apache 2.0 committed. Repo private until Varunika flips it after the audit: `gh repo edit varunikarai/loadbearing --visibility public --accept-visibility-change-consequences` |
| README with setup and Nebius / Nemotron usage | 2026-10-18 (V8, A7), prior art 2026-10-20 (V7) | Technical sections drafted. Pitch and team section not written |
| Hosted demo URL | live 2026-10-11, final 2026-10-17 (A6) | Server and Docker image built and checked locally. Host not chosen, not deployed |
| Public YouTube video, 3 min or less, **with audio**, covering Token Factory and the NVIDIA model used | 2026-10-21 (A9, V10). Moved from 10-18 so it can show the loop closed on 10-17 | Not started |
| Written Nebius / NVIDIA tooling feedback | 2026-10-23 (V11, A11) | Not started |

**Aiming at:** Coding and Agentic Engineering track, Best Use of Tavily ($3,000, needs a functional runtime Tavily call), the overall prizes, Most Valuable Feedback ($100).

## Decisions

- **2026-09-20** Build Loadbearing, not an autonomous PR agent: one already exists in this hackathon. Idea locked, no pivots.
- **2026-09-20** Track: Coding and Agentic Engineering. Tavily is a runtime dependency on purpose.
- **2026-09-20** Models routed by job: Nano per fork, Super across forks, Ultra for the explanation.
- **2026-09-30** The core is stdlib only and the Sandboxes SDK is an optional extra. The local backend is for development; the submission runs on Sandboxes.
- **2026-09-30** Nemotron model IDs live in `.env`, never in code. They are not published in the docs; `loadbearing models` lists them.
- **2026-09-30** Repo private until 2026-10-18, so the idea cannot be scouted before it is built.
- **2026-09-30** Commits: one concern each, the message says why, each person commits as themselves.
- **2026-10-06** Close the loop: find, explain, fix, prove. Ultra writes the smallest fix, the fix is applied in a fresh fork of the same checkpoint, and the probe re-runs to show the defect gone. Makes "agents that write, run, and test code" explicit. (Proposed by Aeshvarya, accepted by Varunika.)
- **2026-10-06** The demo target is an LLM pipeline on Nemotron, such as a retrieval or tool-calling step that silently ignores a retrieved field. Which one is still open. (Aeshvarya, accepted.)
- **2026-10-06** Noise floor: the baseline runs k times, and output keys that vary on their own are marked unstable and left out of verdicts, instead of voiding the whole report. (Aeshvarya, accepted.)
- **2026-10-06** Tavily infers `expects` for undeclared fields from upstream docs, so an undeclared field can carry a defect claim. (Aeshvarya, accepted.)
- **2026-10-06** Prior art in the README: metamorphic testing and input ablation or sensitivity analysis. Not mutation testing, which mutates the code, not the inputs. (Aeshvarya, accepted.)

## Open questions

- **Work split:** written in full in [WORKPLAN.md](WORKPLAN.md) by Varunika on 2026-10-06, 40.5 points hers and 39.5 his, tech and non-tech on both sides. Aeshvarya confirms it, or counters a specific task, here by Fri 2026-10-09, before A1 lands.
- **Demo target pipeline:** an LLM pipeline on Nemotron (decided 2026-10-06), but which one is not chosen. Due Sat 2026-10-10.
  A3 shortlist (Aeshvarya, 2026-10-06). All three use the standard library and Nemotron through Token Factory at temperature 0, read `input.json`, print JSON, and carry `env: ["NEBIUS_API_KEY"]`.
  1. **Support answerer over retrieved policy (RAG).** Record: `question`, `passages` (retrieved policy text), `user_id`, `request_ts`. Planted defect: the prompt is filled from `record.get("context", "")`, but the retriever writes `passages`, so the model answers from its priors. Asked "how long do I have to return this?" with a passage saying 14 days, it says 30, fluently. Silent passthrough on `passages`. Why a judge recognises it: everyone has shipped or used RAG, and "it answered without reading the docs" is the failure people fear most. Docs for V4: retrieval-augmented generation guides that say answers must be grounded in the retrieved context. Prior art fit: Lost in the Middle (V7).
  2. **Tool-calling agent after an API rename.** Record: `user_message`, `tool_result` (a weather API response with `temp_c`), `session_id`. Planted defect: the agent reads `tool_result.get("temperature")`, a field the API renamed to `temp_c`, gets `None`, and the model fills in a plausible temperature itself. Silent passthrough on `tool_result.temp_c`. Why a judge recognises it: schema drift breaking agents quietly is a well-known pain, and it is "agentic" on its face. Docs for V4: the weather API's public reference, which names `temp_c`. This gives Tavily the clearest job of the three: the current docs settle what the field is called.
  3. **Meeting summariser that drops its instructions.** Record: `transcript`, `instructions` ("action items only, max 5 bullets"), `meeting_id`. Planted defect: `instructions` is formatted into a variable that is never placed in the prompt. Silent passthrough on `instructions`. Weaker: the output still looks like a reasonable summary, so the defect is harder to show on screen in a few seconds.

  Recommendation: **1**, with 2 as the fallback. 1 has the most legible before and after on camera (14 days becomes 30 days), and the A4 proof lands as a plain sentence: after the fix, the answer says 14. 2 is the better Tavily story, so if V4 needs a stronger runtime job, pick 2.
- **Hosted demo shape:** settled by `loadbearing serve` (merged 2026-10-06): pick a target, run or view a probe, read-only mode for recorded runs.
- **Credits:** do they cover Sandboxes runs or only inference? Check the console balance after the first Sandboxes run.
- **Demo host:** Render, Fly or Railway; all take the Dockerfile as is. Aeshvarya to pick by 2026-10-11.

Aeshvarya's five proposals from 2026-10-06 were all accepted the same day; they are now in Decisions.

## Quick reference

```bash
PYTHONPATH=src python3 -m loadbearing probe examples/ticket_triage/target.json   # local slice
PYTHONPATH=src python3 -m unittest discover -s tests                              # tests
```

Problem statement: [SPEC.md](SPEC.md). Setup, target format, layout: [README.md](README.md).

## Log

Newest first.

### 2026-10-07
- **V5 writer done offline** (Varunika, merge `51b0ef5`): `NemotronRouter.write_fix` (Ultra returns whole new file contents and a rationale) and `fix.write_fix`, which refuses any fix that touches a file outside `sources`, no longer compiles, changes nothing, or rewrites more than half a file. The C5 fields are on `FieldVerdict` (`intent_source`, `evidence`, `reconciliation`, `explanation`), and `tests/fakes.py` gives both sides an offline Token Factory client and router. An offline loop test probes the toy target, has a fake Ultra fix `body`, and runs `prove()`: `body` becomes load-bearing, the outage ticket comes out P1, no new defect. Live Ultra check waits on V1.
- **V3 noise floor done** (Varunika, merge `e21d43e`): the unmutated record runs `baseline_runs` times alongside the forks; keys that differ between those runs are left out of every comparison; `Report.unstable_keys`, `Report.baseline_runs` and `Report.void` exist; `probe(..., baseline_runs=N)` overrides the target. The toy target is unchanged. 84 tests pass.
- **Hand-offs to Aeshvarya**, all in his files:
  1. `--fix` and `--prove`: the writer is ready. `write_fix(verdict, target, NemotronRouter.from_env(tiers=("ultra",)))` per defect, then `prove()`.
  2. `--baseline-runs`: pass it as `probe(..., baseline_runs=args.baseline_runs)`.
  3. `cli.render`: the "baseline disagrees with itself, so no verdict below is sound" warning should key on `report.void`, not `not report.deterministic`, and list `report.unstable_keys` when there are any. Today it would wrongly void an LLM target's whole report.
  4. Run counts: `timing_line` and `report.py` count runs as `len(report.forks) + 2`; with the noise floor that is `+ report.baseline_runs`.
  5. Schema 2 (A5): `baseline_runs`, `unstable_keys` and the four new verdict fields are on the dataclasses now.
- **Waiting on Varunika:** the A3 pick (RAG answerer, weather agent, or summariser).

### 2026-10-06 (g)
- Sandboxes backend rebuilt on contree-sdk 0.3.6 after reading its source (Aeshvarya): the old client import did not exist, the project variable is `NEBIUS_PROJECT_ID`, and there is no `contree auth`. Networking is on by default, so a fork can call Nemotron.
- A1 contracts (C1, C2, C5, C6) and A2 secrets into forks merged, three and four days early. A setup run can no longer write a key into a checkpoint.
- A4 on the toy target: `apply` on both backends and `prove()`. The real `body` fix is proven clean (the outage ticket becomes P1); a fix that leaks `ticket_id` is caught as a new defect. 60/60 tests.
- A3 shortlist posted under Open questions; recommendation is the RAG answerer. Next for Aeshvarya: own credits and `.env`, then A3 once the target is picked on Sat 2026-10-10.

### 2026-10-06 (f)
- `Fix` contract (C3) on `main` (Varunika, `460c787`), four days early: `src/loadbearing/fix.py` plus tests built on the toy target's real `bdoy` to `body` fix, so A4 can prove against a known-good fix now.
- Pulled Aeshvarya's Sandboxes backend rebuilt on contree-sdk 0.3.6 and his A1 contracts; the full suite passes with all of it on `main`.
- Next for Varunika: Sat 2026-10-10, V1 (no `contree auth` step any more: key and project ID go in `.env`), then V3.

### 2026-10-06 (e)
- WORKPLAN.md written (Varunika): 24 tasks, 12 each, every one with why, owned files, prerequisites, steps and a done test; seven contracts so neither side waits; an ownership map; a day-by-day timeline to submission on 10-25; the judging criteria mapped to tasks; risks and a cut order.
- Balance: Varunika 24 tech and 16.5 non-tech, Aeshvarya 26 tech and 13.5 non-tech.
- Next: Aeshvarya confirms or counters by Fri 2026-10-09.

### 2026-10-06 (d)
- Varunika accepted all five of Aeshvarya's proposals. Recorded in Decisions, scheduled in Plan, written into SPEC.md (find, explain, fix, prove; LLM targets with a noise floor; Tavily inferring `expects`), and listed as open in the README status.
- Next: Sat 2026-10-10, the live Sandboxes run and picking the LLM demo target. Everything accepted today depends on both.

### 2026-10-06 (c)
- Reviewed and merged `aeshvarya/report-and-demo` into `main` (Varunika, `47514fc`). 34/34 tests and the probe gate pass on the branch and on `main`. The server only runs targets listed at startup.
- Stage One wording checked against the rules: the track asks for "coding agents and developer tools: agents that write, run, and test code in Token Factory". Loadbearing qualifies as a developer tool today; closing the loop would make the fit stronger, not rescue it.
- Prior art: mutation testing mutates the code, not the inputs, so it is not the right citation. The README's prior-art section, not yet written, should name metamorphic testing and input ablation or sensitivity analysis.

### 2026-10-06 (b)
- Invite accepted (Aeshvarya). Read the repo end to end; the slice runs and 18/18 tests pass as written.
- Built on `aeshvarya/report-and-demo`: per-run timing; versioned JSON report; self-contained HTML report around the fork tree; `loadbearing serve` with cache and `--readonly`; `$PORT`; Dockerfile (checked in a container); CI running tests and the probe gate. 34/34 tests.
- Next: Varunika merges, Aeshvarya picks a host and deploys by 2026-10-11.

### 2026-10-06
- Aeshvarya invited to the repo with write access (Varunika). Invite expires 2026-10-13.
- Credits: Nebius Builders Program form in progress (Varunika). Hackathon code form (`NEBIUS-DEVPOST-GLOBAL26`) not yet confirmed done.
- No commits 2026-10-01 to 10-06. The planned 2026-10-02 to 10-04 build block did not happen; its next action moves to 2026-10-10.
- This file added.

### 2026-10-01
- Aeshvarya confirmed on the team.

### 2026-09-30
- Repo created (Varunika): mutation engine, checkpoint-and-fork engine, verdicts, local and Sandboxes backends, Nemotron router, Tavily client, CLI, toy target.
- Slice runs locally: 15 forks from one checkpoint, both planted bugs caught, 18/18 tests.

### 2026-09-20
- Direction set to Loadbearing. Problem statement written, now [SPEC.md](SPEC.md).

### 2026-09-07
- Registered: Varunika and Aeshvarya.
