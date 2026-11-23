---
type: Template
title: ADR template
description: One architectural decision, its forces, and its cost.
status: draft
generated: { by: "claude-code/<model-id>", at: "<YYYY-MM-DDTHH:MM:SSZ>" }
---

Skeleton for `type: ADR` concepts — one architectural decision, the
forces behind it, and what it costs. Copy the fence below into a new
file's frontmatter, then fill the body headings. Resolve every
`<placeholder>` or delete its line.

```yaml
type: ADR
title: <the decision, stated as an action>
description: <one sentence recording what was decided and why>
tags: [<tag>, <tag>]
status: draft
sources:
  - { id: <source-id>, resource: "<URL or /path this was written from>", title: "<source title>" }
generated: { by: "claude-code/<model-id>", at: "<YYYY-MM-DDTHH:MM:SSZ>" }
```

# Context

<what forced the decision — a constraint, an incident, or a requirement>

# Options considered

| Option | Why it was not chosen |
|---|---|
| <option> | <reason> |

# Decision

<the decision, one sentence, present tense>

# Consequences

- <what gets better>
- <what gets worse>

# Traceability

- Decides for: [<specification title>](../specifications/<slug>.md)
- Selects: [<technology title>](../technologies/<slug>.md)
- Supersedes: [<earlier ADR title>](../adrs/<slug>.md)
