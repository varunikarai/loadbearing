# Loadbearing

Find out which inputs a pipeline is actually load-bearing on, by running it.

Loadbearing checkpoints a pipeline once in a Nebius Token Factory Sandbox, forks that checkpoint once per input mutation, runs every fork in parallel from the same snapshot, and reports two defect classes:

- **Silent passthrough**: an input that should matter was destroyed, and the output did not move.
- **Phantom sensitivity**: an input that should not matter was nudged, and the output moved.

The problem statement is in [SPEC.md](SPEC.md).

## Status

Built and tested offline unless it says live. Nothing has run against a live Nebius account yet.

- [x] Mutation engine: destroy (template-replace), drop, nudge
- [x] Checkpoint-and-fork engine, timed: checkpoint, parallel wall time, and the same runs one after another
- [x] Verdicts: silent passthrough and phantom sensitivity
- [x] Noise floor: the baseline runs `baseline_runs` times, and keys that vary on their own are set aside
- [x] Close the loop: Ultra writes the fix, validated before use; a fresh fork of the same checkpoint proves it
- [x] An LLM demo target: a support answerer over retrieved policy, with a planted rename bug
- [x] Report schema 2 and a self-contained HTML report: the fork tree, the evidence, the proven fix
- [x] Demo server with cached runs and a read-only mode; Dockerfile; CI with a probe gate and a clean-clone check
- [x] Secrets reach forks only, never a checkpoint
- [x] Prior art: metamorphic testing, leave-one-feature-out, input erasure
- [x] Benchmark: 54 pipelines with planted bugs; the probe finds 48 of 49, a static check 35 ([bench/](bench/))
- [x] GitHub Action with a job summary
- [ ] Sandboxes backend run against a live account (checked against the contree-sdk 0.3.6 source, not yet run)
- [ ] Nemotron Nano, Super and Ultra verified live with real model IDs
- [ ] Tavily inferring which fields should matter, from upstream docs
- [ ] Hosted demo deployed at a public URL
- [ ] Demo video

## Quickstart

Python 3.10 or later. The core has no dependencies.

```bash
git clone https://github.com/varunikarai/loadbearing.git
cd loadbearing
PYTHONPATH=src python3 -m loadbearing probe examples/ticket_triage/target.json
```

```
ticket-triage: 15 forks from one checkpoint (local)
checkpoint 0.01s, then 17 runs in 0.07s wall (0.46s one after another, 6.5x parallel)

field          intent      destroy  drop   nudge  verdict
ticket_id      irrelevant  same     same   same   inert
submitted_at   irrelevant  moved    moved  moved  PHANTOM SENSITIVITY
customer_tier  relevant    moved    moved  moved  load-bearing
subject        relevant    moved    moved  moved  load-bearing
body           relevant    same     same   same   SILENT PASSTHROUGH

2 defect(s): submitted_at (phantom sensitivity), body (silent passthrough)
```

The ticket body reports a full outage, and the pipeline still says P3, because it reads the body under a misspelled key. Nothing throws and the output is well-formed. The exit code is 1 whenever a defect is found, so a probe can gate CI.

### On Nebius Sandboxes

```bash
pip install -e '.[sandbox]'
cp .env.example .env        # set NEBIUS_API_KEY and NEBIUS_PROJECT_ID, or run `contree auth` once
loadbearing probe examples/ticket_triage/target.json --backend sandbox
```

### With Nemotron judging each diff

```bash
cp .env.example .env        # set NEBIUS_API_KEY
loadbearing models          # prints the Nemotron IDs your key can call; paste them into .env
loadbearing probe examples/ticket_triage/target.json --nano
```

### Find, fix, prove

```bash
loadbearing probe examples/ticket_triage/target.json --fix     # Ultra writes a fix per defect
loadbearing probe examples/ticket_triage/target.json --prove   # ...and a fresh fork proves each one
```

With `--prove`, the probe and every proof share one checkpoint, so a fix is the only thing that
differs. Each proof says whether the defect is gone and whether any other field gained one. A
fix is refused before it runs if it touches a file outside the target's `sources`, no longer
compiles, changes nothing, or rewrites most of a file. The exit code still reflects the pipeline
as given. `--baseline-runs N` overrides the target's noise floor.

### The LLM demo target

```bash
loadbearing probe examples/support_answerer/target.json --intent --prove
# needs NEBIUS_API_KEY, NEMOTRON_NANO_MODEL, NEMOTRON_SUPER_MODEL, NEMOTRON_ULTRA_MODEL, TAVILY_API_KEY
```

A support answerer over retrieved policy text. The retriever writes `passages`, the prompt reads
`context`, so a customer 20 days into a 14-day return window is told they have 30 days for a full
refund. Its target leaves `passages` undeclared on purpose: without `--intent` the probe only
observes that the answer never moves when the passages are destroyed. With `--intent`, Tavily
reads NVIDIA's own RAG guides, Super quotes the line saying the model answers from the retrieved
data, and that observation becomes a cited silent passthrough. The proven fix makes the answer 14
days and a warranty repair.

## In CI

```yaml
- uses: actions/checkout@v4
- uses: varunikarai/loadbearing@main
  with:
    target: path/to/target.json      # args: "--baseline-runs 5" for an LLM pipeline
```

The job fails when a probe finds a defect, and the run page shows the verdict table, each
defect, and any proven fix as a job summary. `fail-on-defects: "false"` reports without
failing; the `defects` output carries the count.

On Nebius, with Nemotron judging each diff, pass the keys from repository secrets:

```yaml
- uses: varunikarai/loadbearing@main
  with:
    target: path/to/target.json
    args: --backend sandbox --nano
  env:
    NEBIUS_API_KEY: ${{ secrets.NEBIUS_API_KEY }}
    NEBIUS_PROJECT_ID: ${{ secrets.NEBIUS_PROJECT_ID }}
    NEMOTRON_NANO_MODEL: ${{ vars.NEMOTRON_NANO_MODEL }}
```

## The report

```bash
loadbearing probe examples/ticket_triage/target.json --out report.json --html report.html
loadbearing report report.json            # re-render a saved run without re-running it
```

`report.html` is one self-contained page: the checkpoint fanning out to every fork, the
field-by-mutation matrix, and, for each defect, the baseline and fork outputs side by side
with the changed keys marked. It fetches nothing, so a saved copy always opens.

## The demo server

```bash
loadbearing serve                          # http://127.0.0.1:8000
loadbearing serve --backend sandbox --nano # runs on Nebius, Nano judging each diff
loadbearing serve --readonly               # serve recorded runs only, never run
```

It lists every `examples/<name>/target.json`, runs a probe on one when asked, and caches the
result in `runs/`, so a page view never costs a run. `--readonly` refuses new runs, which is
how a public deployment keeps Sandboxes credits intact. The Dockerfile runs it on any
container host that sets `$PORT`.

## Writing a target

A target is a JSON file next to the pipeline it describes.

| Field | Meaning |
|---|---|
| `name` | Label for the report |
| `image` | OCI image the sandbox starts from |
| `setup` | Runs once, before the checkpoint is taken |
| `files` | Copied into the checkpoint |
| `command` | Runs in every fork. The fork's record is at `input.json` |
| `record` | The baseline input |
| `expects.relevant` | Fields that should change the output. Never moving is a silent passthrough |
| `expects.irrelevant` | Fields that should not. Moving is a phantom sensitivity |
| `timeout` | Seconds a single run may take. Default 60 |
| `baseline_runs` | How often the unmutated record runs, for the noise floor. 2 or more, default 2 |
| `env` | Variable names passed from the host to baseline and fork runs only, never to setup |
| `docs` | `{"query": ..., "urls": [...]}`: where Tavily looks for what the pipeline should read |
| `sources` | Files a fix may rewrite. Default: `files` |

Undeclared fields are still probed and reported, but never flagged as defects. Every key after
`expects` is optional, so a target written for the first version still loads unchanged.

## How it uses Nebius and NVIDIA

| Piece | Job |
|---|---|
| Token Factory Sandboxes | The setup run with `disposable=False` is the checkpoint. Every fork is a run from that snapshot with one mutated input, so the only thing that differs between forks is the input. |
| Nemotron Nano | One call per moved fork: is the change meaningful, or noise? |
| Nemotron Super | Reconciles every fork on a field into one defect statement |
| Nemotron Ultra | Reads the pipeline source and explains why a path does or does not read the field |
| Tavily | Fetches upstream docs that establish what a pipeline is supposed to read |

## Layout

```
src/loadbearing/
  mutations.py       one mutation, one field: destroy, drop, nudge
  probe.py           checkpoint once, fork per mutation in parallel, compare, judge
  compare.py         did the output move, and which keys
  verdict.py         silent passthrough, phantom sensitivity
  noise.py           the noise floor: keys that vary with no mutation
  target.py          target file loader
  backends/local.py  directory snapshot, for development with no account
  backends/contree.py  Nebius Token Factory Sandboxes
  nemotron.py        Token Factory client, Nano / Super / Ultra routing
  tavily.py          Tavily search client
  fix.py             a fix, and the checks it passes before any fork applies it
  prove.py           re-probe a fix from the same checkpoint; the whole loop
  report.py          the versioned JSON report
  html_report.py     the self-contained HTML report and fork tree
  markdown_report.py the Markdown summary for CI job summaries
  serve.py           the demo server
  cli.py             loadbearing probe | report | serve | models
examples/ticket_triage/     toy pipeline with two planted bugs
examples/support_answerer/  LLM pipeline on Nemotron that ignores what it retrieved
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Every test runs offline, with no key. Nemotron and Token Factory are replaced by fakes, including
a fake Token Factory server that the LLM demo target talks to over HTTP, unmodified.

## Benchmark

54 small pipelines with planted input-handling bugs, scored field by field:

| detector | found | missed | false alarms |
|---|---|---|---|
| Loadbearing (runs it) | 48 | 1 | 3 |
| Static name check (reads it) | 35 | 14 | 22 |

Exact McNemar test on paired calls: p = 1.9e-07. The misses and false alarms are listed case by
case, and include two cases built to find the probe's limits. Nemotron reading the code is the
next baseline. How the cases are built and what this does not show: [bench/README.md](bench/README.md).

## Prior art

- **Metamorphic testing** (Chen, Cheung and Yiu, 1998) checks relations between runs on transformed inputs; Loadbearing's relations are per field and come from intent.
- **Leave-one-feature-out** (Sculley et al., NeurIPS 2015) finds inputs a model barely uses; Loadbearing applies the idea to any running pipeline and also flags the input it should use but silently does not.
- **Input erasure** and **sensitivity analysis** measure what an input changes; Loadbearing adds a defect claim per field, a noise floor for LLM output, and a fix proven from the same checkpoint.
- **"Lost in the Middle"** (Liu et al., TACL 2024) shows why a retrieval pipeline can answer without using what it retrieved.

Sources, differences in full, and documented real failures: [docs/prior-art.md](docs/prior-art.md).

## License

[Apache 2.0](LICENSE)
