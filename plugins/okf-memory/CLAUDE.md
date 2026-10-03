# okf-memory

PreToolUse/PostToolUse hooks that answer oversized full `Read`s with a
per-file memory (OKF concept, structural outline with line numbers).
User-facing behaviour is in `README.md`; this file covers what breaks when
you edit the implementation.

## File map

- `scripts/okf_memory.py` — the hook; dispatches on `hook_event_name`
- `scripts/outline.py` — outline extraction: Python `ast`, Markdown headings,
  JSON key tree, regex declaration scan for everything in `LANGS`
- `hooks/hooks.json` — registers the script on `PreToolUse(Read)` and
  `PostToolUse(Read|Edit|Write|MultiEdit)`
- `bin/okf-memory-preview` — runs the PreToolUse path for one file
- `tests/test_okf_memory.py` — stdlib `unittest`

## Invariants in `scripts/okf_memory.py`

- **Fail open.** `main()` catches `Exception`. Any failure must end in "no
  output" = the Read proceeds. Never emit a deny from an error path.
- Ranged reads (`offset`/`limit` not None) are never denied. That is the only
  way Claude can read a big file in full; removing it makes such files
  unreadable through `Read`.
- Stale memories are never served: `ensure_memory()` compares
  `source_sha256` before returning existing content.
- Everything from `NOTES_HEADING` down is preserved verbatim on regeneration
  (`notes_section()`). Don't change the heading text without migrating it.
- `PostToolUse` never creates a memory (`create=False`) and never prints.
- Memory path keeps the source extension (`file.ext.md`) — changing it to
  `file.md` makes same-stem files collide.
- No network; stdlib only.

## Adding a language

Add an entry to `LANGS` (ext → name, patterns, flags) in `outline.py`, and
an `_ALIASES` row for extra extensions. Add a case in `OutlineTests`.

## Adding a `userConfig` key

1. `userConfig` in `.claude-plugin/plugin.json`
2. `option("<key>", default)` in `okf_memory.py`
3. A flag in `bin/okf-memory-preview`

## Tests

```
python3 -m unittest discover -s plugins/okf-memory/tests
```
