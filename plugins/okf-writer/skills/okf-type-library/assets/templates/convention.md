---
type: Template
title: Convention template
description: A rule a newcomer would otherwise get wrong.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Convention` concepts — a rule a newcomer would
otherwise get wrong, and why it exists. Copy the fence below into a new
file's frontmatter, then fill the body headings. Resolve every
`<placeholder>` or delete its line.

```yaml
type: Convention
title: <the rule, as a short imperative>
description: <one sentence saying what this rule is and why it matters>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Rule

<the rule, stated as an imperative>

# Why

<what goes wrong without this rule — the mistake it prevents>

# Examples

Do:

```
<example that follows the rule>
```

Don't:

```
<example that violates the rule>
```

# Enforcement

<how this is checked — a lint rule, a review checklist item, or "none,
convention only">

# Traceability

- Constrains: [<component, interface, or plan item title>](/components/<slug>.md)
