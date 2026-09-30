# Loadbearing: the spec

The statement both builders work against. If a feature does not serve this, it does not ship.

## Problem

Agent and data pipelines fail silently. They produce confident, well-formed, correctly-typed output over inputs they are not actually reading. Nothing throws. Tests pass. The answer is fiction, catchable only by a human who happens to look at the right field.

## The question nobody can answer today

Which of my inputs is this system genuinely load-bearing on?

## How Loadbearing answers it

Empirically. Checkpoint the pipeline once, fork that checkpoint per mutation, run the forks in parallel holding everything else identical. Report two defect classes:

| Defect | Meaning |
|---|---|
| **Silent passthrough** | The output did not move when an input was destroyed. The pipeline claims to use a field it never reads. |
| **Phantom sensitivity** | The output moved when an irrelevant input was nudged. The pipeline reacts to something that should not matter. |

## The claim we defend

For any pipeline, we tell you which inputs actually change its behaviour, and we prove it by running it, not by reading it.

## Why each piece of the stack is there

| Piece | Job | Why it is load-bearing, not decoration |
|---|---|---|
| Nebius Token Factory Sandboxes | Checkpoint once, fork per mutation | The comparison is only sound if every fork starts from a byte-identical environment. Checkpoint-and-fork makes "hold everything constant except one input" a primitive instead of N rebuilds. |
| Nemotron Nano | Classify each fork's diff | One cheap call per fork: is this change meaningful or noise? |
| Nemotron Super | Reconcile across forks | Turns many per-fork diffs into one defect class per input. |
| Nemotron Ultra | Explain the defect | Long-horizon reasoning over the pipeline source: why does this path not read the field? |
| Tavily | Fetch intended behaviour | Pulls the upstream spec or docs, which is what makes phantom sensitivity a finding rather than a guess. |

## Scope for the vertical slice

One checkpoint, N forks from it, one mutation per fork, one Nano call classifying each diff, one printed verdict. On a toy pipeline. Nothing more.
