---
type: Template
title: Specification template
description: What one capability should do, before it is built.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Specification` concepts — what one capability should
do, described from outside, before it is built. Copy the fence below
into a new file's frontmatter, then fill the body headings. Resolve
every `<placeholder>` or delete its line.

```yaml
type: Specification
title: <the capability, as a noun phrase>
description: <one sentence saying what this specifies and for whom>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Problem

<what is not possible today, and who is blocked by it>

# Scope

- In: <what this specification covers>
- Out: <what it deliberately does not cover>

# Behaviour

<what the system does, observable from outside — one paragraph or
subsection per externally visible behaviour. No implementation detail.>

# Acceptance

- <a condition an implementation either meets or does not>

# Open questions

- <question> — <who decides, and by when>

# Traceability

- Requirements: [<requirement title>](/requirements/<slug>.md)
- Plan: [<plan item title>](/plan-items/<slug>.md)
- Decisions: [<ADR title>](/decisions/<slug>.md)
