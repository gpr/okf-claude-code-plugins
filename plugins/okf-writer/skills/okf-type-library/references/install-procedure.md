# Install procedure

The full form of `SKILL.md`'s outline; step numbers here match it. Read
`catalog.md` before step 3; read `traceability.md` if you need to explain
a pre-wired link.

## Step 1 — Locate the bundle root

1. If the session context already contains an okf-reader "OKF bundles"
   table, its paths are the candidate set. Read the table; do not
   re-scan.
2. Otherwise, scan the way okf-reader does: candidates are directories
   containing an `index.md` whose frontmatter declares `okf_version`, at
   most 4 levels below the project (repository) root, skipping
   dot-directories (except `.okf`), `node_modules`, `venv`, `.venv`,
   `__pycache__`, `dist`, `build`, `target`, `vendor`, and the vendored
   cache (`.okf/cache`). If none declares `okf_version`, fall back to
   whichever of `spec/`, `docs/okf/`, `knowledge/` has an `index.md`.
3. Resolve:
   - **0 candidates** — ask the user: name an existing bundle directory,
     or a path at which to start a new one. Never invent a root.
   - **1 candidate** — use it, unless it is the trusted bundle (below),
     which always asks.
   - **N candidates** — if the request names a path inside exactly one,
     use that one; otherwise ask which.
4. A directory the user names explicitly is the bundle root even
   without an `okf_version` marker — the marker is a discovery aid, not
   a conformance requirement.
5. In okf-reader's injected table, the row with `Bundle` id `standards`
   is the organization's trusted bundle. Never treat it as a write
   target without asking first, even when it is the only candidate.

This mirrors `okf-concept`'s `references/authoring-procedure.md` §Step
1. If the two disagree, that file wins — it is the longer form. Change
both together.

## Step 2 — Read the existing registry

1. Read `<root>/templates/index.md`.
   - Present — each entry's link text is a canonical `type` string,
     each link target is `templates/<slug>.md`.
   - Absent but `templates/` exists — list `templates/*.md` and read the
     `type:` inside each one's skeleton fence.
   - `templates/` absent entirely — the registry is empty.
2. Also collect `type:` values already in use by concepts under
   `<root>`, excluding `<root>/templates/` — a bundle can predate this
   skill and have types with no template.
3. This union is the skip-list for step 3.

## Step 3 — Select

1. **Named types win.** If the request names types explicitly ("add
   Technology and Dependency templates"), install exactly those — no
   preset, no additions. Match each name against the catalog with
   `norm()` (defined in `okf-concept/references/templates.md`).
2. **Otherwise, match a preset phrase** (table in `SKILL.md`). First
   match wins; two matches — union them and say so at the confirm step.
3. **Otherwise (vague intent)** — use the `minimal` preset: Specification,
   ADR, Plan Item. Adding a type later is one re-run; removing one after
   `okf-concept` has adopted it as a canonical spelling means manually
   cleaning `templates/index.md`, the template file, and every concept
   written against it — so default small.
4. **Subtract what exists.** Drop any selected type whose `norm()`
   matches an entry from step 2's skip-list. Report each as
   `skip, already exists` rather than dropping it silently.
## Step 4 — Confirm once

In one message, before any write: bundle root, preset (if any) and what
triggered it, each type with its target path and new/skip status, and
what else will be touched (`templates/index.md`, `log.md`). No per-file
confirmation.

## Step 5 — Write each template

For each selected type:

1. Read `assets/templates/<slug>.md` from this skill's own directory.
2. Replace the single `generated:` line with
   `generated: { by: claude-code/<running model id>, at: <now, RFC 3339
   UTC, Z suffix> }`. The literal model id shown in this skill's docs
   (e.g. `claude-code/claude-opus-5`) is illustrative and never copied
   verbatim — substitute the actual running model.
3. Every other byte is transcribed unchanged — do not re-type or
   reformat the skeleton.
4. Write to `<root>/templates/<slug>.md`. Never overwrite: a
   pre-existing file at that path was already a skip at step 3. If one
   appears anyway between confirm and write, stop and report rather
   than merge.

## Step 6 — `templates/index.md`

1. Create with H1 `# Templates` if absent.
2. **Back-fill.** If `templates/` already held `*.md` files but no
   `index.md`, add an entry for each of those too, reading canonical
   spelling from each file's own fence `type:`. Skipping this step
   hides those pre-existing templates from `okf-concept` step 2, which
   stops scanning `templates/*.md` the moment an index exists.
3. Entry format: `* [<canonical Type>](<slug>.md) - <one-liner>`, link
   text byte-identical to the written file's fence `type:`, one-liner
   byte-identical to the written file's own `description`. Insert
   alphabetically if the file is already sorted by link text, else
   append.

## Step 7 — Bundle-root `index.md`

If `templates/` was newly created this run, add
`* [Templates](templates/) - Concept skeletons, one per type.` to
`<root>/index.md`, creating that file with `okf_version: "0.2"` if it
doesn't exist.

## Step 8 — `log.md`

Bundle root only.

1. Read `<root>/log.md`; create with H1 `# Directory Update Log` if
   absent.
2. Today's `## YYYY-MM-DD` heading: if present, append bullets at the
   end of its block; if absent, insert it immediately after the H1,
   above all existing date headings (newest first) — no blank line
   between the heading and its first bullet, matching `okf-concept`'s
   `log.md` convention exactly (see its worked examples in
   `authoring-procedure.md`).
3. One bullet per installed template, bundle-root-relative link:
   `* **Creation**: Installed the [<Type> template](/templates/<slug>.md) from the okf-type-library catalog.`

## Step 9 — Self-check and report

- Every written file has exactly two `^---$` lines.
- Every written file's frontmatter contains `type: Template`.
- No `<…>` survives in any written file's own frontmatter (the fence
  and body keep theirs — that's expected).
- Every installed slug has an entry in `templates/index.md` whose link
  text matches its fence `type:` exactly.
- No written file has a `verified:`, `attester:`, or `executor:` key —
  check keys at line start (`^\s*(verified|attester|executor):`), not
  bare words: `attested-computation.md`'s prose names all three to
  forbid them.
- List every file written, and every type skipped and why.

## Single-type mode (invoked by `okf-concept`)

`okf-concept` step 7 calls this procedure for one catalogued type it has
already chosen and confirmed with the user (its step 4, case 3). In this
mode:

- Skip steps 1–4. The bundle root comes from `okf-concept`, the
  selection is that one type, and `okf-concept`'s own confirm already
  covered the install — don't ask a second time.
- No skip-list check: `okf-concept` takes this path only for a type new
  to the bundle. Never overwrite still holds — if
  `<root>/templates/<slug>.md` exists anyway, stop and report.
- Run steps 5–8 as written, for that one type: write the template, add
  its `templates/index.md` entry (with back-fill), link `templates/` from
  the bundle-root `index.md` if it is new, and log the usual step 8
  `Installed the … template` bullet.
- Run step 9's checks, then hand back to `okf-concept`, which loads the
  installed template's fence and writes the concept.
