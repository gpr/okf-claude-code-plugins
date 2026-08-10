---
type: Template
title: Environment template
description: One place the system runs and what differs there.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Environment` concepts — one place the system runs,
and what makes it different from the others. Copy the fence below into a
new file's frontmatter, then fill the body headings. Resolve every
`<placeholder>` or delete its line. Never record secrets, credentials,
or connection strings here — link to where they live instead.

```yaml
type: Environment
title: <environment name>
description: <one sentence saying what this environment is for>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Purpose

<what this environment is for and who uses it>

# Access

<who can reach it, and how — link to the process, not the credentials>

# Configuration

| Setting | Value | Differs from |
|---|---|---|
| <setting> | <value> | <other environment> |

# Data

<what data lives here — real, synthetic, or a subset, and its
retention>

# Traceability

- Hosts: [<component title>](/components/<slug>.md)
- Installs: [<dependency title>](/dependencies/<slug>.md)
- Governed by: [<convention title>](/conventions/<slug>.md)
