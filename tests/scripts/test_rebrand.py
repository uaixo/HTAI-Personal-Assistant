"""Contracts for scripts/rebrand.py: literals are branded, docstrings, comments, identifiers and kept
lines are not, and the rewrite is idempotent."""

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("rebrand", REPO_ROOT / "scripts" / "rebrand.py")
rebrand = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rebrand)

from hermes_brand import AGENT_NAME, SYMBOL

PY_SOURCE = '''"""Module docstring about Hermes Agent stays."""
# a comment about Hermes stays
LABEL = "☤ Hermes"
PATH = "~/.hermes/config.yaml"
HEADER = {"X-Hermes-Token": "Hermes Agent"}
MSG = f"Hermes Agent v{VERSION} ({DATE})"  # trailing comment: Hermes
KEEP = "Hermes Agent"  # rebrand: keep
# rebrand: keep
NEXT = "Hermes"
# rebrand: keep-start
BLOCK = ("Hermes Agent",
         "Hermes")
# rebrand: keep-end


def f():
    """Docstring: Hermes."""
    return "Hermes is working"
'''


def test_python_literals_are_branded_but_docstrings_comments_and_kept_lines_are_not():
    out = rebrand.rebrand_python(PY_SOURCE)
    assert '"""Module docstring about Hermes Agent stays."""' in out
    assert "# a comment about Hermes stays" in out
    assert f'LABEL = "{SYMBOL} {AGENT_NAME}"' in out
    assert 'PATH = "~/.hermes/config.yaml"' in out
    assert f'HEADER = {{"X-Hermes-Token": "{AGENT_NAME}"}}' in out
    assert f'MSG = f"{AGENT_NAME} v{{VERSION}} ({{DATE}})"  # trailing comment: Hermes' in out
    assert 'KEEP = "Hermes Agent"  # rebrand: keep' in out
    assert 'NEXT = "Hermes"' in out
    assert 'BLOCK = ("Hermes Agent",\n         "Hermes")' in out
    assert '"""Docstring: Hermes."""' in out
    assert f'return "{AGENT_NAME} is working"' in out
    assert rebrand.rebrand_python(out) == out


def test_line_mode_skips_comment_lines_and_kept_blocks():
    text = "# Hermes Agent in a comment\nName=Hermes\nComment=Launch Hermes Desktop # Hermes\n# rebrand: keep\nX=Hermes\n"
    out = rebrand.rebrand_lines(text, "#")
    assert out == f"# Hermes Agent in a comment\nName={AGENT_NAME}\nComment=Launch {AGENT_NAME} Desktop # {AGENT_NAME}\n# rebrand: keep\nX=Hermes\n"
    assert rebrand.rebrand_lines("Hermes 4 and Hermes-4-405B stay", None) == "Hermes 4 and Hermes-4-405B stay"


@pytest.mark.parametrize(("path", "included"), [
    ("hermes_cli/banner.py", True),
    ("website/docs/index.md", True),
    ("apps/desktop/electron/main.ts", True),
    ("apps/desktop/src/i18n/en.ts", False),
    ("apps/desktop/src/i18n/de_boot.ts", False),
    ("apps/desktop/src/i18n/context.tsx", True),
    ("web/src/i18n/fr.ts", False),
    ("ui-tui/src/i18n/en/app.ts", False),
    ("locales/en.yaml", False),
    ("plugin-catalog/foo/card.json", False),
    ("website/src/data/userStories.json", False),
    ("assets/banner.png", False),
    ("uv.lock", False),
    ("hermes_brand.py", False),
])
def test_inclusion_rules(path, included):
    assert rebrand.is_included(path) is included


@pytest.mark.skipif(shutil.which("node") is None or not (REPO_ROOT / "node_modules" / "typescript").is_dir(),
                    reason="needs Node and the repo's typescript")
def test_typescript_literals_are_branded_through_the_compiler(tmp_path, monkeypatch):
    source = tmp_path / "sample.tsx"
    source.write_text(
        "// Hermes in a comment\nimport { x } from './hermes'\n"
        "const a = 'Hermes Agent'\nconst b = `Hermes can use ${x}`\n"
        "const c = <p title=\"Hermes\">Ask Hermes about Hermes 4</p>\n"
        "const d = 'Hermes' // rebrand: keep\n", encoding="utf-8")
    monkeypatch.setattr(rebrand, "REPO_ROOT", tmp_path)
    changed = rebrand.rebrand_typescript([str(source)], write=True)
    assert changed == [str(source)]
    out = source.read_text(encoding="utf-8")
    assert "// Hermes in a comment" in out and "from './hermes'" in out
    assert f"const a = '{AGENT_NAME}'" in out
    assert f"const b = `{AGENT_NAME} can use ${{x}}`" in out
    assert f"<p title=\"{AGENT_NAME}\">Ask {AGENT_NAME} about Hermes 4</p>" in out
    assert "const d = 'Hermes' // rebrand: keep" in out
    assert rebrand.rebrand_typescript([str(source)], write=False) == []


def test_python_rewrite_that_would_not_parse_is_skipped(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rebrand, "REPO_ROOT", tmp_path)
    (tmp_path / "broken.py").write_text("x = 'Hermes' as\n", encoding="utf-8")
    assert rebrand._rewrite("broken.py", rebrand.rebrand_python, write=True) is False
    assert "skipped broken.py" in capsys.readouterr().err


def test_main_check_mode_reports_without_writing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rebrand, "tracked_files", lambda paths: ["sample.md"])
    monkeypatch.setattr(rebrand, "REPO_ROOT", tmp_path)
    (tmp_path / "sample.md").write_text("# Hermes Agent\n", encoding="utf-8")
    assert rebrand.main(["--check"]) == 1
    assert (tmp_path / "sample.md").read_text(encoding="utf-8") == "# Hermes Agent\n"
    assert rebrand.main([]) == 0
    assert (tmp_path / "sample.md").read_text(encoding="utf-8") == f"# {AGENT_NAME}\n"
    assert rebrand.main(["--check"]) == 0
    assert "sample.md" in capsys.readouterr().out
