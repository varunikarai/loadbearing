# Found by Loadbearing

[`realworld/`](../realworld/) replays bugs that were already public. The bugs here were not:
Loadbearing found them by probing the current release of a library, and each one is checked
against the last release without it.

## DSPy: nested output descriptions never reach the model

| | |
|---|---|
| Library | [DSPy](https://github.com/stanfordnlp/dspy), `XMLAdapter` |
| Release with the bug | `dspy` 3.4.1, the current release on 2026-10-26. Also 3.3.1, 3.4.0, and `main` at the time of writing |
| Last release without it | `dspy` 3.3.0 |
| Pair | `dspy-xml-descriptions-3.4.1` / `dspy-xml-descriptions-3.3.0` |
| Found | 2026-10-26 |
| Upstream | No issue for it existed when we searched on 2026-10-26 |

A pipeline asks a model for a structured return policy, a Pydantic model with two fields, and
describes each field: the window in days "exactly as the passages state it. Never assume a
common default such as 30", and whether this customer can still get a refund. With
`XMLAdapter`, dspy 3.3.1 and later describe a nested output to the model as bare tags:

```
<policy>
<days>
...
</days>
<refundable>
...
</refundable>
</policy>
```

The model's docstring, every field description inside it, and constraints such as a
`Literal`'s allowed values are not sent. Nothing throws. In 3.3.0, the same signature sent the
output's full JSON schema, descriptions included, as `ChatAdapter` and `JSONAdapter` still do.

**Where it comes from.** Nested XML output arrived in dspy 3.3.1 (stanfordnlp/dspy#10239).
For a nested output field, `XMLAdapter.format_field_structure` and
`user_message_output_requirements` render the structure with `_xml_schema`, which walks the
JSON schema's `properties` and keeps only their names. Before that, the field went through
`translate_field_type`, which includes the schema. The rewrite in #10402 keeps the same
skeleton.

**What Loadbearing reports.** The model is DSPy's own `DummyLM`, which records what it was
sent, so what the model was told is the pipeline's output and no key is needed. On 3.4.1:

```
field                   intent      destroy  drop   nudge  verdict
request_id              irrelevant  same     same   same   inert
question                relevant    moved    moved  moved  load-bearing
passages                relevant    moved    moved  moved  load-bearing
policy_description      relevant    same     same   same   SILENT PASSTHROUGH
days_description        relevant    same     same   same   SILENT PASSTHROUGH
refundable_description  relevant    same     same   same   SILENT PASSTHROUGH

3 defect(s): policy_description (silent passthrough), days_description (silent passthrough), refundable_description (silent passthrough)
```

On 3.3.0, the same pipeline and input: every field `load-bearing`, no defects. Both tables
come from a local discovery run (the same pipeline and request, with the release installed
beside it); the targets themselves install their release in the checkpoint and run on Nebius
Sandboxes:

```bash
loadbearing probe found/dspy-xml-descriptions-3.4.1/target.json --backend sandbox
loadbearing probe found/dspy-xml-descriptions-3.3.0/target.json --backend sandbox
```
