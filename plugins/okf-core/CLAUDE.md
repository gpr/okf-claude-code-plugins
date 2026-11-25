# okf-core

No hooks, no `userConfig`. Ships three skills and one agent:

- `okf-generate`, `okf-consume` — **vendored verbatim** from the OKF
  repository (see `UPSTREAM.md`). Never edit them here.
- `okf-spec` — ours: an index into the vendored OKF v0.3 `SPEC.md`, a field
  cheat sheet, and house rules.
- `agents/okf-search.md` — ours: locates and quotes concepts across a
  project's bundles.

User-facing scope is in `README.md`; this file covers what breaks when you
edit it.

## File map

- `UPSTREAM.md` — pinned upstream commit, the sha256 of every vendored file,
  and the re-sync procedure
- `LICENSE-okf-upstream.md` — Apache-2.0 text covering the vendored files
  (the repository itself is MIT)
- `skills/okf-generate/`, `skills/okf-consume/` — vendored skills, including
  their PyYAML-dependent `scripts/validate.py` and `scripts/scan.py`
- `skills/okf-spec/SKILL.md` — frontmatter `description` (the trigger phrase
  Claude matches to decide when to load this skill), the SPEC section → line
  index, and the house rules
- `skills/okf-spec/references/SPEC.md` — vendored OKF v0.3 specification
- `agents/okf-search.md` — haiku search agent. okf-reader's injected `RULES`
  text names it conditionally ("if it is available"), because okf-reader
  must work without okf-core installed
- `tests/test_vendored.py` — stdlib unittest; see below

## Vendored files

A local edit to a vendored file is silently lost at the next re-sync, so
`tests/test_vendored.py` fails when any of them stops matching its hash in
`UPSTREAM.md`, or when a new file appears in a vendored skill directory
without a row. To change their behaviour, add a house rule to
`okf-spec/SKILL.md` instead. To update them, follow "Re-sync" in
`UPSTREAM.md`.

The vendored scripts need PyYAML. That is the one exception to the
repository's stdlib-only rule, and it holds only because they are optional:
the skills tell the agent to check by hand when it cannot run them, and no
hook ever runs them.

The upstream skills declare `license: Apache-2.0` and keep
`metadata.publisher: google`; leave both as they are.

## Editing `okf-spec/SKILL.md`

- The `description` steers requests: format questions here, producing and
  validating to `okf-generate`, answering from a bundle to `okf-consume`.
  Keep it from claiming the verbs the other two own ("creating, editing,
  validating"), or the three skills compete for the same requests.
- The SPEC section → line index is checked by `tests/test_vendored.py`
  against the headings of `references/SPEC.md`; re-sync breaks it loudly
  when upstream moves text.
- The "House rules" section is house policy, not OKF spec text. Keep that
  distinction explicit in wording; don't let house policy get quoted back as
  normative SPEC.md content. A house rule may only fill a gap that SPEC.md
  and `okf-generate` leave open, or restate one of their rules — never
  contradict them.

## `agents/okf-search.md` restates spec vocabulary

The agent runs with only Read/Grep/Glob and a short prompt, so it loads
neither `okf-spec` nor `okf-consume`; the restatement in its prompt is what
it actually sees. It restates: concept identification (§3.2), link
resolution (§6), `status` values and `superseded_by` (§5.4), trust tiers
from current events (§5.3), staleness (§5.5), and okf-consume's conflict
order.

`references/SPEC.md` and `okf-consume/references/trust.md` win on any
disagreement. Re-check the agent whenever they change: nothing mechanical
catches drift here — this file drifted to a dead `Accepted`/`Implemented`
vocabulary once already, and to v0.2 trust rules a second time.

The agent must not assume okf-reader is installed either: when the caller
passes no bundle table, it finds bundle roots itself.

## Tests

```
python3 -m unittest discover -s plugins/okf-core/tests
```

Skill prose isn't unit-testable; verify changes to `okf-spec` and the agent
by reading them against `references/SPEC.md`.
