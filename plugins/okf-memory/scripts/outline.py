"""Structural outline of a source file.

Strategies, best first:

  * Python: the stdlib `ast` - classes, functions and methods with
    signatures, line ranges and first docstring line.
  * Markdown / JSON: heading tree / key tree.
  * Other code: tree-sitter, through the optional `tree-sitter-language-pack`
    package (`structure` extraction: kind, name, signature, line span,
    nesting). Used only when the package imports AND the language's grammar
    is already in its local cache: `get_parser`/`process` download a missing
    grammar over the network, and hooks never touch the network. Grammars are
    fetched by `bin/okf-memory-setup`, an explicit user step.
  * Fallback: a regex declaration scan - lines matching per-language
    declaration patterns, kept with their indentation. Not a parse tree, and
    the outline says so.

Every entry carries a 1-based line number, because the point of the outline is
to let the reader follow up with a ranged `Read` (offset/limit) instead of
reading the whole file.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

MAX_ENTRIES = 400
MAX_LINE = 160
MINIFIED_AVG_LINE = 400

_KW = re.IGNORECASE

# Declaration patterns, matched against each raw line.
_JS = [
    r"^\s*(export\s+)?(default\s+)?(async\s+)?function\b",
    r"^\s*(export\s+)?(default\s+)?(abstract\s+)?class\s+\w+",
    r"^\s*(export\s+)?(declare\s+)?(interface|type|enum|namespace)\s+\w+",
    r"^\s*(export\s+)?(const|let|var)\s+\w+\s*(:[^=]+)?=\s*(async\s+)?(function\b|\([^)]*\)\s*(:[^=]+)?=>|\w+\s*=>)",
    r"^\s+(public\s+|private\s+|protected\s+|static\s+|readonly\s+|async\s+|get\s+|set\s+)*"
    r"(?!(if|for|while|switch|catch|return|function)\b)[A-Za-z_$][\w$]*\s*\([^;]*\)\s*(:\s*[^{;]+)?\{\s*$",
    r"^\s*export\s+(default\s+)?\{",
]
_MODIFIERS = r"((public|private|protected|internal|static|final|abstract|sealed|open|override|data|async|virtual|partial|suspend|inline|export|pub(\([^)]*\))?)\s+)*"
LANGS: dict[str, tuple[str, list[str], int]] = {
    # ext -> (language, patterns, regex flags)
    "js": ("JavaScript", _JS, 0),
    "jsx": ("JavaScript", _JS, 0),
    "mjs": ("JavaScript", _JS, 0),
    "cjs": ("JavaScript", _JS, 0),
    "ts": ("TypeScript", _JS, 0),
    "tsx": ("TypeScript", _JS, 0),
    "go": ("Go", [r"^func\b", r"^type\s+\w+", r"^(var|const)\s"], 0),
    "rs": ("Rust", [
        r"^\s*(pub(\([^)]*\))?\s+)?(async\s+)?(unsafe\s+)?(const\s+)?(extern\s+\"[^\"]*\"\s+)?"
        r"(fn|struct|enum|trait|impl|mod|type|union|macro_rules!)\b",
        r"^(pub(\([^)]*\))?\s+)?(const|static)\s+[A-Z_]",
    ], 0),
    "java": ("Java", [
        _MODIFIERS + r"(class|interface|enum|record|@interface)\s+\w+",
        r"^\s+" + _MODIFIERS + r"[\w<>\[\],.?\s]+\s+\w+\s*\([^;]*$",
    ], 0),
    "kt": ("Kotlin", [_MODIFIERS + r"(class|interface|object|enum\s+class|fun|typealias)\b"], 0),
    "scala": ("Scala", [_MODIFIERS + r"(class|trait|object|def|case\s+class|type)\s+\w+"], 0),
    "swift": ("Swift", [_MODIFIERS + r"(class|struct|enum|protocol|extension|func|actor)\s+\w+"], 0),
    "cs": ("C#", [
        _MODIFIERS + r"(class|interface|struct|enum|record|namespace)\s+\w+",
        r"^\s+" + _MODIFIERS + r"[\w<>\[\],.?\s]+\s+\w+\s*\([^;]*$",
    ], 0),
    "c": ("C", [
        r"^(struct|enum|union|typedef)\b",
        r"^#define\s+\w+",
        r"^(?!(if|for|while|switch|return|else)\b)[A-Za-z_][\w\s\*]*\**\b[A-Za-z_]\w*\s*\([^;]*$",
    ], 0),
    "h": ("C/C++ header", [
        r"^(struct|enum|union|typedef|class|namespace|template)\b",
        r"^#define\s+\w+",
        r"^(?!(if|for|while|switch|return|else)\b)[A-Za-z_][\w\s\*&:<>,]*\b[A-Za-z_~][\w:~]*\s*\([^;]*\)?\s*;?\s*$",
    ], 0),
    "cpp": ("C++", [
        r"^\s*(struct|enum|union|typedef|class|namespace|template)\b",
        r"^#define\s+\w+",
        r"^(?!(if|for|while|switch|return|else)\b)[A-Za-z_][\w\s\*&:<>,]*\b[A-Za-z_~][\w:~]*\s*\([^;]*$",
    ], 0),
    "rb": ("Ruby", [r"^\s*(class|module|def)\s"], 0),
    "php": ("PHP", [r"^\s*" + _MODIFIERS + r"(function|class|interface|trait|enum)\s+\w+"], 0),
    "sh": ("Shell", [r"^\s*(function\s+[\w-]+|[\w-]+\s*\(\)\s*\{?)"], 0),
    "sql": ("SQL", [
        r"^\s*(create|alter)\s+(or\s+replace\s+)?(temp(orary)?\s+)?"
        r"(table|view|materialized\s+view|function|procedure|index|unique\s+index|trigger|type|schema)\b",
    ], _KW),
    "css": ("CSS", [r"^[^\s@}/][^{]*\{", r"^@(media|supports|layer|keyframes)\b"], 0),
    "yaml": ("YAML", [r"^[A-Za-z_\"'][^:#]*:(\s|$)", r"^  [A-Za-z_\"'][^:#]*:(\s|$)"], 0),
    "toml": ("TOML", [r"^\s*\[.*\]\s*$", r"^[A-Za-z_][\w.-]*\s*="], 0),
    "ini": ("INI", [r"^\s*\[.*\]\s*$"], 0),
}
_ALIASES = {"cc": "cpp", "cxx": "cpp", "hpp": "h", "hh": "h", "kts": "kt", "bash": "sh",
            "zsh": "sh", "scss": "css", "less": "css", "yml": "yaml", "cfg": "ini"}


def language(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    ext = _ALIASES.get(ext, ext)
    if ext == "py" or ext == "pyi":
        return "Python"
    if ext in ("md", "markdown"):
        return "Markdown"
    if ext == "json":
        return "JSON"
    return LANGS[ext][0] if ext in LANGS else "text"


def outline(path: Path, text: str) -> tuple[str, list[str]]:
    """Return (method, entries). `method` names how the outline was built."""
    lines = text.splitlines()
    if lines and len(text) / len(lines) > MINIFIED_AVG_LINE:
        return "none (minified or single-line content)", []
    ext = path.suffix.lower().lstrip(".")
    ext = _ALIASES.get(ext, ext)
    if ext in ("py", "pyi"):
        try:
            return "syntax tree (Python ast)", _python(ast.parse(text))
        except (SyntaxError, ValueError, RecursionError):
            pass  # fall through to the declaration scan
        return "declaration scan (Python did not parse)", _scan(
            lines, [r"^\s*(async\s+)?def\s", r"^\s*class\s"], 0)
    if ext in ("md", "markdown"):
        return "heading tree", _markdown(lines)
    if ext == "json":
        try:
            return "key tree (no line numbers: JSON)", _json(json.loads(text))
        except ValueError:
            return "none (invalid JSON)", []
    ts_lang, entries = _tree_sitter(path, text)
    if entries:
        return f"syntax tree (tree-sitter, {ts_lang})", entries
    if ext in LANGS:
        _, patterns, flags = LANGS[ext]
        return "declaration scan (regex, not a parse tree)", _scan(lines, patterns, flags)
    return "none (unknown language)", []


def deps_dir() -> Path:
    """Where `bin/okf-memory-setup` installs optional packages."""
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "okf-memory" / "pylib"


def _language_pack():
    """The tree-sitter language pack module, or None when it is not installed."""
    extra = str(deps_dir())
    if os.path.isdir(extra) and extra not in sys.path:
        sys.path.insert(0, extra)
    try:
        import tree_sitter_language_pack as pack
    except Exception:  # ImportError, or a broken native build
        return None
    return pack


def _tree_sitter(path: Path, text: str) -> tuple[str | None, list[str]]:
    """Outline via tree-sitter, or (None, []) when unavailable for this file."""
    pack = _language_pack()
    if pack is None:
        return None, []
    try:
        lang = pack.detect_language_from_path(str(path))
        # Gate on the local cache: process() would download a missing grammar.
        if not lang or lang not in pack.downloaded_languages():
            return None, []
        result = pack.process(text, pack.ProcessConfig(language=lang, structure=True))
    except Exception:
        return None, []
    out: list[str] = []
    _ts_items(result.structure, 0, out)
    return lang, out


def _ts_items(items, depth: int, out: list[str]) -> None:
    for item in items:
        if len(out) > MAX_ENTRIES:
            return
        span = item.span
        start, end = span.start_line + 1, span.end_line + 1  # tree-sitter rows are 0-based
        where = f"L{start}-{end}" if end != start else f"L{start}"
        kind = str(getattr(item.kind, "type", item.kind)).lower()
        sig = " ".join((item.signature or item.name or "").split())
        label = sig if sig and (item.name or "") in sig else f"{kind} {item.name or sig}".strip()
        doc = (item.doc_comment or "").strip()
        doc = f"  # {_clip(doc.splitlines()[0].strip('/* '))}" if doc else ""
        out.append(f"{where}: {'  ' * depth}{_clip(label)}{doc}")
        if depth < 3:
            _ts_items(item.children, depth + 1, out)


def _clip(s: str) -> str:
    s = s.rstrip()
    return s if len(s) <= MAX_LINE else s[: MAX_LINE - 1] + "…"


def _scan(lines: list[str], patterns: list[str], flags: int) -> list[str]:
    rx = re.compile("|".join(f"(?:{p})" for p in patterns), flags)
    out = []
    for n, line in enumerate(lines, 1):
        if rx.match(line):
            out.append(f"L{n}: {_clip(line.expandtabs(4))}")
    return out


def _markdown(lines: list[str]) -> list[str]:
    out, fence = [], None
    for n, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else (fence or marker)
            continue
        if fence is None:
            m = re.match(r"^(#{1,6})\s+(.*)", line)
            if m:
                depth = len(m.group(1)) - 1
                out.append(f"L{n}: {'  ' * depth}{_clip(m.group(2))}")
    return out


def _json(data, prefix: str = "", depth: int = 0) -> list[str]:
    def kind(v) -> str:
        if isinstance(v, dict):
            return f"object{{{len(v)}}}"
        if isinstance(v, list):
            inner = f" of {kind(v[0])}" if v else ""
            return f"array[{len(v)}]{inner}"
        return type(v).__name__.replace("NoneType", "null").replace("str", "string")

    out = [f"{prefix or '$'}: {kind(data)}"] if depth == 0 else []
    if depth >= 3:
        return out
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data, prefix = data[0], prefix + "[0]"
    if isinstance(data, dict):
        for k, v in data.items():
            path = f"{prefix}.{k}"
            out.append(f"{'  ' * (depth + 1)}{path}: {kind(v)}")
            out.extend(_json(v, path, depth + 1))
    return out


def _doc(node) -> str:
    doc = ast.get_docstring(node, clean=True)
    return f"  # {_clip(doc.strip().splitlines()[0])}" if doc and doc.strip() else ""


def _sig(node) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return _clip(f"{prefix} {node.name}({ast.unparse(node.args)}){ret}")


def _span(node) -> str:
    end = getattr(node, "end_lineno", None) or node.lineno
    start = node.decorator_list[0].lineno if getattr(node, "decorator_list", None) else node.lineno
    return f"L{start}-{end}" if end != start else f"L{start}"


def _python(tree: ast.Module) -> list[str]:
    out: list[str] = []
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append("." * node.level + (node.module or ""))
    if imports:
        out.append("imports: " + _clip(", ".join(dict.fromkeys(imports))))
    _python_body(tree.body, 0, out)
    return out


def _python_body(body: list, depth: int, out: list[str]) -> None:
    pad = "  " * depth
    for node in body:
        if isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in node.bases)
            out.append(f"{_span(node)}: {pad}class {node.name}({bases}){_doc(node)}")
            if depth < 2:
                _python_body(node.body, depth + 1, out)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(f"{_span(node)}: {pad}{_sig(node)}{_doc(node)}")
        elif depth == 0 and isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if names:
                out.append(f"{_span(node)}: {', '.join(names)} = …")
        elif depth == 0 and isinstance(node, ast.If) and "__main__" in ast.unparse(node.test):
            out.append(f"{_span(node)}: if __name__ == '__main__'")
