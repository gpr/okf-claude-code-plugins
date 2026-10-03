# okf-memory

Stops Claude Code from reading big files in full. When Claude asks for a
whole file over a size limit, it gets the file's **memory** instead: a short
[OKF](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
concept with a structural outline of the file, every entry carrying its line
numbers. Claude then reads only the ranges it needs.

On `okf-reader/scripts/okf_context.py` (12 KB, 341 lines) the memory is ~600
tokens instead of ~3,100.

## How it works

Two hooks, one script (`scripts/okf_memory.py`):

| Event | Matcher | Does |
|---|---|---|
| `PreToolUse` | `Read` | Full read of a file over `max_bytes` → creates or refreshes `.memory/<path>.md` and denies the read, with the memory as the reason Claude sees. |
| `PostToolUse` | `Read\|Edit\|Write\|MultiEdit` | Refreshes an **existing** memory whose source changed. Never creates one. |

A source at `path/to/file.ext` has its memory at
`.memory/path/to/file.ext.md`. The extension stays in the name so `app.py`
and `app.js` never share a memory.

### What is never intercepted

- **Ranged reads** (`offset` or `limit` set). This is the escape hatch: when
  Claude really needs the whole file, it reads it with an explicit range.
- Files at or under `max_bytes`.
- Binary files (by extension or NUL byte), images, PDFs, notebooks.
- Files outside the project root, inside `.git`, or inside the memory dir.
- Files no outline can be built for (unknown language, minified code), and
  files whose memory would be more than half the size of the source — there
  the deny would only cost a round trip.

### Staleness

Each memory records `source_sha256`. The `PreToolUse` hook checks it before
serving, so an outline with wrong line numbers is never served even if the
file changed outside Claude (git pull, another editor). The `PostToolUse`
hook refreshes memories right after Claude edits a file, so the next read is
already current.

## The memory file

```markdown
---
type: Source Memory
title: "src/billing.py"
description: "Structural outline of src/billing.py (Python, 812 lines)."
resource: "src/billing.py"
tags: [okf-memory]
generated: { by: okf-memory, at: 2026-10-03T20:38:49Z }
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

Everything above `# Notes` is generated and overwritten on refresh.
Everything from `# Notes` down is yours — and Claude's: it is told it may
record durable facts about the file there ("`total()` excludes tax; tax is
applied in `finalize()`"), and they survive regeneration.

### Outline quality by language

| Language | Method |
|---|---|
| Python | Real syntax tree (`ast`): imports, constants, classes, methods, functions with signatures, line spans and first docstring line. |
| Markdown | Heading tree (ignores headings inside code fences). |
| JSON | Key tree with types and sizes, 3 levels deep. No line numbers. |
| JS/TS, Go, Rust, Java, Kotlin, Scala, Swift, C#, C/C++, Ruby, PHP, Shell, SQL, CSS, YAML, TOML, INI | Declaration scan: lines matching per-language regexes, start line only. **Not a parse tree** — expect occasional misses and false hits. |

Hooks here are stdlib-only Python, and the stdlib has no parser for
languages other than Python; a real tree for them would need tree-sitter,
which this marketplace does not allow as a dependency.

## Configuration

| `userConfig` key | Default | Meaning |
|---|---|---|
| `max_bytes` | `20000` | Full reads above this many bytes are intercepted. `0` disables interception. |
| `memory_dir` | `.memory` | Where memories live, relative to the project root. |

Decide whether `.memory/` is committed. Committing shares the `# Notes`
sections with the team; the generated part churns on every source change.
Ignoring it keeps git clean and memories regenerate on demand.

## Limits

- Only the `Read` tool is intercepted. `cat` through Bash, or `Grep` with
  wide context, still reads the full file.
- The deny reason appears to Claude as a failed tool call; that is how a
  `PreToolUse` hook substitutes content.
- Claude Code's `Edit` requires the file to have been read first. A ranged
  read satisfies that; a denied full read does not.

## Preview

```
bin/okf-memory-preview path/to/big_file.py [--project DIR] [--max-bytes N]
```

Prints what Claude would receive and the size saved. Like the real hook, it
creates or refreshes the memory. Exits 1 when the read would go through.
