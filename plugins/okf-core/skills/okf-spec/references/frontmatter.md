# Concept documents

Covers §4 of OKF v0.2.

Every concept is a UTF-8 markdown file with two parts: a YAML frontmatter
block delimited by `---` on its own line at the start of the file and a
closing `---` on its own line, then a markdown body.

## Frontmatter

```yaml
---
type: <Type name>                  # REQUIRED
title: <Optional display name>
description: <Optional one-line summary>
resource: <Optional canonical URI for the underlying asset>
tags: [<tag>, <tag>, ...]          # Optional
# ... trust, lifecycle, provenance, and computation families (see
#     trust-and-provenance.md, attested-computation.md)
# ... other producer-defined key/value pairs
---
```

**Required:**

- `type`: a short string identifying the kind of concept. Consumers use
  it for routing, filtering, and presentation. Example values:
  `BigQuery Table`, `BigQuery Dataset`, `API Endpoint`, `Metric`,
  `Playbook`, `Reference`, `Attested Computation`. Type values are not
  registered centrally — pick something descriptive and self-explanatory.
  Consumers MUST tolerate unknown types gracefully, typically by treating
  them as generic concepts.

`type` is the only always-required key. A concept carrying just `type`
is fully conformant.

**Recommended:**

- `title`: human-readable display name. If omitted, consumers MAY derive
  one from the filename.
- `description`: a single sentence summarizing the concept. Used by
  `index.md` generators, search snippets, and previews.
- `resource`: a URI that uniquely identifies the underlying asset the
  concept describes. Absent for concepts describing abstract ideas rather
  than physical resources.
- `tags`: a YAML list of short strings for cross-cutting categorization.

The optional provenance, trust, and lifecycle families
(`trust-and-provenance.md`) and the computation fields for Attested
Computation concepts (`attested-computation.md`) may also appear.

**Extensions:** producers MAY include any additional keys. Consumers
SHOULD preserve unknown keys when round-tripping and MUST NOT reject
documents with unrecognized fields.

## Body

The body is standard markdown. Favor structural markdown (headings,
lists, tables, fenced code blocks) over freeform prose — structure aids
both human reading and agent retrieval.

There are no required body sections. These headings have conventional
meaning and SHOULD be used when applicable:

| Heading | Purpose |
|---|---|
| `# Schema` | Structured description of an asset's columns/fields. |
| `# Examples` | Concrete usage examples, often as fenced code blocks. |
| `# Computation` | The sanctioned computation of an Attested Computation. See `attested-computation.md`. |

Per-claim attribution to external sources uses markdown footnotes keyed
to `sources` entries rather than a body citations list — see
`trust-and-provenance.md`.

## Example: a concept bound to a resource

```markdown
---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-05-28T14:30:00Z }
---

# Schema

| Column        | Type      | Description                              |
|---------------|-----------|------------------------------------------|
| `order_id`    | STRING    | Globally unique order identifier.        |
| `customer_id` | STRING    | Foreign key into [customers](/tables/customers.md). |
| `total_usd`   | NUMERIC   | Order total in US dollars.               |
| `placed_at`   | TIMESTAMP | When the customer submitted the order.   |

# Joins

Joined with [customers](/tables/customers.md) on `customer_id`.
```

## Example: a concept not bound to a resource

```markdown
---
type: Playbook
title: "Incident response: data freshness alert"
description: Steps to triage a freshness alert on the orders pipeline.
tags: [oncall, incident]
generated: { by: human:ahormati, at: 2026-04-12T09:00:00Z }
---

# Trigger

A freshness alert fires when `orders` lags more than 30 minutes behind its
expected SLA. See the [orders table](/tables/orders.md).

# Steps

1. Check the [ingestion job dashboard](https://example.com/dash).
2. ...
```
