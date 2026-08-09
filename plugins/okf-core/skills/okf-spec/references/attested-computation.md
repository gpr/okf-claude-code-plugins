# Attested computations

Covers §10 of OKF v0.2.

An Attested Computation concept carries not just what a value *means* but
a sanctioned way to *compute* it, so a consumer can confirm an agent ran
the blessed computation instead of improvising its own. Provenance
(`trust-and-provenance.md`) answers "where did this claim come from";
attestation answers "was this number produced the way we said it must
be." OKF records the computation and the means to check it — it does not
execute anything itself.

## A computation is its own concept

A sanctioned computation is a standalone concept of
`type: Attested Computation`. A concept that needs the value (a `Metric`,
a `BigQuery Table`) links to it with a normal markdown link. Three
reasons it's standalone rather than embedded:

- **`runtime` defines what `parameters` mean.** A parameter is a SQL bind
  variable, a dbt var, or a Python argument depending on the runtime.
  Keeping `runtime` and `parameters` in one frontmatter makes the
  binding semantics self-evident.
- **One computation, many consumers.** The same computation can back a
  metric, a dashboard concept, and a report — referenced once, reused.
- **Trust state is per computation.** `verified`, `stale_after`, and a
  single `attester` describe one thing. Revenue, profit, and margin each
  verify and attest independently — three concepts, not three entries in
  one frontmatter.

## Contract fields

In addition to the provenance/trust/lifecycle families
(`trust-and-provenance.md`), an Attested Computation concept carries:

- `runtime`: REQUIRED. How to run the computation, and so what
  `parameters` means and how the executor/attester interpret it.
  Example values: `bigquery`, `postgres`, `dbt`, `python`, `Looker`.
- `parameters`: a list of the typed, named holes the agent may fill.
  Each entry: `{name, type, required}`. Binding semantics follow
  `runtime`.
- `computation`: optional path to a file holding the computation, used
  instead of an inline body fence (see below). Absent ⇒ the body
  `# Computation` fence is the computation.
- `executor`: how the computation is run. `resource` names run
  instructions or code; a runner (an agent, or deterministic consumer
  code) follows it. `receipt` declares the fields a run must return —
  the evidence the attester inspects (e.g. a BigQuery `job_id` and the
  SQL the job actually executed).
- `attester`: the deterministic check. `resource` names code (no LLM)
  that takes a receipt and returns a verdict. Meant to run
  consumer-side.

What sits behind a `resource` (a Skill, a script, a container) is a
packaging choice — OKF fixes the interface, not the packaging.

```markdown
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
stale_after: 2026-09-23
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
---

# Computation

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = @year

The computation binds only the declared `parameters`, per the recognition
policy.[^rev-policy]

[^rev-policy]: Revenue recognition policy
```

## The computation: inline vs file

- **Inline:** a single fenced code block in the body under
  `# Computation`. Best for a short computation reviewed alongside the
  contract.
- **File:** set `computation` to a path and omit the body fence. Best for
  a long or generated computation, or one already kept as a real file
  shared with non-OKF tooling.

```yaml
runtime: bigquery
computation: references/computations/lib/revenue.sql
parameters:
  - { name: year, type: integer, required: true }
```

An agent MAY only supply *values* for the declared `parameters`; it MUST
NOT author or edit the computation. Binding `computation` with the
parameter values into the executable artifact is the consumer's job, and
the attester independently re-derives that same binding to compare
against what actually ran. Because the comparison is on the expanded,
compiled artifact the receipt carries (`executed_sql`, `compiled_sql`), a
rewritten query, a swapped computation file, or a mutated dependency
fails the check.

## How a consumer uses it (informative)

The runtime artifacts below are **not** stored in the bundle.

1. **Discover** via `type: Attested Computation`.
2. **Load** the contract from frontmatter and the computation from the
   body (or the file named by `computation`).
3. **Parameterize**: the agent supplies values for declared parameters.
4. **Execute**: the executor runs the bound computation and returns a
   receipt shaped by `executor.receipt`.
5. **Attest**: the consumer runs the attester over the receipt, checking
   provenance (the computation that ran equals `computation` bound with
   the claimed parameters, not agent-authored SQL) and fidelity (the
   displayed value matches the receipt's authoritative source, re-read
   by job id rather than taken from the agent's text).
6. **Gate**: refuse to display a failing attestation; warn or refuse
   when `today >= stale_after`. On success, surface the verdict (e.g. a
   link to the job log) so trust is visible.

## Verification versus attestation

- `verified` confirms the *definition* still matches policy. Doc-level,
  slow, recorded in the bundle.
- Attestation confirms a single *run* produced the value the sanctioned
  way. Per-call, runtime, not stored in the bundle.

A concept with a stale definition can still attest cleanly, and a
freshly-verified definition still requires attestation on each run —
both are needed.
