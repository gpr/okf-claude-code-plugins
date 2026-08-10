---
type: Template
title: Interface template
description: One contract between components, with its guarantees.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Interface` concepts — one contract between
components (an API, a CLI, an event schema), and what it promises. Copy
the fence below into a new file's frontmatter, then fill the body
headings. Resolve every `<placeholder>` or delete its line.

```yaml
type: Interface
title: <interface name>
description: <one sentence saying what this interface lets a caller do>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Contract

```
<request/response shape, CLI signature, or event schema>
```

# Guarantees

<what a caller can rely on — ordering, idempotency, latency, etc.>

# Errors

| Code | Meaning | Caller action |
|---|---|---|
| <code> | <meaning> | <action> |

# Versioning

<how a breaking change to this interface is signalled>

# Traceability

- Exposed by: [<component title>](/components/<slug>.md)
- Consumed by: [<component title>](/components/<slug>.md)
- Constrained by: [<convention title>](/conventions/<slug>.md)
