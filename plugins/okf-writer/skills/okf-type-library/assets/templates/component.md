---
type: Template
title: Component template
description: One unit of the system, its responsibility and boundary.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Component` concepts — one unit of the system, what
it owns, and where its boundary sits. Copy the fence below into a new
file's frontmatter, then fill the body headings. Resolve every
`<placeholder>` or delete its line.

```yaml
type: Component
title: <component name>
description: <one sentence saying what this component is responsible for>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Responsibility

<the one thing this component owns>

# Boundary

- In: <what this component does>
- Out: <what it deliberately delegates elsewhere>

# Interfaces

| Direction | Interface | Purpose |
|---|---|---|
| <in/out> | <interface> | <why> |

# State it owns

<data or state this component is the source of truth for, or "none">

# Traceability

- Realizes: [<specification title>](/specifications/<slug>.md)
- Exposes: [<interface title>](/interfaces/<slug>.md)
- Depends on: [<component title>](/components/<slug>.md)
- Runs in: [<environment title>](/environments/<slug>.md)
