---
type: Template
title: Risk template
description: What could go wrong, how bad, and who watches it.
status: draft
generated: { by: <claude-code/model-id>, at: <RFC 3339 UTC, Z suffix> }
---

Skeleton for `type: Risk` concepts — one thing that could go wrong, how
bad it would be, and who is watching for it. Copy the fence below into a
new file's frontmatter, then fill the body headings. Resolve every
`<placeholder>` or delete its line.

```yaml
type: Risk
title: <the risk, as a short noun phrase>
description: <one sentence stating the trigger and the impact>
tags: [<tag>, <tag>]
status: draft
stale_after: <YYYY-MM-DD — when this assessment should be revisited>
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Risk

If <trigger>, then <impact>.

# Assessment

| Likelihood | Impact | Exposure |
|---|---|---|
| <low/medium/high> | <low/medium/high> | <resulting priority> |

# Mitigation

<what reduces the likelihood or impact>

# Escalation trigger

<the observable signal that means this risk is materializing>

# Owner

<who watches this risk>

# Traceability

- Threatens: [<requirement or component title>](/requirements/<slug>.md)
- Mitigated by: [<plan item title>](/plan-items/<slug>.md)
- Realized in: [<postmortem title>](/postmortems/<slug>.md)
