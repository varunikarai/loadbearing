# Real bugs, from public issues

Each folder is one release of an open-source AI library, pinned in the target's setup, with a
few lines of calling code that pass a request's fields to the library the way a pipeline would.
Every bug here was reported in public and fixed upstream; each comes as a pair, the last
release with the bug and the first with the fix. `cases.json` says what each one is.

| Pair | Issue | Fix |
|---|---|---|
| `haystack-split-overlap-2.30.2` / `-2.31.0` | [deepset-ai/haystack#11767](https://github.com/deepset-ai/haystack/issues/11767) | [#11768](https://github.com/deepset-ai/haystack/pull/11768) |
| `haystack-answer-meta-2.7.0` / `-2.8.0` | [deepset-ai/haystack#8542](https://github.com/deepset-ai/haystack/issues/8542) | [#8544](https://github.com/deepset-ai/haystack/pull/8544) |
| `pydantic-ai-description-2.5.0` / `-2.5.1` | [pydantic/pydantic-ai#6262](https://github.com/pydantic/pydantic-ai/issues/6262) | [#6265](https://github.com/pydantic/pydantic-ai/pull/6265) |

The setups install packages, so these targets set `needs_sandbox` and run on Nebius Sandboxes
only; the local backend refuses them rather than install into the host's Python:

```bash
loadbearing probe realworld/haystack-split-overlap-2.30.2/target.json --backend sandbox
```

The recorded runs are in `demo/runs/`, and the hosted demo shows them. The pydantic-ai pair
uses pydantic-ai's own `FunctionModel`, which reports what the agent sent the model, so no API
key is needed: what the model was told is the output.

The Haystack overlap bug was checked on more releases than the pair: present in 2.12.0, 2.16.0,
2.20.0, 2.24.0, 2.28.0 and 2.30.2, absent in 2.10.0, 2.10.3, 2.11.0 and 2.11.2 (on the same
input), and fixed in 2.31.0.
