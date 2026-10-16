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

_Updated 2026-10-16_

- **State:** the whole loop has run live on Token Factory and Tavily, on the local backend: Nano scores 18, 19 and 19 of 20; on the support answerer Tavily and Super infer `passages` is relevant from a quoted source, Ultra's one-line fix is proven, and the run is recorded in `demo/runs/` for the hosted demo. Ultra fixes by exact-quote edits. Intent comes from the target's own docs first, search only for the gaps. The README leads with the product working, and an inferred field's card says its intent came from docs. 183 tests pass on `main`; the current tree is clean for the audit. **Live:** the hosted demo, https://loadbearing-demo.vercel.app (A6). **Not yet live:** the Sandboxes backend (V1, beta not enabled: 403), any recording made on Sandboxes.
- **Next action:** Aeshvarya, who holds the keys from 10-11: review hand-off 23; Sandboxes beta access, then V1's run (hand-off 20 is in, so the image step is covered), `loadbearing probe examples/ticket_triage/target.json --backend sandbox --nano` (pass = the same two defects, found on Nebius), then the support answerer on Sandboxes. Varunika: V9 palette (was due 10-10) and V10 outline (was due 10-11) on Fri 10-16, then V8 README narrative by 10-18.
- **Waiting on:** Aeshvarya confirming or countering the split in WORKPLAN.md (due 2026-10-09; both are working inside it); Sandboxes beta access.
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
| Runs on Token Factory or AI Cloud, uses an NVIDIA open model | stage 1 pass/fail | Met on Token Factory 10-10: Nano, Super and Ultra live, recorded in `demo/runs/`. Sandboxes not yet run |
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
- **2026-10-07** Demo target: **shortlist option 1, the support answerer over retrieved policy (RAG)**. Planted defect: the prompt reads `context`, the retriever writes `passages`, so a 14-day return policy comes out as 30 days. Option 2 (weather tool agent) is the fallback. (Picked by Varunika from Aeshvarya's shortlist.)

## Open questions

- **Work split:** written in full in [WORKPLAN.md](WORKPLAN.md) by Varunika on 2026-10-06, 40.5 points hers and 39.5 his, tech and non-tech on both sides. Aeshvarya confirms it, or counters a specific task, here by Fri 2026-10-09, before A1 lands.
- **Demo target pipeline:** decided 2026-10-07, the RAG answerer (see Decisions). The shortlist below is kept for the record.
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

### 2026-10-16 (b)
- **A6 live: https://loadbearing-demo.vercel.app** (Aeshvarya). Vercel project linked to the fork, so every sync of `main` redeploys it (the first one did, Ready in 15 s). Checked logged out: the index lists both sections (2 + 54), a free run of the toy target finds both defects in about 1 s, the support answerer's recorded run shows NVIDIA's quote and Ultra's proven fix, and `POST /t/support_answerer/run` is refused 403. No key is set on the host. `DEMO_URL` is set; keep-warm ran green against it.
- The first deploy answered 404 everywhere: Vercel now hands a Python app the rewritten path, so the catch-all rewrite sent every request to `/api/index`. Removed it; Python apps are served on every path.

### 2026-10-16
- **Hand-off 23 reviewed and merged** (Aeshvarya): only moves on fields that should not matter are re-run. Agreed: a move on a field that should matter is not a defect claim. The one cost, for the recording: a chance move on a `passages` fork would hide the silent passthrough in that run, so if the table does not say SILENT PASSTHROUGH, re-run rather than edit anything. README brought in line (three lines).
- **V1, first live attempt:** `loadbearing probe examples/ticket_triage/target.json --backend sandbox` reaches Token Factory, authenticates, and gets `403 Forbidden` on its first call (`/sandboxes/v1/inspect/?tag=python:3.12-slim`): the beta is not enabled for the project yet (form sent 10-10, no reply). The SDK only says "You do not have permission"; the backend now says Sandboxes is likely not enabled and names the project ID. For V11: the 403 never mentions the beta.
- **Hosting docs:** `demo/README.md` says how to host on Vercel (one import, no settings) or Render (`DEMO_URL` for the keep-warm ping).
- 196 tests pass.

### 2026-10-14 (c)
- **Hand-off 18 done** (Aeshvarya, `692c147`): the support answerer re-recorded with own docs first. The cited intent for `passages` is now NVIDIA's own page (checked by Varunika: the quote is on blogs.nvidia.com word for word), the fix is one line, the proof is clean, and the README's screenshots and terminal output come from this run (all seven re-rendered images opened: nothing private in any).
- **Hand-off 23 brought up to date** (Varunika, `varunika/confirm-only-phantoms`): merged with his 16:32 work, kept his new terminal-and-page test, and the report now says only moves on fields that should not matter are re-run. 190 tests on the branch. The recorded run stays a true capture of the version that made it: its "2 moved fork(s) re-run" are the two `question` forks, which a run after 23 would not re-run.

### 2026-10-14 (b)
- **Confirm-moves reviewed** (Varunika, on Aeshvarya's `782fa63`): right aim, a single sampled answer should not make a phantom sensitivity. But it confirmed every moved fork, including fields that should matter, and kept only majority moves. A test with a pipeline that reads `body` but uses it only on some runs shows `main` reporting `body` as a **silent passthrough**: a defect made by noise. It also recorded `moves: 1` on forks that never moved.
- **Hand-off 23 to Aeshvarya, branch `varunika/confirm-only-phantoms`** (for his review; it rewrites his `test_a_real_move_is_confirmed_on_every_run`): confirm only moves on fields that should not matter (declared or inferred), the only place a move is a defect claim; the `received_at` fluke is still caught. Forks that never moved record 0 moves. Three new tests: the weak reader stays load-bearing, a real phantom is confirmed on every run, unmoved forks record no moves. 186 tests pass. **Worth merging before the hand-off 18 re-record:** on the live answerer a proof needs `passages` to move after the fix, and a flaky move there would now count against it.
- Process, once: the change altered the judging step and added `runs` and `moves` to the frozen report contract (C5) without a review. Additive, so nothing breaks; next time a line in PROGRESS.md first.
- Correction to this entry: 186 tests is `main`; the hand-off 23 branch has 189.

### 2026-10-14
- **Hand-offs 21 and 22 reviewed and merged by Aeshvarya** (`51e78fa`, `4af66f2`), before the 24-hour window closed. **Hand-off 20 done** (Aeshvarya, `97d34a0`): the Sandboxes checkpoint now starts from `images.oci()`, which finds the image or imports it, with a test. Checked by Varunika: matches the SDK source, 183 tests pass, audit go on 321 commits, CI green.
- Still open before the 10-17 milestone: hand-off 18 (re-record, re-render, re-score), Sandboxes beta access and V1's run, A6 deployed.

### 2026-10-14
- **Hand-offs 21 and 22 reviewed and merged** (Aeshvarya): a hung fork is recorded as exit 124, a fix that crashes on the real input is never proven, and the README says the old terminal run's proof was not clean. Thanks for catching that one: the full output I pasted ended with `adds defects on received_at` under text saying it was clean.
- **Hand-off 20 done:** `contree.py` calls `images.oci(target.image)`, which finds the tag or imports it; checked against the 0.3.6 source (`_pull_image_by_oci` falls back to `_import_image` on `NotFoundError`).
- **Why that proof was not clean, and the fix** (Aeshvarya, run orchestration in `probe.py`, shared file, please look): `received_at` is never in the prompt, so its move was one sampled answer coming back different. When the noise floor shows a pipeline is not deterministic, a fork that moved now runs `CONFIRM_RUNS = 2` more times and counts as moved only if most of its runs moved. Deterministic pipelines run nothing extra. Forks in the report carry `runs` and `moves` (additive, schema still 2); the terminal prints a `confirmed:` line and the report's noise note names any move that was not counted. On the first live run after it, `destroy:received_at` moved 1 of 3 and was not counted, exactly the case above.
- **Hand-off 18 done:** re-recorded `--intent --prove` twice with the final code; both proofs clean, the evidence is NVIDIA's own page (blogs.nvidia.com, named in `docs.urls`), the fix is the one-line `context` -> `passages`. The recording, the screenshots and the README's terminal block, before/after table and evidence text all come from the second run. `scripts/eval_nano.py`: 19 of 20 on each of three runs; "only latency" now passes, the miss is "punctuation only".
- **A6: the demo runs as a WSGI app** (`wsgi_app()` and `respond()` in `serve.py`, shared with the HTTP server) with a Vercel entry point (`api/index.py`, `vercel.json`): recorded runs copied into `/tmp`, free targets runnable, a run answers with its report instead of a redirect. Checked under `wsgiref`: index, health, a free run, a paid run refused 403, the recorded run with its NVIDIA quote. Deploying needs one dashboard import by Aeshvarya (the connector cannot create projects); Render stays possible from `render.yaml`.
- 191 tests pass.

### 2026-10-13 (c)
- **Bugs fixed in Varunika's files, merged:** destroying an empty list or object returned it unchanged, so a relevant field with an empty baseline value could be reported as a silent passthrough without ever being tested (`197eacc`); a timestamp nudge dropped `.000` or added seconds, changing the format along with the time (`37b2368`); a record key containing a dot crashed the probe mid-run with a `KeyError`, and is now refused before any run (`37b2368`); Token Factory and Tavily calls now retry a 429, a 5xx or a dropped connection with backoff, so one rate limit no longer throws away a paid run (`net.py`, `210b81e`).
- **Before the repo goes public:** the weather diffs in the Nano eval set use a neutral city (only the place name changed); `pyproject.toml` lists both builders as authors. The audit's only remaining hits are in old versions in history, none in the current tree. README lede and hero caption now say the shown runs used the local backend (`73560e9`); SPEC describes exact-quote fixes (`05f678b`).
- **Hand-off 21 to Aeshvarya, branch `varunika/h21-timeout-and-proof`** (his files, merges under rule 4 from 2026-10-14 17:20): `backends/local.py` let a fork that ran past the timeout crash the whole probe, and now records it as exit 124; `prove.py` called a fix proven when the patched pipeline crashed on the real input (the exit code then differs on every fork that changes the field, which counts as a reaction), or when the after-run was void. Each has a test that failed before the fix.
- **Hand-off 22 to Aeshvarya, branch `varunika/h22-readme-sync`** (his README sections, built on 21, merges with it): the expanded terminal output ends with `proof: ... the fix adds defects on received_at`, under text saying no other field gained one; it now says which run is which. Also: how intent is sourced now and why the recorded quote is a search hit, the exact-quote and proof checks, the `docs` reading order, dotted keys, `intent.py` and `net.py` in the layout, and Status.
- **Correction:** the 2026-10-13 (b) entry said 173 tests; it was 172 (one of the three new tests replaced an old one). Now 180 on `main`, 182 with 21 and 22.

### 2026-10-13 (b)
- **Tavily caches keyed on the target's docs and a format version** (Varunika, `intent.py`, `20fe941`): both caches were keyed on the target's name (and the intent cache on its fields), so editing `docs.urls` kept serving the old pages, and a cache from before own-docs-first would have brought the search-hit quote straight back. A stale cache is now fetched again, not trusted. 173 tests pass.
- **Hand-off 18 is simpler for it:** no need to delete anything under `runs/`; re-running `--intent --prove` on the support answerer refetches and re-asks on its own.

### 2026-10-13
- **Hand-off 19 merged** (`2e616e9`) under rule 4: no review in 24 hours counts as approval. An inferred field's evidence card now says its docs, not a declaration, set its intent. 170 tests pass.
- **SPEC brought in line with own docs first** (Varunika, `3938792`): the pipeline's own `docs.urls` settle intent first, search results only the fields those leave open.
- **Hand-off 20 to Aeshvarya**, `backends/contree.py`, before V1's first live run: `checkpoint()` calls `images.use(target.image)`. In contree-sdk 0.3.6, `use()` only builds a reference to the tag and never checks it, so on an account without `python:3.12-slim` the first run fails. `images.oci(target.image)` looks the tag up and imports it from docker.io when it is missing (`_pull_image_by_oci`). Worth switching before the run, or keeping the exact error text for V11 if it fails as predicted.
- **Open on Aeshvarya's side since 10-11:** hand-off 18 (re-record citing NVIDIA's page, re-score Nano; the screenshots also need re-rendering for 19); A6 was due live 10-11 and is not deployed; Sandboxes beta access, which V1 and the 10-17 milestone (loop closed on Sandboxes) both need.

### 2026-10-11 (c)
- **Pre-public check of the nine README screenshots** (Varunika, V6): no keys, paths, user names or addresses in any of them. The text audit cannot read images, so they were opened one by one.
- **Hand-off 19 to Aeshvarya**, `html_report.py`, branch `varunika/h19-inferred-card` (not merged, his review): the evidence card always opened "Declared as an input that should change the output", so the README's own screenshot says `passages` was declared right above the quote that inferred it. Inferred fields now read "Not declared, but its docs say it is an input that should...". Tested; the screenshots need re-rendering with hand-off 18. Reviewed his other 10-11 code: model prose is escaped before any tag is added, so it cannot inject HTML.
- **V12 re-score** (Varunika, estimate, out of 10): Technological Implementation 6 (from 4), Design 5 (from 4), Potential Impact 6 (from 5), Quality of the Idea 7; **24 of 40, from 20**. Top gap now: **Sandboxes**, which the track description names and nothing has touched live. Until it runs, the README's first line ("checkpoints a pipeline once in a Nebius Token Factory Sandbox") describes what the code does, not what any run has shown; if Sandboxes is not live by 2026-10-18, that line changes before the flip. Then the hosted URL and the video.

### 2026-10-11 (b)
- **PR #1 reviewed and merged** (Varunika, `343ba8c`): exact-quote edits close hand-off 16 with no change to `fix.py`, since a line Ultra never quotes cannot come back altered. Follow-up in `nemotron.py` (`6a80d68`): a reply that already starts as a JSON answer keeps think tags quoted inside it; before, an edit quoting `rsplit("</think>")` was cut in half and the fix refused.
- **Own docs first** (Varunika, `intent.py`, `053a100`): the recording quotes a search hit, while the target declares NVIDIA's RAG guides and the README says those are what Super quotes. Super now settles undeclared fields from the target's own `docs.urls` first; search results settle only what those leave open. RAG 101 carries "The LLMs then use the retrieved data to craft appropriate responses." word for word (checked 10-11).
- **Hand-off 17 done** (Varunika, `65b09d9`): Nano's prompt names how long a run took as incidental, next to ids and timestamps. Needs a live re-score.
- **Hand-off 18 to Aeshvarya**, recordings: delete `runs/support-answerer.docs.json` and `.intent.json`, re-record `--intent --prove` so the evidence is NVIDIA's page, then README lines 74 and 236 agree; re-run `scripts/eval_nano.py` for hand-off 17.
- 169 tests pass; audit go on 258 commits.

### 2026-10-11
- **Live keys and runs are Aeshvarya's from here** (agreed 10-11): Varunika needs no key, credits or Sandboxes access. CI, the Docker image and the hosted demo use no secrets, and every paid run is recorded into `demo/runs/`.
- **The whole loop live with Tavily** (Aeshvarya): `--intent --prove` on the support answerer. `passages` was left out of `expects` (hand-off 9), Tavily and Super cite a RAG source saying answers are grounded in the retrieved passages, so the unread field is a defect. Ultra's fix is the one line `context` -> `passages`, the proof is clean, and the answer goes from "Yes... 30-day return window" to "No... the 14-day window has passed, but the warranty covers a repair or replacement". 19 runs in about 9 s on the local backend.
- **Hand-offs 15 and 16, fixed in PR #1** (Aeshvarya, in Varunika's `nemotron.py`, for her review): the first live fix retyped all of `pipeline.py` and rewrote its `<think>` regex too. Ultra now answers with exact old/new edits, each quote unique in its file, so a line it never quoted comes back byte for byte; only a reasoning trace in front of the answer is stripped. The same PR adds the recording and fixes `.gitignore`, whose `runs/` also hid `demo/runs/` and would have left the Dockerfile's `COPY` with nothing on a fresh clone.
- **V2 bar met live:** `scripts/eval_nano.py` scored 18, 19 and 19 of 20. Every run missed the same case, "only latency" (`latency_ms` 812 -> 774 called meaningful). **Hand-off 17 to Varunika**, the Nano prompt: worth naming timings next to ids and timestamps as noise.
- `--explain` live on the toy target: Ultra quotes the `.second % AGENTS` line and the `'bdoy'` key. The CLI now prints the cited intent, Super and Ultra under each defect; before, they reached only `--out`.
- README status now says what has run live.

### 2026-10-10 (e)
- **A13 against Nemotron 3 Super reading the code** (Aeshvarya, three runs, about $0.30): 49, 51 and 49 of 54 cases right, against the probe's 50 on every run; not significant (p = 0.38). Its wrong cases change between runs at temperature 0, and every run it raised a false alarm on `shipping-clean`. Both READMEs now say plainly that on twenty-line pipelines with one-line bugs, reading does about as well; the stated difference is repeatability, the forks as evidence, and the proven fix.
- **Proposal (Aeshvarya), not agreed:** a second benchmark track where the defect is not on a readable line: an LLM step that is given a field and ignores it, or reacts to a field that should not matter (a name, an id). Reading the code cannot see those; running can. It may need a value-swap mutation next to destroy, drop and nudge, which is `mutations.py` (Varunika's), so it is a question, not a claim.

### 2026-10-10 (d)
- **First live Token Factory calls** (Aeshvarya): Nano, Super and Ultra each answer on the default endpoint (`api.tokenfactory.nebius.com/v1/`), about 1 s each. The model IDs are `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b`. The project ID starts `aiproject-`, not `project-`. Sandboxes needs a "Request beta access" click per account; the page says it is free during the beta.
- **A3 live on the local backend:** the old prompt made Nano answer "not enough information", so there was no wrong answer to find. Changed to a decisive-agent prompt: the live baseline now says "Yes, you can still return them for a refund within the 30-day window"; `question` is load-bearing, the ids inert, 19 runs in 8.3 s.
- **The whole loop live** (Super, Ultra, fix, proof; Tavily's intent supplied by hand until the Tavily key is in): Super and Ultra name the `context`/`passages` line, Ultra's fix is proven clean, and the answer after it is `can_return: false`, 14 days, "file a warranty claim for a repair or replacement". 29 s.
- **Hand-off 15 to Varunika**, `nemotron.py`: `chat()` strips `<think>...</think>` from every reply, including a `write_fix` reply whose file content contains that pattern. On the support answerer, whose source strips think tags, Ultra's fix came back with that line rewritten and the final newline changed: two edits unrelated to the defect. Suggest stripping a reasoning trace only before the JSON object starts, never inside it.
- **Hand-off 16 to Varunika**, `fix.py`: `validate` allowed those unrelated edits, because they were small. Worth a check that a fix changes only the lines Ultra's rationale is about, or a prompt line asking to keep every other line byte-identical.

### 2026-10-10 (c)
- **Hand-offs 13 and 14 done** (Aeshvarya): the benchmark is scored per case too (50 of 54 against 26, exact McNemar on cases p = 1.9e-05) and both READMEs lead with it and name the two mechanisms; the read-only demo runs any free target (no keys, local, no model calls) and serves paid runs as recorded, with several target folders listed in sections.
- Fixed a flaky test: the fake Token Factory's listen backlog of 5 refused connections under the probe's parallel runs. Passed 15 in a row.
- **A6 deploy-ready** (Aeshvarya): the image serves the examples and all 54 benchmark cases read-only and copies `demo/runs/` recordings into its cache; `render.yaml`; a keep-warm ping to `DEMO_URL`. Checked in a container. Live once the host account exists.
- A9 storyboard and A12 checklist drafted, kept outside the repo.

### 2026-10-10 (b)
- **V12 dry run** (Varunika, early; the two scored reviews stay on 10-20 and 10-23). Scored against the rules' own wording as if submitted today, out of 10: **Technological Implementation 4** (well built: 154 tests, CI, a reproducible benchmark; but the criterion asks how effectively it *uses* Token Factory and Nemotron, and nothing has run live), **Design 4** ("a complete, coherent product experience": the CLI, report and Action exist, but there is no URL to open, no identity, no video), **Potential Impact 5** (real cases with sources, but "based on what's demonstrated" the demo target has only met a fake Token Factory, and the README never names who it is for), **Quality of the Idea 7** (checkpoint-and-fork as an ablation primitive, rules decide defects so no model can invent one, intent drawn from cited sources, honest limits). Stage One would fail today on schedule alone: private repo, no demo URL, no video, no live call.
- **Top three gaps, each with an owner:**
  1. **Nothing live.** Moves Technological Implementation, Potential Impact, Stage One and the Tavily prize at once. Varunika, V1 today; then Aeshvarya, A3 live.
  2. **No product a judge can touch.** The rules require "a working Project for judging and testing... without any restriction", and the demo as planned runs `--readonly`, so a judge could not run anything. Aeshvarya, A6 (hand-off 14); Varunika, V9.
  3. **The README does not yet answer the rules' question:** "highlight how you've used NVIDIA Nemotron... and where Token Factory accelerated your workflow". The table at line 177 says what each model does, not what it bought. It needs V1's numbers (one checkpoint instead of N setups, parallel speedup, Nano's cost per fork) and should sit near the top, with the audience named. Varunika, V8 after V1.
- **Hand-off 14 to Aeshvarya**, `serve.py` (A6), a proposal: let anyone run the targets that cost nothing (the toy target and the benchmark cases on the local backend), and serve the Sandboxes and Nemotron runs as recorded; keep only paid runs read-only. Judges can then press run and see it work, and the credits stay safe.

### 2026-10-10
- **Hand-offs 10 to 12 checked on `main`** (Varunika): a crash exits 2 with its traceback, the action installs the sandbox extra, A8 is done. 154 tests pass; audit go on 201 commits.
- **A13 reproduced** (Varunika): `bench/generate.py` rebuilds every case byte for byte and `bench/run.py` gives the same calls (48 of 49 with 3 false alarms; static 35 with 22); only the seconds differ. p = 1.86e-07 and the precision and recall figures recomputed by hand: all match.
- **Hand-off 13 to Aeshvarya**, `README.md` and `bench/README.md`: the field-level McNemar treats the 266 fields as independent, and they are not. Of the 36 fields only the probe gets right, 22 come from one design choice (two pipelines log their id to stderr, repeated over 11 cases each) and 12 from the overwritten operator. Add the case level (the probe is fully right on 50 of 54 cases, the static check on 26; exact McNemar on cases, p = 1.9e-05), and say under "What this does and does not show" that the p-values describe these generated cases and that two mechanisms produce most of the gap. The result stands either way; a judge who checks should find that we said it first.

### 2026-10-09 (d)
- **A13 offline** (Aeshvarya, `bench/`): 54 generated pipelines, 266 declared fields, 49 planted defects. The probe finds 48 with 3 false alarms; a static check of whether each field is named in the code finds 35 with 22; paired, p = 1.9e-07 (exact McNemar). The probe's errors are the two limit cases built to find them and one cascade, all listed. A test pins the cases and the probe's calls. The Nemotron-reads-the-code baseline (`bench/run.py --llm`) runs once there is a key.
- **A14 done** (Aeshvarya): `action.yml` with a Markdown job summary (`probe --markdown`), run on this repository in CI.
- **Hand-offs 10 to 12 done** (Aeshvarya): crashes exit 2, never 1; the action installs the sandbox extra and the README shows the keys from secrets; A8 marked done.
- Next for Aeshvarya: own Nebius credits, then the live A3 run and `bench/run.py --llm`; A6 host.

### 2026-10-09 (c)
- **V6's audit is one command** (Varunika, `varunika/v6-audit`): `python3 scripts/audit.py` reads every version of every file on every branch, every committed path, commit messages, identities and branch names, for key shapes, `.env` and key files, addresses that are not ours, and trailers, and ends with go or no-go. `--also WORD` checks a name that must not go public without committing it. Go on all 189 commits; 149 tests pass.
- **Reviewed Aeshvarya's 10-08 and 10-09 work** (A7, A14, `--explain`, `--intent`, hand-off 9, the `contree auth` correction): no secrets or traces, 139 tests pass on `main`. A13's branch seen, not reviewed: still in progress.
- **Hand-offs to Aeshvarya**, in his files:
  10. `cli.py`: a crash exits 1, the same code as "defects found". A missing target file and a target without `command` both do, with a traceback. So `probe-gate` and the clean-clone job (`test $? -eq 1`) pass on a crash, and any CI gating on the exit code reads a crash as a defect. In `main()`, after `except RuntimeError`, catch the rest: print the traceback, return 2.
  11. `action.yml`: the `args` input's own example is `--backend sandbox --nano`, but the install step skips the sandbox extra, so that example exits 2 asking for `pip install -e '.[sandbox]'`, which an action user cannot run. Install `"$ACTION_PATH[sandbox]"`, and show the keys as `env:` from secrets in the README's "In CI" block.
  12. Board: A8 still says todo; the 2026-10-09 (b) Log says done.

### 2026-10-09 (b)
- **Claimed, two new tasks (Aeshvarya), in new paths only:** A13, a benchmark of pipelines with planted input-handling bugs, reporting exact detection counts for Loadbearing and two baselines (a static check of whether each field is referenced, and Nemotron reading the code); A14, a GitHub Action that runs a probe and writes a job summary.
- A8 done; the notes are kept outside the repo.
- All nine hand-offs are on `main`: `--explain`, `--intent`, and the demo target leaves `passages` undeclared, with NVIDIA's RAG 101 post as its doc.

### 2026-10-09
- **Correction (Aeshvarya):** the 10-06 (g) entry says there is no `contree auth`. There is, in `contree-cli` (`uv tool install contree-cli`); it saves a profile `ContreeSync()` reads. V1 can use it or the two `.env` variables. The backend is unchanged. The CLI reads `NEBIUS_AI_PROJECT`, the SDK `NEBIUS_PROJECT_ID`; the docs' SDK page also shows a `ContreeAsyncClient(...)` constructor that 0.3.6 does not take. Both go in the feedback files.

### 2026-10-07 (e)
- **A4 loop and A5 schema 2 merged** (Aeshvarya, `c03d3cf`): `close_loop()`, `--fix` and `--prove` on one pinned checkpoint, report schema 2. **A3 built and proven offline** (Aeshvarya, `213554d`): `examples/support_answerer`, the RAG answerer with a `docs` block. 127 tests pass. Checked: every malformed Ultra reply in `write_fix` raises `ValueError`, which `close_loop` catches.
- **Hand-off 9 to Aeshvarya, proposed:** the demo target declares all five fields, so `infer_expects` finds no undeclared field and Tavily never runs on it. Leave `passages` out of `expects` (keep `question` relevant and the three ids irrelevant). Then `--intent` has real work: the RAG docs say answers must be grounded in the retrieved passages, Super quotes that with its link, and the silent passthrough on `passages` becomes a defect only Tavily could have claimed. The $3,000 Tavily prize needs exactly that runtime job (WORKPLAN, V4 "Why").

### 2026-10-07 (d)
- **Follow-ups 2 to 4 merged** (Aeshvarya, `052394e`): `--baseline-runs` reaches the probe, the CLI warns only on a void report and otherwise names the unstable keys, and run counts use `baseline_runs`. 114 tests pass on `main`.
- **SPEC.md matches the code** (Varunika, merge `080880a`): Super states each defect while a fixed rule decides it, inferred intents carry a checked quote, a fix passes three checks before a fork runs it, and a report is void only when nothing stable is left.
- **V6 dry run, history clean** (Varunika): all 124 commits on every branch scanned for key patterns, tracked `.env` files, stray emails, trailers, and employer or tool names; nothing found. The one secret-shaped string is a made-up test value. The final audit still runs on 2026-10-18.

### 2026-10-07 (c)
- **V7 drafted** (Varunika, merge `f99f265`): `docs/prior-art.md` (metamorphic testing, leave-one-feature-out with Sculley et al.'s own sentence quoted, input erasure, global sensitivity analysis, Lost in the Middle; how Loadbearing differs from each, including that it does not measure interactions between inputs) and a five-line README section. Three documented failures for Potential Impact: Air Canada's chatbot (*Moffatt v. Air Canada*, 2024 BCCRT 149), New York City's MyCity chatbot (The Markup, 2024-03-29), and Public Health England's missed cases (October 2020). Every source was opened before citing; one figure was corrected to what its source says (nearly 16,000, not 15,841).
- With V7, every task of Varunika's that can be done without her keys, voice or drawing is done. What remains needs her: V1 live run (unblocks the live halves of V2, V4 and V5), V9 palette, V10 outline, then V6, V8, V11, V12.

### 2026-10-07 (b)
- **V2 offline half done** (Varunika, merge `5287f6c`): reasoning traces stripped in every form (a complete block, a trace whose opening tag the template supplied, one cut off); `tests/fixtures/diffs.json`, 20 labelled diffs (10 meaningful, 10 noise); `scripts/eval_nano.py` scores Nano against them and fails below 18/20; `probe(..., explain_with=router)` gives each defect, and only defects, Super's statement and Ultra's account of the code path. The Nano score itself waits on V1's keys.
- **V4 done offline** (Varunika, merge `991e29b`): `tavily.extract` for `docs.urls` and whole pages from search; `NemotronRouter.infer_intent` (Super); `intent.infer_expects(target, router)`, which drops any answer whose quote is not really in the excerpt it cites and caches docs and intents under `runs/`; `probe(..., inferred=...)` judges undeclared fields by inferred intent, marked `inferred` with the evidence. On the toy target with `submitted_at` undeclared, the spec sentence turns it from an observation into a cited phantom sensitivity. 111 tests pass.
- **Hand-offs to Aeshvarya**, in addition to the five above:
  6. `--explain`: `probe(..., explain_with=NemotronRouter.from_env(tiers=("super", "ultra")))`.
  7. `--intent`: `inferred = infer_expects(target, NemotronRouter.from_env(tiers=("super",)))`, then `probe(..., inferred=inferred)`. Cache lands in `runs/`, same as the demo server's.
  8. A3: give the RAG target a `docs` block (a query, and URLs if there is a canonical page) so V4 runs live on it.

### 2026-10-07
- **V5 writer done offline** (Varunika, merge `51b0ef5`): `NemotronRouter.write_fix` (Ultra returns whole new file contents and a rationale) and `fix.write_fix`, which refuses any fix that touches a file outside `sources`, no longer compiles, changes nothing, or rewrites more than half a file. The C5 fields are on `FieldVerdict` (`intent_source`, `evidence`, `reconciliation`, `explanation`), and `tests/fakes.py` gives both sides an offline Token Factory client and router. An offline loop test probes the toy target, has a fake Ultra fix `body`, and runs `prove()`: `body` becomes load-bearing, the outage ticket comes out P1, no new defect. Live Ultra check waits on V1.
- **V3 noise floor done** (Varunika, merge `e21d43e`): the unmutated record runs `baseline_runs` times alongside the forks; keys that differ between those runs are left out of every comparison; `Report.unstable_keys`, `Report.baseline_runs` and `Report.void` exist; `probe(..., baseline_runs=N)` overrides the target. The toy target is unchanged. 84 tests pass.
- **Hand-offs to Aeshvarya**, all in his files:
  1. `--fix` and `--prove`: the writer is ready. `write_fix(verdict, target, NemotronRouter.from_env(tiers=("ultra",)))` per defect, then `prove()`.
  2. `--baseline-runs`: pass it as `probe(..., baseline_runs=args.baseline_runs)`.
  3. `cli.render`: the "baseline disagrees with itself, so no verdict below is sound" warning should key on `report.void`, not `not report.deterministic`, and list `report.unstable_keys` when there are any. Today it would wrongly void an LLM target's whole report.
  4. Run counts: `timing_line` and `report.py` count runs as `len(report.forks) + 2`; with the noise floor that is `+ report.baseline_runs`.
  5. Schema 2 (A5): `baseline_runs`, `unstable_keys` and the four new verdict fields are on the dataclasses now.
- **A3 pick made the same evening:** the RAG answerer, with the weather agent as fallback. Aeshvarya can build it now.

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
