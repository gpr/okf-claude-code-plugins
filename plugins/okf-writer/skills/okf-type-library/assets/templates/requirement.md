---
type: Template
title: Requirement template
description: One testable statement with a fit criterion.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Requirement` concepts — one atomic statement the
system must satisfy, with a way to tell whether it's met. Copy the fence
below into a new file's frontmatter, then fill the body headings.
Resolve every `<placeholder>` or delete its line.

```yaml
type: Requirement
title: <the requirement, as a short noun phrase>
description: <one sentence restating the shall-statement>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Statement

The system shall <observable behaviour>.

# Fit criterion

<how you'd measure this passing — a number, a test, an observation. If
you can't state one, this isn't ready to be a Requirement yet.>

# Rationale

<why this requirement exists — what breaks or is blocked without it>

# Priority

<must / should / could, and why>

# Traceability

- Specified by: [<specification title>](/specifications/<slug>.md)
- Delivered by: [<plan item title>](/plan-items/<slug>.md)
- Verified by: [<test plan title>](/test-plans/<slug>.md)
- Threatened by: [<risk title>](/risks/<slug>.md)
