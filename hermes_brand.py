"""Product brand for user-facing text: the one place the product name lives.

``AGENT_NAME`` is what a person reads in the CLI, TUI, desktop app, dashboard, messaging replies and
docs. Internal identifiers are NOT brand and keep their upstream names so merges from upstream stay
cheap: the ``hermes`` command, ``HERMES_*`` environment variables, ``~/.hermes``, the ``hermes_*``
modules, ``hermes://`` links, HTTP headers and API object names.

How the brand reaches the surfaces:

- catalogs are branded as they load — ``agent.i18n_layers.flatten`` (every ``locales/*.yaml`` layer,
  packs and overlays included) and ``apps/shared/src/brand.ts`` (the bundled TypeScript catalogs);
- string literals in source, docs, skills and packaging metadata are branded at rest by
  ``scripts/rebrand.py``, which applies the same :func:`brand_text` rule and is idempotent, so it is
  re-run after every merge from upstream.

Import-safe, stdlib-only — importable from anywhere (the ``hermes_constants`` convention).
"""

from __future__ import annotations

import re

AGENT_NAME = "NousAI"
VENDOR = "Nous Research"
# Glyph that marks the agent in response labels and short notices (the upstream caduceus ``☤``).
SYMBOL = "✦"

# The upstream product names as they appear in prose, bounded on both sides so identifiers stay
# untouched: ``hermes_cli`` (lowercase), ``HERMES_HOME`` (uppercase), ``X-Hermes-Token`` and
# ``Hermes-Setup.exe`` (hyphenated), ``NousResearch.Hermes`` (dotted), ``OpenHermes``/``HermesCLI``
# (joined) — and the Hermes model family (``Hermes 4``, ``Hermes 3 & 4``, ``Hermes-3-Llama``).
# ``Hermes.app`` / ``Hermes.exe`` ARE renamed: the desktop bundle is named after the product.
_LEGACY_BRAND = re.compile(r"(?<![A-Za-z0-9_.\-])Hermes(?: Agent)?(?![A-Za-z0-9_\-])(?! \d)")
# ``Hermes' tool store`` -> ``NousAI's tool store``: a bare-apostrophe possessive reads as a typo on a
# name that does not end in s. Only a word-bounded name followed by ``' <word>`` qualifies, so the
# closing quote of ``'Hermes'`` (opened by the quote before the name) is never mistaken for one.
_LEGACY_POSSESSIVE = re.compile(r"(?<![A-Za-z0-9_.\-'’])Hermes(?: Agent)?(?P<apostrophe>['’])(?= [A-Za-z])")
_LEGACY_SYMBOL = "☤"


def _possessive(match: re.Match[str]) -> str:
    """``NousAI's`` for a possessive; untouched when the apostrophe closes a quote opened earlier on
    the line (``'Run Hermes' now``), which the brand rule then handles as a plain name."""
    text, start, apostrophe = match.string, match.start(), match.group("apostrophe")
    line_start = text.rfind("\n", 0, start) + 1
    if text.count(apostrophe, line_start, start) % 2:
        return match.group(0)
    return f"{AGENT_NAME}{apostrophe}s"


def brand_text(text: str) -> str:
    """``text`` with every upstream product name and glyph replaced by the brand. Idempotent."""
    text = _LEGACY_POSSESSIVE.sub(_possessive, text)
    return _LEGACY_BRAND.sub(AGENT_NAME, text).replace(_LEGACY_SYMBOL, SYMBOL)


__all__ = ["AGENT_NAME", "SYMBOL", "VENDOR", "brand_text"]
