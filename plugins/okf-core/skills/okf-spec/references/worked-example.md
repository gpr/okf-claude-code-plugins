# Worked example

Complete, copy-pasteable files. Use these as templates instead of
inventing field names.

## Bundle-root `index.md`

```markdown
---
okf_version: "0.2"
---

# Finance bundle

* [Income statement](metrics/income-statement.md) - Headline income-statement figures for a fiscal year.

## Computations

* [Revenue](computations/revenue.md) - Recognized revenue for a fiscal year.
* [Gross profit](computations/profit.md) - Gross profit by segment for a fiscal year.
```

## A concept with `sources`, `generated`, and `status`

```markdown
---
type: Metric
title: Income statement (fiscal year)
description: Headline income-statement figures for a fiscal year.
tags: [finance, income-statement]
status: stable
generated: { by: claude-code/claude-opus-5, at: 2026-08-09T14:30:00Z }
sources:
  - id: fpa-handbook
    resource: https://wiki.acme/finance/fpa-handbook
    title: FP&A reporting handbook
---

# Definition

The income statement reports [revenue](../computations/revenue.md) and
[gross profit](../computations/profit.md) for a fiscal year, per the FP&A
reporting handbook.[^fpa-handbook] Each figure is produced by a
sanctioned, attestable computation; this concept only narrates them.

[^fpa-handbook]: FP&A reporting handbook
```

Note what's absent: no `verified` (this agent didn't confirm it against
policy — a human or process would add that later), no `attester` (this
concept isn't itself an Attested Computation, it links to one).

## `log.md` entry for the change above

```markdown
# Directory Update Log

## 2026-08-09
* **Creation**: Added the [income statement](metrics/income-statement.md) concept, linking revenue and gross profit.
```

## Full v0.1 → v0.2 migration of one concept

**v0.1 form** — one doc, SQL as prose an agent could rewrite, flat
citations, only `timestamp`:

```markdown
---
type: Metric
title: Income statement (fiscal year)
description: Headline income-statement figures for a fiscal year.
tags: [finance, income-statement]
timestamp: '2026-05-28T22:53:05+00:00'
---

# Definition
The income statement reports revenue and gross profit for a fiscal year.

# Revenue
Recognized revenue sums `amount` over rows booked to the fiscal year:

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = <year>

# Citations
- https://wiki.acme/finance/fpa-handbook
- https://wiki.acme/finance/revenue-recognition
```

**v0.2 form** — the figure splits into its own Attested Computation
concept, linked from a narrative concept:

```
bundles/finance/
  metrics/income-statement.md      type: Metric  (narrates, links)
  computations/revenue.md          type: Attested Computation
  computations/profit.md           type: Attested Computation  (runtime: dbt, not shown)
  references/skills/run-on-bq.md
  references/attesters/revenue.py
```

`computations/revenue.md`:

````markdown
---
type: Attested Computation
title: Revenue for fiscal year
description: Recognized revenue for a fiscal year, per Finance's definition.
status: stable
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
stale_after: 2026-09-23T00:00:00Z
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
---

# Computation

```sql
SELECT SUM(amount) AS revenue
FROM finance.recognized_revenue
WHERE fiscal_year = @year
```

The computation binds only the declared `parameters`, per the recognition
policy.[^rev-policy]

[^rev-policy]: Revenue recognition policy
````

See `attested-computation.md` for why the computation stands alone and
what an agent may and may not touch in it.
