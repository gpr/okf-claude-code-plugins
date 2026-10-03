---
type: Template
title: Plan Item template
description: One unit of implementation work and its done-condition.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Plan Item` concepts — one unit of implementation
work, traced back to what it satisfies. Copy the fence below into a new
file's frontmatter, then fill the body headings. Resolve every
`<placeholder>` or delete its line.

```yaml
type: Plan Item
title: <the work, stated as an action>
description: <one sentence saying what is true once this is done>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Goal

<the outcome this produces, in one sentence>

# Steps

1. <step, small enough that its result is checkable>

# Files touched

| Path | Change |
|---|---|
| `<path>` | <what changes there> |

# Done when

- <observable condition — not "the code is written">

# Traceability

- Satisfies: [<requirement title>](/requirements/<slug>.md)
- Specified by: [<specification title>](/specifications/<slug>.md)
- Decided in: [<ADR title>](/adrs/<slug>.md)
- Verified by: [<test plan title>](/test-plans/<slug>.md)
