# Traceability

OKF has no typed relation fields and no wikilinks (see `okf-spec`'s
`cross-linking.md`, or `okf-concept`'s `okf-essentials.md` if `okf-core`
isn't installed) — a link is a plain markdown link, and the kind of
relationship it asserts lives in the surrounding prose, not the link
itself. This catalog carries that topology in a convention instead: a
uniform heading name plus a bold lead word on each bullet, both
greppable.

## The graph

```
Specification ──specifies──▶ Requirement ──delivered by──▶ Plan Item
      │                            │                            │
      │                            └──verified by──▶ Test Plan ◀─┘
      │                            ▲
      │                            └──threatens──── Risk
      ▼
  Component ──exposes──▶ Interface ◀──constrains──── Convention
      │
      ▼
  Environment ──installs──▶ Dependency ◀──pins── Technology ◀──selects── ADR
      ▲
      └──concerns──── Postmortem ──produces──▶ Playbook, Risk, ADR
```

The spine — `Specification → Requirement → Plan Item → ADR → Technology
→ Dependency` — is the five types the spec-driven-development preset
installs, plus `Test Plan` for verification.

## Convention

Every skeleton except `Glossary Term` ends with a `# Traceability`
heading:

```markdown
# Traceability

- <Bold relation>: [<title hint>](/<dir>/<slug>.md)
```

One fixed heading name across the catalog makes
`grep -rn '^# Traceability' <bundle-root>/` enumerate the whole link
graph without opening every file. `Glossary Term` uses `# Related
terms` instead — "traceability" is the wrong word for a definition, and
this exception is deliberate, not an oversight.

## Directory hints

Placeholder links use `okf-concept` step 4's `<plural-slug>/` default
(`/requirements/`, `/plan-items/`, `/test-plans/`, `/technologies/`,
`/dependencies/`, `/components/`, `/interfaces/`, `/risks/`,
`/playbooks/`, `/environments/`, `/postmortems/`, `/conventions/`), with
one named exception: **ADR links use `/decisions/`**, the directory
`okf-concept`'s own worked examples establish twice
(`okf-concept/references/authoring-procedure.md`, "Worked example: new
type").

Every one of these paths lives inside a `<placeholder>` line. When a
bundle files a type somewhere else, `okf-concept` step 6 rewrites or
deletes the whole line while resolving placeholders — a wrong directory
hint costs nothing, it's a starting guess, not a constraint.

## Per-type bullets

| Type | `# Traceability` bullets |
|---|---|
| Specification | Requirements, Plan, Decisions |
| Requirement | Specified by, Delivered by, Verified by, Threatened by |
| Plan Item | Satisfies, Specified by, Decided in, Verified by |
| ADR | Decides for, Selects, Supersedes |
| Technology | Decided in, Pinned by, Runs in |
| Dependency | Chosen for, Decided in, Installed in |
| Component | Realizes, Exposes, Depends on, Runs in |
| Interface | Exposed by, Consumed by, Constrained by |
| Test Plan | Verifies, Runs in |
| Risk | Threatens, Mitigated by, Realized in |
| Playbook | Operates, Written after |
| Environment | Hosts, Installs, Governed by |
| Postmortem | Concerns, Produced |
| Convention | Constrains |
| Attested Computation | Evidences, Runs in |
| Glossary Term | `# Related terms` — Related, Where it appears |

Not every bullet needs a target at authoring time — same rule as any
other placeholder: resolve it or delete the line.
