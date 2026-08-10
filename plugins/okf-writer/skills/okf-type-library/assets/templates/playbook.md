---
type: Template
title: Playbook template
description: A repeatable procedure a human runs.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Playbook` concepts — a repeatable procedure a human
runs, step by step. Copy the fence below into a new file's frontmatter,
then fill the body headings. Resolve every `<placeholder>` or delete its
line.

```yaml
type: Playbook
title: <the procedure, stated as an action>
description: <one sentence saying when to run this and what it achieves>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# When to run this

<the trigger — an alert, a schedule, a request>

# Preconditions

- <what must be true before starting>

# Steps

1. <command or action> — expect <result>

# If it goes wrong

| Symptom | Action |
|---|---|
| <symptom> | <action> |

# Traceability

- Operates: [<component or environment title>](/components/<slug>.md)
- Written after: [<postmortem title>](/postmortems/<slug>.md)
