# Benchmark: does running a pipeline find what reading it misses?

54 small pipelines, 266 declared input fields, 49 planted defects. Each detector
gets the same source code and the same declared intent (which fields should
change the output, which should not), and calls every field a silent
passthrough, a phantom sensitivity, or neither. Results: [RESULTS.md](RESULTS.md).

```bash
python3 bench/generate.py                    # rebuild bench/cases/ (deterministic)
PYTHONPATH=src python3 bench/run.py          # Loadbearing and the static check, offline, ~4 s
PYTHONPATH=src python3 bench/run.py --llm    # also Nemotron reading the code (needs .env keys)
```

## The cases

Four pipelines, each correct as written: support-ticket triage, a loan
pre-screen, a shipping quote, and moderation routing ([domains.py](domains.py)).
Each case is one of them with at most one bug planted by a source edit
([generate.py](generate.py)):

| Operator | Defect it plants | Cases |
|---|---|---|
| typo | a relevant field read under a misspelled key (`bdoy`) | 12 |
| stale key | a relevant field read under the name it had before an upstream rename | 12 |
| overwritten | a relevant field read, then replaced by a default before use | 12 |
| timestamp leak | the arrival second decides a routing queue | 4 |
| id bucketing | a hash of the request id picks a variant | 4 |
| id echoed | the request id is copied into the output | 4 |
| clean | none | 4 |
| threshold-only field | none: correct code that uses a field only past a threshold | 1 |
| value-specific leak | an id changes the output only when it starts with `TEST-` | 1 |

Two of the four pipelines log the request id to stderr, as real services do.
That is harmless (Loadbearing ignores stderr) and is part of what a static check
has to cope with.

The last two rows are there to find Loadbearing's limits, and it fails both: a
field used only through a threshold looks unread when no mutation of this
record's value crosses it, and a leak that needs a specific value is not
triggered by destroying, dropping or nudging. Both are reported as errors below,
not removed.

## Detectors

- **Loadbearing:** the probe, on the local backend, unchanged from the CLI.
- **Static name check:** the check a reviewer might script. A relevant field whose
  name never appears in the code is a silent passthrough; an irrelevant field
  whose name appears anywhere is a phantom sensitivity. Naive on purpose: it is
  the floor, not the competition.
- **Nemotron reads the code** (`--llm`): the source and the declared intent go to
  Nemotron Super, which lists the defects it sees. This is the baseline that
  matters. Its numbers appear in RESULTS.md once it has been run with a key.

## Scoring

One unit is one declared field in one case. A call is right only when it
matches the truth exactly; the wrong defect class counts as a false alarm and a
miss. Detectors are compared pairwise with an exact McNemar test on the units
where exactly one of them is right.

## What this does and does not show

- **The bugs are synthetic, and we wrote both them and Loadbearing.** The
  operators are common real patterns, but this measures what each kind of
  detector can see, not how often these bugs occur in the wild.
- **One record per case.** Loadbearing's verdicts are about the record it ran;
  a different record can make a threshold-only field visible.
- **Cascades are scored as false alarms.** In the loan pipeline, once income is
  never read the ratio is pinned, so the requested amount genuinely cannot change
  the output either. Loadbearing says so, which is true of the program as given,
  but only one defect was planted, so it counts against Loadbearing. Fixing the
  income read clears both.
- **No interactions.** Each mutation changes one field; a defect that needs two
  fields to change together is not tested here or by the probe.
