---
type: Template
title: Attested Computation template
description: A sanctioned computation, copied from its approved source.
status: draft
generated: { by: "claude-code/<model-id>", at: "<YYYY-MM-DDTHH:MM:SSZ>" }
---

Skeleton for `type: Attested Computation` concepts. Copy the fence below
into a new file's frontmatter, then fill the body headings. Resolve
every `<placeholder>` or delete its line.

Use this type only when a sanctioned computation exists: an approved SQL
file, a dbt model, or a query from its owner. Copy it verbatim into the
single fenced block under `# Computation` — never write or edit it — and
cite it in `sources`. Without one, write no Attested Computation:
describe the value in a concept of another type (e.g. `Metric`) and
report the gap. For a long computation that already lives in a file, set
`computation: "/<path to the file>"` in the frontmatter instead, and put
no fenced block under `# Computation`.

Add `executor: { resource: "/<path to run instructions>", receipt:
[<field>, ...] }` and `attester: { resource: "/<path to deterministic
code>" }` only when those files exist; otherwise state under
`# Attestation` that the computation cannot be attested yet. Never write
`verified` when authoring.

```yaml
type: Attested Computation
title: <the computation, as a noun phrase>
description: <one sentence saying what this computes and for whom>
tags: [<tag>, <tag>]
status: draft
runtime: <bigquery | postgres | dbt | python | ...>
parameters:
  - { name: <param>, type: <string | integer | number | boolean | date | timestamp>, required: <true | false — default false> }
sources:
  - { id: <sanctioned-source>, resource: "<URL or /path of the approved query, model, or policy>", title: "<source title>" }
generated: { by: "claude-code/<model-id>", at: "<YYYY-MM-DDTHH:MM:SSZ>" }
```

# Purpose

<what this computation answers, and who consumes the result>

# Computation

```<runtime language, e.g. sql>
<the sanctioned computation, copied verbatim from its source; each parameter is a bind variable such as @year>
```

<the rules the computation implements, cited with a footnote whose label is the sanctioned source's id>

# Output

<shape of the result — columns, fields, or a one-line description>

# Attestation

<how a run is executed and checked, naming the executor and attester; or "Not attestable yet: no executor or attester exists.">

# Traceability

- Evidences: [<requirement or test plan title>](../requirements/<slug>.md)
- Runs in: [<environment title>](../environments/<slug>.md)
