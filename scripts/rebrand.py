#!/usr/bin/env python3
"""Brand string literals at rest, idempotently — the overlay that keeps this fork mergeable.

Only text a person reads changes. Identifiers keep their upstream spelling (the ``hermes`` command,
``HERMES_*`` variables, ``hermes_*`` modules, HTTP headers, URLs, the Hermes model family), so a merge
from upstream touches the lines it always did and one run of this script re-brands whatever the merge
brought in. Catalogs are never rewritten: ``locales/*.yaml`` and the bundled TypeScript catalogs are
branded as they load (see ``hermes_brand``), which keeps them byte-identical to upstream.

    python scripts/rebrand.py              # brand every tracked file
    python scripts/rebrand.py --check      # list files still carrying the upstream brand; exit 1 if any
    python scripts/rebrand.py PATH ...     # only these files / directories

Python: string constants (never docstrings), located with ``ast``. TypeScript / JavaScript: string and
template literals and JSX text, located with the TypeScript compiler (``scripts/rebrand_ts.mjs``).
Everything else (Markdown, YAML, shell, PowerShell, Nix, Rust, JSON, HTML, plists): line by line,
skipping comment lines where the language has them. A line that carries ``rebrand: keep``, the line
after such a comment, or a ``rebrand: keep-start`` … ``rebrand: keep-end`` block is left alone.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from hermes_brand import AGENT_NAME, SYMBOL, _LEGACY_BRAND, _LEGACY_SYMBOL, brand_text

KEEP_MARKER = "rebrand: keep"

PY_EXTENSIONS = {".py"}
TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}
HASH_COMMENT_EXTENSIONS = {".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1", ".nix", ".yml", ".yaml", ".toml",
                           ".cfg", ".ini", ".conf", ".service", ".desktop", ".dockerfile"}
SLASH_COMMENT_EXTENSIONS = {".rs", ".swift", ".kt", ".java", ".c", ".h", ".cpp", ".hpp", ".m", ".mm"}
PLAIN_EXTENSIONS = {".md", ".mdx", ".html", ".txt", ".json", ".plist", ".manifest", ".xml", ".css", ".rst"}
HASH_COMMENT_NAMES = {"Dockerfile", "activate"}

# Never rewritten: third-party and personal content, lockfiles, the catalogs (branded at load),
# the OAuth client registration upstream publishes under its own client_id URL, and the brand
# machinery itself (its inputs ARE the upstream names). The published model catalog under
# website/static/api/ IS rewritten: a test holds it to the branded build script's output.
EXCLUDED_PREFIXES = ("plugin-catalog/", "contributors/", "locales/", "ui-tui/src/i18n/en/",
                     "website/static/oauth/", "apps/desktop/pr-assets/")
EXCLUDED_FILES = {
    "hermes_brand.py", "scripts/rebrand.py", "scripts/rebrand_ts.mjs", "tests/test_hermes_brand.py",
    "tests/scripts/test_rebrand.py", "apps/shared/src/brand.ts", "apps/shared/src/brand.test.ts",
    "ui-tui/src/i18n/en.ts", "website/src/data/userStories.json", "uv.lock", "flake.lock",
}
EXCLUDED_PATTERNS = (
    re.compile(r"(^|/)package-lock\.json$"),
    re.compile(r"^apps/desktop/src/i18n/[a-z]{2}(-[a-z]+)?(_[a-z_]+)?\.ts$"),
    re.compile(r"^web/src/i18n/[a-z]{2}(-[a-z]+)?\.ts$"),
)


def is_included(path: str) -> bool:
    """True when ``path`` (repo-relative, POSIX) is a text file this script may rewrite."""
    if path in EXCLUDED_FILES or path.startswith(EXCLUDED_PREFIXES):
        return False
    if any(pattern.search(path) for pattern in EXCLUDED_PATTERNS):
        return False
    return handler_for(path) is not None


def kept_lines(lines: list[str]) -> set[int]:
    """0-based indexes of lines a ``rebrand: keep`` marker protects: the marker line, the line after
    it, and everything inside a ``keep-start`` … ``keep-end`` block."""
    kept: set[int] = set()
    in_block = False
    for index, line in enumerate(lines):
        if f"{KEEP_MARKER}-start" in line:
            in_block = True
        if in_block or KEEP_MARKER in line:
            kept.add(index)
            if KEEP_MARKER in line:
                kept.add(index + 1)
        if f"{KEEP_MARKER}-end" in line:
            in_block = False
    return kept


def rebrand_lines(text: str, comment_prefix: str | None = None) -> str:
    """Line-by-line branding; lines starting with ``comment_prefix`` and kept lines pass through."""
    lines = text.split("\n")
    kept = kept_lines(lines)
    out = []
    for index, line in enumerate(lines):
        skip = index in kept or (comment_prefix is not None and line.lstrip().startswith(comment_prefix))
        out.append(line if skip else brand_text(line))
    return "\n".join(out)


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                ids.add(id(first.value))
    return ids


def rebrand_python(text: str) -> str:
    """Brand every str and bytes constant except docstrings and kept lines; comments are never touched."""
    tree = ast.parse(text)
    kept = kept_lines(text.split("\n"))
    docstrings = _docstring_ids(tree)
    data = text.encode("utf-8")
    line_starts = [0]
    for line in data.split(b"\n")[:-1]:
        line_starts.append(line_starts[-1] + len(line) + 1)
    spans: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))):
            continue
        if id(node) in docstrings or node.end_lineno is None or node.end_col_offset is None:
            continue
        if node.lineno - 1 in kept:
            continue
        spans.add((line_starts[node.lineno - 1] + node.col_offset,
                   line_starts[node.end_lineno - 1] + node.end_col_offset))
    for start, end in sorted(spans, reverse=True):
        data = data[:start] + brand_text(data[start:end].decode("utf-8")).encode("utf-8") + data[end:]
    result = data.decode("utf-8")
    ast.parse(result)  # the rewrite must leave valid Python behind
    return result


def rebrand_typescript(paths: list[str], *, write: bool) -> list[str]:
    """Brand TS/JS literals through the TypeScript compiler; falls back to line mode without Node."""
    if not paths:
        return []
    node = shutil.which("node")
    payload = {"files": paths, "pattern": _LEGACY_BRAND.pattern, "agentName": AGENT_NAME,
               "legacySymbol": _LEGACY_SYMBOL, "symbol": SYMBOL, "keepMarker": KEEP_MARKER, "write": write}
    if node is not None:
        proc = subprocess.run([node, str(SCRIPTS_DIR / "rebrand_ts.mjs")], input=json.dumps(payload),
                              capture_output=True, text=True, encoding="utf-8", cwd=REPO_ROOT, timeout=900,
                              check=False)
        if proc.returncode == 0:
            return proc.stdout.split()
        if proc.returncode != 3:
            raise RuntimeError(f"rebrand_ts.mjs failed:\n{proc.stderr}")
    print("note: Node + typescript unavailable, branding TS/JS line by line", file=sys.stderr)
    return [path for path in paths if _rewrite(path, lambda text: rebrand_lines(text, "//"), write=write)]


def handler_for(path: str) -> Callable[[str], str] | str | None:
    """The transform for ``path``: a text function, the string ``"ts"`` for the Node batch, or None."""
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if suffix in PY_EXTENSIONS:
        return rebrand_python
    if suffix in TS_EXTENSIONS:
        return "ts"
    if suffix in HASH_COMMENT_EXTENSIONS or name in HASH_COMMENT_NAMES or name.endswith(".Dockerfile"):
        return lambda text: rebrand_lines(text, "#")
    if suffix in SLASH_COMMENT_EXTENSIONS:
        return lambda text: rebrand_lines(text, "//")
    if suffix in PLAIN_EXTENSIONS:
        return rebrand_lines
    return None


def _rewrite(path: str, transform: Callable[[str], str], *, write: bool) -> bool:
    file = REPO_ROOT / path
    try:
        text = file.read_text(encoding="utf-8", newline="")  # windows-footgun: ok (round-trips a BOM as-is)
    except UnicodeDecodeError:
        return False
    try:
        new = transform(text)
    except SyntaxError as exc:  # not parseable before, or not valid after: leave it for a human
        print(f"skipped {path}: {exc}", file=sys.stderr)
        return False
    if new == text:
        return False
    if write:
        with file.open("w", encoding="utf-8", newline="") as handle:
            handle.write(new)
    return True


def tracked_files(paths: Iterable[str]) -> list[str]:
    proc = subprocess.run(["git", "ls-files", "-z", "--", *paths], capture_output=True, cwd=REPO_ROOT,
                          check=True, timeout=120)
    return [entry.decode("utf-8") for entry in proc.stdout.split(b"\0") if entry]


def run(paths: Iterable[str], *, write: bool) -> list[str]:
    """Brand the tracked files under ``paths``; returns the files that changed (or would change)."""
    changed: list[str] = []
    ts_batch: list[str] = []
    for path in tracked_files(paths):
        if not is_included(path):
            continue
        handler = handler_for(path)
        if handler == "ts":
            ts_batch.append(path)
        elif callable(handler) and _rewrite(path, handler, write=write):
            changed.append(path)
    changed.extend(rebrand_typescript(ts_batch, write=write))
    return sorted(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", default=["."], help="files or directories (default: the whole tree)")
    parser.add_argument("--check", action="store_true", help="report instead of rewriting; exit 1 when anything changes")
    args = parser.parse_args(argv)
    changed = run(args.paths, write=not args.check)
    if args.check:
        for path in changed:
            print(path)
    verb = "still carry the upstream brand" if args.check else "rebranded"
    print(f"{len(changed)} file(s) {verb}", file=sys.stderr)
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
