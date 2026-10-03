---
type: Template
title: Postmortem template
description: What broke, what it cost, what changed as a result.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Postmortem` concepts — what broke, what it cost, and
what changed as a result. Copy the fence below into a new file's
frontmatter, then fill the body headings. Resolve every `<placeholder>`
or delete its line. Name systems and decisions, not people.

```yaml
type: Postmortem
title: <the incident, as a short noun phrase>
description: <one sentence summarizing what happened>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Impact

<who or what was affected, and for how long>

# Timeline

| Time (UTC) | Event |
|---|---|
| <time> | <event> |

# Contributing factors

- <factor — a system condition or a decision, not a person>

# What we changed

- <the concrete follow-up: a Plan Item, an ADR, a Risk raised>

# Traceability

- Concerns: [<component or environment title>](/components/<slug>.md)
- Produced: [<ADR, Playbook, or Risk title>](/adrs/<slug>.md)
