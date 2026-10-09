# Recorded runs for the hosted demo

Runs that cost credits (on Nebius Sandboxes, or with Nemotron calls) are recorded
once and served from here, so a visitor sees the real run without spending
anything. The Dockerfile copies this folder into the server's cache.

Record one by probing with `--out` into this folder, named
`<target>.<backend>.json`, for example:

```bash
loadbearing probe examples/support_answerer/target.json --backend sandbox --intent --prove \
  --out demo/runs/support_answerer.sandbox.json
```

Never record a run made with keys in the record itself. Reports hold inputs and
outputs, not the environment, but check before committing.
