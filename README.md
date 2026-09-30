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
- [ ] Tavily call establishing intended behaviour from upstream docs
- [ ] Hosted demo
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
contree auth
loadbearing probe examples/ticket_triage/target.json --backend sandbox
```

### With Nemotron judging each diff

```bash
cp .env.example .env        # set NEBIUS_API_KEY
loadbearing models          # prints the Nemotron IDs your key can call; paste them into .env
loadbearing probe examples/ticket_triage/target.json --nano
```

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
  cli.py             loadbearing probe | models
examples/ticket_triage/  toy pipeline with two planted bugs
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## License

[Apache 2.0](LICENSE)
