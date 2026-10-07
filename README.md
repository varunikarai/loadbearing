# Loadbearing

Find out which inputs a pipeline is actually load-bearing on, by running it.

Loadbearing checkpoints a pipeline once in a Nebius Token Factory Sandbox, forks that checkpoint once per input mutation, runs every fork in parallel from the same snapshot, and reports two defect classes:

- **Silent passthrough**: an input that should matter was destroyed, and the output did not move.
- **Phantom sensitivity**: an input that should not matter was nudged, and the output moved.

The problem statement is in [SPEC.md](SPEC.md).

## Status

- [x] Mutation engine: destroy (template-replace), drop, nudge
- [x] Checkpoint-and-fork engine, with the baseline run twice to prove it is deterministic
- [x] Verdicts: silent passthrough and phantom sensitivity
- [x] Local backend, and a toy target with two planted bugs, both caught end to end
- [ ] Sandboxes backend run against a live account (written against the documented SDK, not yet exercised)
- [ ] Nemotron Nano diff classification verified with real model IDs
- [ ] Super reconciliation and Ultra explanation in the report
- [ ] Tavily inferring which fields should matter, from upstream docs
- [ ] Noise floor: a k-run baseline marks keys that vary on their own as unstable
- [ ] Close the loop: Ultra writes the fix, a fresh fork of the same checkpoint proves the defect gone
- [ ] An LLM pipeline on Nemotron as the demo target
- [ ] Prior art: metamorphic testing and input ablation
- [x] Timing: checkpoint, parallel wall time, and the same runs summed one after another
- [x] Versioned JSON report, and a self-contained HTML report built around the fork tree
- [x] Demo server with cached runs and a read-only mode; Dockerfile; CI with a probe gate
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
cp .env.example .env        # set NEBIUS_API_KEY and NEBIUS_PROJECT_ID
loadbearing probe examples/ticket_triage/target.json --backend sandbox
```

### With Nemotron judging each diff

```bash
cp .env.example .env        # set NEBIUS_API_KEY
loadbearing models          # prints the Nemotron IDs your key can call; paste them into .env
loadbearing probe examples/ticket_triage/target.json --nano
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

Undeclared fields are still probed and reported, but never flagged as defects.

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
  target.py          target file loader
  backends/local.py  directory snapshot, for development with no account
  backends/contree.py  Nebius Token Factory Sandboxes
  nemotron.py        Token Factory client, Nano / Super / Ultra routing
  tavily.py          Tavily search client
  report.py          the versioned JSON report
  html_report.py     the self-contained HTML report and fork tree
  serve.py           the demo server
  cli.py             loadbearing probe | report | serve | models
examples/ticket_triage/  toy pipeline with two planted bugs
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Prior art

- **Metamorphic testing** (Chen, Cheung and Yiu, 1998) checks relations between runs on transformed inputs; Loadbearing's relations are per field and come from intent.
- **Leave-one-feature-out** (Sculley et al., NeurIPS 2015) finds inputs a model barely uses; Loadbearing applies the idea to any running pipeline and also flags the input it should use but silently does not.
- **Input erasure** and **sensitivity analysis** measure what an input changes; Loadbearing adds a defect claim per field, a noise floor for LLM output, and a fix proven from the same checkpoint.
- **"Lost in the Middle"** (Liu et al., TACL 2024) shows why a retrieval pipeline can answer without using what it retrieved.

Sources, differences in full, and documented real failures: [docs/prior-art.md](docs/prior-art.md).

## License

[Apache 2.0](LICENSE)
