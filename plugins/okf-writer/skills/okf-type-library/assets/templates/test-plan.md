---
type: Template
title: Test Plan template
description: How something gets proven, and what evidence counts.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Test Plan` concepts — how a Requirement or Plan Item
gets proven, and what evidence counts as proof. Copy the fence below
into a new file's frontmatter, then fill the body headings. Resolve
every `<placeholder>` or delete its line.

```yaml
type: Test Plan
title: <what is under test, as a noun phrase>
description: <one sentence saying what this proves>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Under test

<the requirement, plan item, or behaviour this plan verifies>

# Cases

| ID | Given / When / Then | Expected |
|---|---|---|
| <id> | <scenario> | <expected result> |

# Environment

<where these cases run — local, staging, a specific Environment concept>

# Evidence

<what artifact counts as proof — a passing run, a report, a receipt>

# Traceability

- Verifies: [<requirement or plan item title>](/requirements/<slug>.md)
- Runs in: [<environment title>](/environments/<slug>.md)
