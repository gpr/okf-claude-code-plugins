#!/usr/bin/env python3
"""Tests for scripts/okf_memory.py and scripts/outline.py.

Run with: python3 -m unittest discover -s plugins/okf-memory/tests -v
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import okf_memory  # noqa: E402
import outline  # noqa: E402


def write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def big_python(n: int = 40) -> str:
    chunks = ['"""Module doc."""\nimport os\nfrom pathlib import Path\n\nLIMIT = 3\n']
    for i in range(n):
        body = "\n".join(f"    x{j} = {j} * {i}  # padding padding padding" for j in range(12))
        chunks.append(f'\ndef func_{i}(a: int, b: str = "x") -> int:\n    """Doc {i}."""\n{body}\n    return a\n')
    chunks.append("\nclass Thing(Base):\n    \"\"\"A thing.\"\"\"\n\n    def method(self):\n        pass\n")
    return "".join(chunks)


class TmpProjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = Path(self._tmpdir.name).resolve()
        self._env = dict(os.environ)
        self.addCleanup(lambda: os.environ.clear() or os.environ.update(self._env))
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.root)
        for key in ("MAX_BYTES", "MEMORY_DIR"):
            os.environ.pop(f"CLAUDE_PLUGIN_OPTION_{key}", None)

    def run_hook(self, payload: dict) -> tuple[str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), \
                unittest.mock.patch("sys.stdin", io.StringIO(json.dumps(payload))):
            okf_memory.main()
        return out.getvalue(), err.getvalue()

    def pre(self, path: Path, **tool_input) -> tuple[str, str]:
        return self.run_hook({
            "hook_event_name": "PreToolUse", "tool_name": "Read", "cwd": str(self.root),
            "tool_input": {"file_path": str(path), **tool_input},
        })

    def post(self, tool: str, path: Path) -> tuple[str, str]:
        return self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(self.root),
            "tool_input": {"file_path": str(path)},
        })


import unittest.mock  # noqa: E402


class PreReadTests(TmpProjectTestCase):
    def test_small_file_passes_through_silently(self):
        src = write(self.root, "small.py", "x = 1\n")
        out, err = self.pre(src)
        self.assertEqual((out, err), ("", ""))
        self.assertFalse((self.root / ".memory").exists())

    def test_big_file_is_denied_with_memory_and_memory_is_written(self):
        src = write(self.root, "pkg/mod.py", big_python())
        out, _ = self.pre(src)
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["permissionDecision"], "deny")
        reason = hso["permissionDecisionReason"]
        self.assertIn("def func_0(a: int, b: str='x') -> int", reason)
        self.assertIn("class Thing(Base)", reason)
        mem = self.root / ".memory/pkg/mod.py.md"
        self.assertTrue(mem.is_file())
        self.assertIn(mem.read_text(), reason)

    def test_ranged_read_is_never_intercepted(self):
        src = write(self.root, "mod.py", big_python())
        self.assertEqual(self.pre(src, offset=1, limit=50)[0], "")
        self.assertEqual(self.pre(src, limit=10)[0], "")
        self.assertEqual(self.pre(src, offset=0)[0], "")

    def test_outside_project_passes_through(self):
        with tempfile.TemporaryDirectory() as other:
            src = write(Path(other), "mod.py", big_python())
            self.assertEqual(self.pre(src)[0], "")

    def test_memory_dir_itself_is_not_intercepted(self):
        src = write(self.root, ".memory/huge.md", "# h\n" + "x" * 50000)
        self.assertEqual(self.pre(src)[0], "")

    def test_binary_passes_through(self):
        src = self.root / "blob.dat"
        src.write_bytes(b"\0\1\2" * 20000)
        self.assertEqual(self.pre(src)[0], "")

    def test_no_outline_means_no_interception(self):
        src = write(self.root, "data.unknownext", "plain text line\n" * 3000)
        self.assertEqual(self.pre(src)[0], "")

    def test_max_bytes_option_and_zero_disables(self):
        src = write(self.root, "mod.py", big_python())
        os.environ["CLAUDE_PLUGIN_OPTION_MAX_BYTES"] = "0"
        self.assertEqual(self.pre(src)[0], "")
        os.environ["CLAUDE_PLUGIN_OPTION_MAX_BYTES"] = str(src.stat().st_size + 1)
        self.assertEqual(self.pre(src)[0], "")

    def test_memory_dir_option(self):
        src = write(self.root, "mod.py", big_python())
        os.environ["CLAUDE_PLUGIN_OPTION_MEMORY_DIR"] = "kb/mem"
        self.assertNotEqual(self.pre(src)[0], "")
        self.assertTrue((self.root / "kb/mem/mod.py.md").is_file())

    def test_same_stem_different_ext_do_not_collide(self):
        a = write(self.root, "app.py", big_python())
        b = write(self.root, "app.js", "\n".join(f"export function f{i}(a) {{\n" + "  return a;\n" * 20 + "}" for i in range(120)))
        self.pre(a), self.pre(b)
        self.assertTrue((self.root / ".memory/app.py.md").is_file())
        self.assertTrue((self.root / ".memory/app.js.md").is_file())

    def test_stale_memory_is_regenerated_and_notes_survive(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        mem = self.root / ".memory/mod.py.md"
        mem.write_text(mem.read_text().replace(
            okf_memory.NOTES_PLACEHOLDER, "# Notes\n\nfunc_3 is the hot path.\n"))
        src.write_text(big_python() + "\ndef added_later():\n    pass\n")
        reason = json.loads(self.pre(src)[0])["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("def added_later()", reason)
        self.assertIn("func_3 is the hot path.", reason)
        self.assertIn("func_3 is the hot path.", mem.read_text())

    def test_fresh_memory_is_served_as_is(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        mem = self.root / ".memory/mod.py.md"
        mem.write_text(mem.read_text() + "\nhand edit\n")
        self.assertIn("hand edit", self.pre(src)[0])

    def test_garbage_input_never_raises(self):
        for payload in ("not json", json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Read",
                                                 "tool_input": {"file_path": 42}})):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err), \
                    unittest.mock.patch("sys.stdin", io.StringIO(payload)):
                okf_memory.main()
            self.assertEqual(out.getvalue(), "")


class PostToolTests(TmpProjectTestCase):
    def test_post_refreshes_existing_memory_after_edit(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        src.write_text(big_python() + "\ndef edited():\n    pass\n")
        self.assertEqual(self.post("Edit", src), ("", ""))
        self.assertIn("def edited()", (self.root / ".memory/mod.py.md").read_text())

    def test_post_never_creates_a_memory(self):
        src = write(self.root, "mod.py", big_python())
        self.post("Write", src)
        self.post("Read", src)
        self.assertFalse((self.root / ".memory").exists())


class OutlineTests(unittest.TestCase):
    def test_python_tree_has_spans_signatures_and_nesting(self):
        _, entries = outline.outline(Path("m.py"), big_python(2))
        text = "\n".join(entries)
        self.assertIn("imports: os, pathlib", text)
        self.assertIn("LIMIT = …", text)
        self.assertRegex(text, r"L\d+-\d+: def func_1\(a: int, b: str='x'\) -> int  # Doc 1\.")
        self.assertRegex(text, r"L\d+-\d+:   def method\(self\)")

    def test_python_syntax_error_falls_back_to_scan(self):
        method, entries = outline.outline(Path("m.py"), "def ok():\n    pass\ndef broken(:\n")
        self.assertIn("declaration scan", method)
        self.assertEqual(len(entries), 2)

    def test_markdown_headings_skip_code_fences(self):
        md = "# Top\n\n```sh\n# not a heading\n```\n\n## Sub\n"
        _, entries = outline.outline(Path("x.md"), md)
        self.assertEqual(entries, ["L1: Top", "L7:   Sub"])

    def test_typescript_scan(self):
        ts = ("export interface Foo {\n  a: number;\n}\n"
              "export const f = async (x: number) => x;\n"
              "class Bar {\n  private baz(x: number): void {\n    if (x) {\n    }\n  }\n}\n")
        _, entries = outline.outline(Path("x.ts"), ts)
        self.assertEqual([e.split(":")[0] for e in entries], ["L1", "L4", "L5", "L6"])

    def test_json_key_tree(self):
        _, entries = outline.outline(Path("x.json"), json.dumps({"a": {"b": [1, 2]}, "c": "s"}))
        self.assertEqual(entries, ["$: object{2}", "  .a: object{1}", "    .a.b: array[2] of int", "  .c: string"])

    def test_minified_has_no_outline(self):
        method, entries = outline.outline(Path("x.js"), "var a=1;" * 2000)
        self.assertTrue(method.startswith("none"))
        self.assertEqual(entries, [])


if __name__ == "__main__":
    unittest.main()
