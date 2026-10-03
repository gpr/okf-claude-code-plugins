# Provenance, trust, lifecycle, and actors

Covers §5 and §7 of OKF v0.2.

All families below are optional. Their absence carries meaning: an
unverified concept is distinguishable from a verified one, but is never
rejected for lacking any of these fields (see `conformance.md`).

## Provenance: `sources`

Records the materials a concept derives from, external or internal to
the bundle.

```yaml
sources:
  - id: ga4-schema
    resource: https://developers.google.com/analytics/bigquery/export-schema
    title: GA4 BigQuery Export schema
    author: team:ga4-docs
    usage_count: 5000
    last_modified: 2026-05-30T00:00:00Z
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
```

Each `sources` entry:

- `resource`: REQUIRED within an entry. Either a concrete artifact a
  consumer can follow (an absolute URL, a bundle-relative path, or a
  path into a `references/` subdirectory) or a population/scope
  descriptor it cannot (e.g. `all queries in BigQuery project X`).
- `id`: optional stable key used to attribute individual claims (below).
  SHOULD be present when the body cites the source.
- `title`: optional human-readable label.
- `author`, `usage_count`, `last_modified`: optional credibility
  signals, below.

**Source credibility signals.** OKF records objective, per-source
signals so a consumer can judge trust from the sources a concept was
extracted from. It does not store a credibility score — a score is
subjective, unportable, and goes stale. Credibility is *inferred* from
the signals, not stored:

- `author`: who or what produced the source, in the actor convention
  (below). An authority signal.
- `usage_count`: how often `resource` was exercised (dashboard views,
  query executions, page reads) over `usage_window`. An adoption/
  liveness signal. For a single artifact, its own exercise count; for a
  scope descriptor, the number of exercises within scope that touch the
  concept. Coarse — read it as liveness and trend, not a precise
  cross-kind ranking (a scheduled query's executions and a human's
  deliberate dashboard views don't carry equal weight).
- `last_modified`: when the source itself last changed (a datetime).
  A recency signal, distinct from `generated.at` below, which records
  when the *concept* was written.
- `usage_window`: written once as a sibling of `sources`, frames every
  `usage_count` with a `{from, to}` datetime range. A single entry MAY carry
  its own `usage_window` to override the shared one.

Lineage is expressed through links, not a dedicated field: when a
`resource` points at another OKF concept, the derivation edge already
exists in the bundle graph, so a consumer MAY recurse into that source's
own `sources`. External leaf sources carry only their intrinsic signals.

**Per-claim attribution.** Use a markdown footnote whose label is a
`sources[].id`:

```markdown
The `events_` table is sharded daily as `events_YYYYMMDD`.[^ga4-schema]

[^ga4-schema]: GA4 BigQuery Export schema
```

The footnote label is the join key into `sources`; resolve attribution
through the matching entry, not by parsing the footnote prose. Labels are
keyed rather than positional (`sources[0]`) because a positional index
misattributes silently the moment the list is reordered, whereas a
stable `id` survives reordering.

## Trust: `generated` and `verified`

`generated` records how the current content was produced. `verified`
records who or what has confirmed the content against its sources or
`resource`. Kept distinct because who *wrote* a concept need not be who
*confirmed* it.

```yaml
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
```

- `generated.by`: REQUIRED within `generated`. An actor (below).
- `generated.at`: an ISO 8601 datetime marking the content's last
  meaningful change. Distinguishes a recent edit from a stale fact.

```yaml
verified:
  - { by: human:ahormati, at: 2026-06-25T09:00:00Z }
  - { by: process:finance-nightly, at: 2026-06-26T02:00:00Z }
```

- `verified`: a list of verification events, each with `by` (an actor)
  and `at` (an ISO 8601 datetime). Multiple entries capture independent
  checks — e.g. a human sign-off plus a nightly process. "How recently"
  is the latest `at`.
- Independent of `generated.at`: content can change without
  re-confirmation, and facts can be re-confirmed without regeneration.
- A single verifier MAY be written as one `{by, at}` mapping without the
  list dash. Consumers MUST treat a bare mapping as a one-element list:

```yaml
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
```

## Trust tiers

Derived from `verified`, lowest to highest:

- No `verified` key ⇒ **unverified**.
- `verified` by non-`human:` actors only ⇒ **machine-confirmed**.
- `verified` by a `human:<id>` actor ⇒ **human-reviewed**.

A concept with no trust frontmatter is still consumable — MUST NOT be
rejected. Trust tiers are advisory signals, not access control.

## Lifecycle: `status`

```yaml
status: stable        # draft | stable | deprecated
```

- `draft`: not yet reviewed; possibly incomplete.
- `stable`: default; ready for consumption.
- `deprecated`: kept for links and history; no longer current.

Absent `status` ⇒ `stable`.

## Lifecycle: `stale_after`

```yaml
stale_after: 2026-09-23T00:00:00Z   # content is stale on/after this instant
```

Optional absolute instant (an ISO 8601 datetime). A concept is stale
when `now >= stale_after`. An absolute instant, not a relative TTL, keeps
the staleness decision a plain comparison independent of when the
concept is read.

## Actor convention

Fields recording an identity (`generated.by`, `verified[].by`) use one
convention:

- `<producer>/<version>` for agents and tools, e.g.
  `reference_agent/gemini-2.5-pro`.
- `human:<id>` for a person, e.g. `human:ahormati`.
- `process:<id>` for an automated process, e.g.
  `process:finance-nightly`.

Trust-tier classification keys off the `human:` prefix, so hand-authored
or human-confirmed content MUST use it.

For this plugin set's own actor literal and timestamp format when
writing concepts, see SKILL.md's "Rules for this agent".
