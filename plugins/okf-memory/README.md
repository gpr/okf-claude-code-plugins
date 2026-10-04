# okf-memory

Stops Claude Code from paying for big files in full. When Claude reads a
whole file over a size limit, what it sees is the file's **memory** instead: a short
[OKF](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
concept with a structural outline of the file, every entry carrying its line
numbers. Claude then reads only the ranges it needs.

On `okf-reader/scripts/okf_context.py` (12 KB, 341 lines) the memory is ~600
tokens instead of ~3,100.

## How it works

One script (`scripts/okf_memory.py`), two events:

| Event | Matcher | Does |
|---|---|---|
| `PostToolUse` | `Read` | Full read of a file over `max_bytes` → creates or refreshes `.memory/<path>.md` and replaces the result Claude sees with it (`updatedToolOutput`). The Read itself ran, so Edit's read-before-edit rule is satisfied. |
| `PostToolUseFailure` | `Read` | A full read that failed — typically a file over Read's own size cap — gets the memory attached as `additionalContext` next to the error. |
| `PostToolUse` | `Edit\|Write\|MultiEdit`, ranged `Read` | Refreshes an **existing** memory whose source changed. Never creates one. |

A source at `path/to/file.ext` has its memory at
`.memory/path/to/file.ext.md`: the source's own path under `.memory/`, plus
the `.md` every OKF concept needs. The extension stays in the name so
`app.py` and `app.js` never share a memory. A file named exactly `index` or
`log` (no extension) gets no memory: `index.md` and `log.md` are reserved
OKF names at every level.

The reply Claude sees also tells it to use `Grep` on the original file to
find what the outline does not show (a string, a call site, a constant),
then Read only the range around the match.

### `.memory/` is an OKF bundle

Every time a memory is created or regenerated, the hook also maintains the
bundle-root files, so `.memory/` stays a valid OKF v0.2 bundle:

- `.memory/index.md` — created with `okf_version: "0.2"` if missing. Under
  `# Source Memories` it holds one entry per memory, sorted by path, with
  the memory's `description`; a refresh updates the entry in place. Anything
  else in the file is kept.
- `.memory/log.md` — newest date first, one entry per change:
  `**Creation**` for a new memory, `**Update**` for a regeneration. The same
  entry is not repeated under one date, so ten edits of a file in a day log
  one update.

```markdown
# Memory Update Log

## 2026-10-04
* **Update**: Regenerated [src/billing.py](src/billing.py.md) after its source file changed.
* **Creation**: Memory of the source file, [src/billing.py](src/billing.py.md).
```

Only memories written after this behaviour shipped are listed; an older
memory joins the index on its next regeneration. Parallel hooks serialize
their `index.md`/`log.md` updates with a lock file
(`.memory/.okf-memory.lock`); on Windows there is no lock, so two memories
created at the same instant can race and one index entry can be lost until
that memory is next regenerated.

If you set `memory_dir` to a directory that is not a dotdir, `okf-reader`'s
auto-discovery will find its `okf_version` and load it as a normative
bundle. Keep it a dotdir (the default) unless you want that.

### What is never replaced

- **Ranged reads** (`offset` or `limit` set). This is the escape hatch: when
  Claude really needs the whole file, it reads it with an explicit range.
- Files at or under `max_bytes`.
- Binary files (by extension or NUL byte), images, PDFs, notebooks.
- Files outside the project root, inside `.git`, or inside the memory dir.
- Files no outline can be built for (unknown language, minified code), and
  files whose memory would be more than half the size of the source — there
  the real content is the better answer.

### Staleness

Each memory records `source_sha256`. The hook checks it before serving,
so an outline with wrong line numbers is never served even if the
file changed outside Claude (git pull, another editor). The `PostToolUse`
hook refreshes memories right after Claude edits a file, so the next read is
already current.

## The memory file

```markdown
---
type: Source Memory
title: "src/billing.py"
description: "Structural outline of src/billing.py (Python, 812 lines)."
resource: "../../src/billing.py"
tags: [okf-memory]
sources: [{ id: source, resource: "../../src/billing.py", title: "src/billing.py" }]
generated: { by: okf-memory/0.1.0, at: 2026-10-03T20:38:49Z }
source_sha256: 99f1…
source_bytes: 31207
source_lines: 812
outline_entries: 42
---

# Outline

Language: Python. Method: syntax tree (Python ast). Line numbers are 1-based.

    L12-14: def load_rates() -> dict  # Exchange rates by currency.
    L64-77: class Invoice(Base)  # One billable document.
    L70-77:   def total(self) -> Decimal
    …

# Notes

<!-- Hand-written. Everything from this heading down survives regeneration. -->
```

`resource` and `sources[].resource` are relative to the memory file itself,
so they resolve to the source as OKF §6 reads a relative path.

Everything above `# Notes` is generated and overwritten on refresh.
Everything from `# Notes` down is yours — and Claude's: it is told it may
record durable facts about the file there ("`total()` excludes tax; tax is
applied in `finalize()`"), and they survive regeneration.

### Outline quality by language

| Language | Method |
|---|---|
| Python | Real syntax tree (stdlib `ast`): imports, constants, classes, methods, functions with signatures, line spans and first docstring line. |
| Markdown | Heading tree (ignores headings inside code fences). |
| JSON | Key tree with types and sizes, 3 levels deep. No line numbers. |
| JS/TS, Go, Rust, Java, Kotlin, Scala, Swift, C#, C/C++, Ruby, PHP, Bash, Lua, … | **With tree-sitter** (optional, see below): real syntax tree — classes, methods, functions, structs, traits, impls, with signatures, line spans and nesting. **Without it:** regex declaration scan, start line only, not a parse tree. |
| CSS, SQL, YAML, TOML, INI | Regex declaration scan. |

The outline's `Method:` line always says which strategy produced it.

## tree-sitter (optional)

```
bin/okf-memory-setup            # install + download default grammars
bin/okf-memory-setup --check    # what is installed, no network
bin/okf-memory-setup --languages go,rust,typescript
```

The setup installs
[`tree-sitter-language-pack`](https://pypi.org/project/tree-sitter-language-pack/)
with `pip install --target` into `~/.local/share/okf-memory/pylib`
(`$XDG_DATA_HOME` respected) — no virtualenv, nothing in your system
site-packages — and downloads grammars into the package's cache. A copy
already importable by `python3` works too.

The hooks never download anything. `tree-sitter-language-pack` fetches a
missing grammar over the network on first use, so the hook only uses
languages already in its cache and falls back to the regex scan for the
rest. Re-run the setup to add a language.

## Configuration

| `userConfig` key | Default | Meaning |
|---|---|---|
| `max_bytes` | `20000` | Full reads above this many bytes show the memory instead. `0` disables replacement. |
| `memory_dir` | `.memory` | Where memories live, relative to the project root. |

Decide whether `.memory/` is committed. Committing shares the `# Notes`
sections with the team; the generated part churns on every source change.
Ignoring it keeps git clean and memories regenerate on demand.

## Limits

- Only the `Read` tool is covered. `cat` through Bash, or `Grep` with wide
  context, still returns the full file.
- The file is still read from disk; only what Claude sees is replaced, so
  the saving is in tokens, not I/O.
- `updatedToolOutput` must match Read's output schema, which Claude Code
  does not document. The hook rewrites only the `{"type": "text", "file":
  {"content", ...}}` shape and leaves anything else alone; if Claude Code
  rejects the replacement, Claude simply sees the real file. Check with a
  live session after Claude Code upgrades.
- Claude sees the memory with Read's line-number margin, which numbers the
  memory's lines. The `L<n>` entries inside it are the source's line
  numbers, and the header says so.

## Preview

```
bin/okf-memory-preview path/to/big_file.py [--project DIR] [--max-bytes N]
```

Simulates the `PostToolUse` hook after a full read: prints what Claude
would see and the size saved. Like the real hook, it
creates or refreshes the memory. Exits 1 when the read would go through.
