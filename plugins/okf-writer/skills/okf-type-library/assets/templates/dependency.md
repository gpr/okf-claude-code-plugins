---
type: Template
title: Dependency template
description: One pinned third-party artifact, version and licence.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Dependency` concepts — one third-party artifact this
project actually pins, at a version, with a licence and an upstream
owner. Copy the fence below into a new file's frontmatter, then fill the
body headings. Resolve every `<placeholder>` or delete its line.

```yaml
type: Dependency
title: <package or service name>
description: <one sentence saying what this project uses it for>
resource: <registry, package, or repository URL>
tags: [<tag>, <tag>]
status: draft
stale_after: <YYYY-MM-DD — when the pin should be revisited>
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Pin

| Field | Value |
|---|---|
| Version | `<exact version or range>` |
| Declared in | `<lockfile or manifest path>` |
| Licence | <SPDX identifier> |
| Upstream owner | <organisation or maintainer> |

# Why this one

<what it does here that nothing already in the tree does>

# Risks on upgrade

- <breaking-change surface, or "none known">

# Traceability

- Chosen for: [<technology title>](/technologies/<slug>.md)
- Decided in: [<ADR title>](/decisions/<slug>.md)
- Installed in: [<environment title>](/environments/<slug>.md)
