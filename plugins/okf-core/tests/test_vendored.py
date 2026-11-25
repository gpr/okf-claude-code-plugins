"""Vendored upstream files must stay byte-identical to UPSTREAM.md.

okf-core copies okf-generate, okf-consume, SPEC.md and the upstream license
verbatim from the Open Knowledge Format repository. A local edit would be
silently lost on the next re-sync, so overrides belong in okf-spec's house
rules instead. This test catches such edits, and also new files dropped into
a vendored skill directory without a manifest row.
"""

import hashlib
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
MANIFEST = PLUGIN / "UPSTREAM.md"
VENDORED_DIRS = ["skills/okf-generate", "skills/okf-consume"]
ROW = re.compile(r"^([0-9a-f]{64})  (\S+)  (\S+)$")


def manifest_rows():
    text = MANIFEST.read_text(encoding="utf-8")
    block = text.split("<!-- vendored:begin -->", 1)[1].split("<!-- vendored:end -->", 1)[0]
    rows = {}
    for line in block.strip().splitlines():
        match = ROW.match(line)
        if not match:
            raise AssertionError(f"malformed UPSTREAM.md row: {line!r}")
        rows[match.group(2)] = match.group(1)
    return rows


class VendoredFilesTest(unittest.TestCase):
    def test_manifest_has_rows(self):
        self.assertGreater(len(manifest_rows()), 0)

    def test_hashes_match(self):
        for rel, expected in manifest_rows().items():
            with self.subTest(path=rel):
                path = PLUGIN / rel
                self.assertTrue(path.is_file(), f"{rel} is listed in UPSTREAM.md but missing")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(
                    actual, expected,
                    f"{rel} differs from upstream; don't edit vendored files "
                    "(put overrides in skills/okf-spec/SKILL.md) or re-sync and "
                    "update UPSTREAM.md",
                )

    def test_every_vendored_file_is_listed(self):
        rows = manifest_rows()
        for directory in VENDORED_DIRS:
            for path in sorted((PLUGIN / directory).rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    rel = path.relative_to(PLUGIN).as_posix()
                    with self.subTest(path=rel):
                        self.assertIn(rel, rows, f"{rel} is not listed in UPSTREAM.md")


class SpecIndexTest(unittest.TestCase):
    """okf-spec's section -> line index must point at SPEC.md's headings."""

    INDEX_ROW = re.compile(r"^\| (\d+)–(\d+) \| (§\d+|Appendix [A-Z])\b")

    def test_line_index_matches_spec_headings(self):
        skill = (PLUGIN / "skills/okf-spec/SKILL.md").read_text(encoding="utf-8")
        spec = (PLUGIN / "skills/okf-spec/references/SPEC.md").read_text(encoding="utf-8").splitlines()
        rows = [m for m in map(self.INDEX_ROW.match, skill.splitlines()) if m]
        self.assertGreater(len(rows), 10)
        for match in rows:
            start, end, label = int(match.group(1)), int(match.group(2)), match.group(3)
            with self.subTest(section=label):
                heading = spec[start - 1]
                expected = label[1:] + "." if label.startswith("§") else label
                self.assertTrue(
                    heading.startswith("## ") and heading[3:].startswith(expected),
                    f"line {start} of SPEC.md is {heading!r}, not {label}; update the index in okf-spec/SKILL.md",
                )
                self.assertLessEqual(end, len(spec))
        # Each range ends where the next one starts; the last ends at EOF.
        bounds = [(int(m.group(1)), int(m.group(2)), m.group(3)) for m in rows]
        for (_, end, label), (next_start, _, _) in zip(bounds, bounds[1:]):
            with self.subTest(section=label, check="end"):
                self.assertEqual(end + 1, next_start,
                                 f"{label} ends at {end} but the next section starts at {next_start}")
        self.assertEqual(bounds[-1][1], len(spec), "the last indexed section must end at the last line of SPEC.md")


if __name__ == "__main__":
    unittest.main()
