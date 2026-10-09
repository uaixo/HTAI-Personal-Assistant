"""An install made before the rebrand carries upstream's auto-seeded SOUL.md; it upgrades in place to
the branded default, while a user-edited persona is never touched."""

import os
from unittest.mock import patch

from hermes_cli.config import ensure_hermes_home
from hermes_cli.default_soul import DEFAULT_SOUL_MD, is_legacy_template_soul

# What upstream auto-seeds today (keep its spelling: this is what older installs wrote to disk).
# rebrand: keep-start
_UPSTREAM_DEFAULT_SOUL = (
    "You are Hermes Agent, built by Nous Research. Be direct: match the length of your reply to the "
    "weight of the ask \u2014 a one-line question gets a one-line answer, and finished work gets a short "
    "report of what changed, what's verified, and what's left, never a replay of the process. No filler "
    "(\"Great question,\" \"I'd be happy to\"), no restating the request back, no re-summarizing what you "
    "already said, no narrating tool calls the user can see. Plain claims over adjectives; when unsure, "
    "say so plainly. Agree because it's right, not because the user said it. Depth is earned \u2014 give "
    "it when the user asks for detail, teaches, or the stakes demand it, not by default."
)
# rebrand: keep-end


def test_the_branded_default_differs_from_upstream_and_is_not_itself_legacy():
    assert _UPSTREAM_DEFAULT_SOUL != DEFAULT_SOUL_MD
    assert is_legacy_template_soul(_UPSTREAM_DEFAULT_SOUL)
    assert is_legacy_template_soul(_UPSTREAM_DEFAULT_SOUL.replace("\u2014", "--"))
    assert not is_legacy_template_soul(_UPSTREAM_DEFAULT_SOUL + " Always answer in rhyming couplets.")


def test_upstream_default_soul_md_upgrades_to_the_branded_default(tmp_path):
    with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
        soul_path = tmp_path / "SOUL.md"
        soul_path.write_text(_UPSTREAM_DEFAULT_SOUL, encoding="utf-8")
        ensure_hermes_home()
        assert soul_path.read_text(encoding="utf-8") == DEFAULT_SOUL_MD


def test_user_edited_upstream_default_is_left_alone(tmp_path):
    customized = _UPSTREAM_DEFAULT_SOUL + " Always answer in rhyming couplets."
    with patch.dict(os.environ, {"HERMES_HOME": str(tmp_path)}):
        soul_path = tmp_path / "SOUL.md"
        soul_path.write_text(customized, encoding="utf-8")
        ensure_hermes_home()
        assert soul_path.read_text(encoding="utf-8") == customized
