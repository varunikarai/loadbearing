# Recorded runs for the hosted demo

Runs that cost credits (on Nebius Sandboxes, or with Nemotron calls) are recorded
once and served from here, so a visitor sees the real run without spending
anything. The Dockerfile copies this folder into the server's cache, and the Vercel
function (`api/index.py`) copies it into `/tmp`.

Record one by probing with `--out` into this folder, named
`<target>.<backend>.json`, for example:

```bash
loadbearing probe examples/support_answerer/target.json --backend sandbox --intent --prove \
  --out demo/runs/support_answerer.sandbox.json
```

Never record a run made with keys in the record itself. Reports hold inputs and
outputs, not the environment, but check before committing.

## Hosting it

Either host serves the same pages as `loadbearing serve --readonly`: the free targets
run on request, anything that needs keys shows its recorded run, and no key is ever
set on the host.

- **Vercel:** Add New > Project, import the repository, Deploy. `vercel.json` routes
  every path to `api/index.py`, a WSGI function, and bundles the targets and
  recordings with it. Nothing to configure.
- **Render, or any container host:** New > Blueprint, pick the repository.
  `render.yaml` builds the Dockerfile; the free plan sleeps when idle, so set the
  repository variable `DEMO_URL` and `.github/workflows/keep-warm.yml` pings it.
