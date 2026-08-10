---
type: Template
title: Attested Computation template
description: A sanctioned computation, drafted for human attestation.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Attested Computation` concepts. Copy the fence below
into a new file's frontmatter, then fill the body headings. Resolve
every `<placeholder>` or delete its line. Never write `verified`,
`attester`, or `executor` here — those represent human or
deterministic-process confirmation this skill cannot supply. Never write
a real computation into `# Computation`; leave the TODO line exactly as
it appears below, byte for byte, until a human or the sanctioned process
supplies it.

```yaml
type: Attested Computation
title: <the computation, as a noun phrase>
description: <one sentence saying what this computes and for whom>
tags: [<tag>, <tag>]
status: draft
runtime: <bigquery | postgres | dbt | python | ...>
parameters:
  - { name: <param>, type: <type>, required: <true|false> }
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Purpose

<what this computation answers, and who consumes the result>

# Inputs

| Parameter | Type | Required |
|---|---|---|
| `<name>` | `<type>` | <true/false> |

# Computation

TODO: paste the sanctioned computation — an agent must not author this.

# Output

<shape of the result — columns, fields, or a one-line description>

# Traceability

- Evidences: [<requirement or test plan title>](/requirements/<slug>.md)
- Runs in: [<environment title>](/environments/<slug>.md)
