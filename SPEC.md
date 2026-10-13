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

Then close the loop. Ultra writes the smallest fix for each defect, the fix is applied in a fresh fork of the same checkpoint, and the probe re-runs on that fork to show the defect gone. **Find, explain, fix, prove**, with the same checkpoint primitive at every step.

Ultra writes a fix as exact edits: each quotes text that must appear once in its file, and every line it does not quote stays byte for byte. A fix is checked before any fork runs it: it may change only the pipeline's own source files, a Python file must still compile, and it may not remove or replace more than half of a file's lines (three, in a file shorter than six). A fix that fails a check is rejected, not applied.

## The claim we defend

For any pipeline, we tell you which inputs actually change its behaviour, and we prove it by running it, not by reading it.

## Why each piece of the stack is there

| Piece | Job | Why it is load-bearing, not decoration |
|---|---|---|
| Nebius Token Factory Sandboxes | Checkpoint once, fork per mutation, fork again to prove a fix | The comparison is only sound if every fork starts from a byte-identical environment. Checkpoint-and-fork makes "hold everything constant except one input" a primitive instead of N rebuilds, and the same primitive makes "this fix removed the defect, and nothing else changed" provable. |
| Nemotron Nano | Classify each fork's diff | One cheap call per fork: is this change meaningful or noise? |
| Nemotron Super | Reconcile across forks | States, for each defect, what its destroy, drop and nudge forks show together. The defect class itself comes from a fixed rule over the forks, never from a model, so no model can invent a defect. |
| Nemotron Ultra | Explain the defect and write the fix | Long-horizon reasoning over the pipeline source: why does this path not read the field, and what is the smallest change that makes it? |
| Tavily | Infer which fields should matter | Pulls the pipeline's own docs (`docs.urls`) and searches for more (`docs.query`). Super fills in `expects` for fields nobody declared from the pipeline's own pages first, and from the search results only where those pages say nothing, so an undeclared field can carry a defect claim. Each inferred intent carries a verbatim quote and its link, and a quote that is not in the page it cites is thrown away. That is what makes phantom sensitivity a finding rather than a guess. |

## LLM pipelines

The demo target is an LLM pipeline, because that is where silent passthrough does the most damage: a retrieval or tool-calling step that answers fluently while ignoring what it retrieved. An LLM's output varies on its own, so a two-run determinism check would void every verdict. Instead the baseline runs k times, and output keys that vary with no mutation at all are marked **unstable** and left out of verdicts. Everything else is still judged. Only when nothing stable is left (every key varies, the exit code varies, or the output is not JSON and varies) is the report void, and it says so instead of judging.

## Scope for the vertical slice

One checkpoint, N forks from it, one mutation per fork, one Nano call classifying each diff, one printed verdict. On a toy pipeline. Nothing more.
