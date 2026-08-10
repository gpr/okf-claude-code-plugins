---
type: Template
title: Technology template
description: A technology committed to, and where it applies.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Technology` concepts — a category-level choice and
its blast radius. Copy the fence below into a new file's frontmatter,
then fill the body headings. Resolve every `<placeholder>` or delete its
line.

```yaml
type: Technology
title: <the technology, as a name>
description: <one sentence saying what this project uses it for>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# What it is used for

<the job this technology does in this project>

# Where it applies

- In: <where this technology is used>
- Out: <where it deliberately is not>

# Alternatives not taken

| Alternative | Why not |
|---|---|
| <alternative> | <reason> |

# Operational cost

<what it costs to run, operate, or keep current>

# Traceability

- Decided in: [<ADR title>](/decisions/<slug>.md)
- Pinned by: [<dependency title>](/dependencies/<slug>.md)
- Runs in: [<environment title>](/environments/<slug>.md)
