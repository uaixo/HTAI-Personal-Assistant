"""Contracts for the product brand: which text carries it, which identifiers never do, and that every
catalog layer serves branded text while the shipped YAML stays upstream-identical."""

import pytest

from agent import i18n, i18n_layers
from hermes_brand import AGENT_NAME, SYMBOL, VENDOR, brand_text

_LEGACY = ("Hermes Agent", "Hermes", "☤")


@pytest.mark.parametrize(("text", "expected"), [
    ("Welcome to Hermes Agent!", f"Welcome to {AGENT_NAME}!"),
    ("Hermes is working on 2 chats.", f"{AGENT_NAME} is working on 2 chats."),
    ("You are Hermes Agent, built by Nous Research.", f"You are {AGENT_NAME}, built by {VENDOR}."),
    ("Hermes' tool store, Hermes's home, (Hermes)", f"{AGENT_NAME}' tool store, {AGENT_NAME}'s home, ({AGENT_NAME})"),
    ("Hermes Desktop / Hermes Cloud / Hermes Light", f"{AGENT_NAME} Desktop / {AGENT_NAME} Cloud / {AGENT_NAME} Light"),
    ("/Applications/Hermes.app and Hermes.exe", f"/Applications/{AGENT_NAME}.app and {AGENT_NAME}.exe"),
    ("☤ Starting Hermes update…", f"{SYMBOL} Starting {AGENT_NAME} update…"),
    ("Hermes Agent v0.18.2 (abc123)", f"{AGENT_NAME} v0.18.2 (abc123)"),
    ("See 「Hermes」 and 【Hermes Agent】", f"See 「{AGENT_NAME}」 and 【{AGENT_NAME}】"),
])
def test_brand_text_replaces_the_product_name_in_prose(text, expected):
    assert brand_text(text) == expected


@pytest.mark.parametrize("text", [
    "hermes doctor", "~/.hermes/config.yaml", "HERMES_HOME", "hermes_cli.main", "hermes://open",
    "X-Hermes-Session-Token", "Hermes-Setup.exe", "Hermes-4-405B", "NousResearch.Hermes",
    "OpenHermes-2.5", "DeepHermes", "HermesCLI", "HermesE2E-1", "hermes-agent.nousresearch.com",
    "Hermes 4", "Hermes 3 & 4 models", "Hermes-3-Llama-3.1-70B", "github.com/NousResearch/Hermes-Agent",
])
def test_brand_text_leaves_identifiers_urls_and_model_names_alone(text):
    assert brand_text(text) == text


def test_brand_text_is_idempotent_and_never_leaves_the_upstream_brand():
    once = brand_text("☤ Hermes Agent: Hermes, HermesCLI, hermes update, Hermes 4")
    assert brand_text(once) == once
    assert "Hermes Agent" not in once and SYMBOL in once
    assert "HermesCLI" in once and "hermes update" in once and "Hermes 4" in once


def test_flatten_brands_every_text_leaf_of_every_layer():
    flat = i18n_layers.flatten({"a": {"b": "Hermes Agent is ready ☤"}, "c": "Hermes 4 is a model"})
    assert flat == {"a.b": f"{AGENT_NAME} is ready {SYMBOL}", "c": "Hermes 4 is a model"}
    assert i18n_layers.load_locale_source({"x": "Ask Hermes"}) == {"x": f"Ask {AGENT_NAME}"}


@pytest.mark.parametrize("lang", i18n.SUPPORTED_LANGUAGES)
def test_bundled_catalogs_serve_branded_text(lang):
    catalog = i18n._load_bundled(lang)
    assert catalog, lang
    carrying = [key for key, text in catalog.items() if brand_text(text) != text]
    assert carrying == [], f"{lang}: {carrying[:5]}"
    assert any(AGENT_NAME in text for text in catalog.values()), lang


def test_t_renders_the_brand_for_the_default_language():
    key = next(k for k, v in i18n._load_bundled("en").items() if AGENT_NAME in v and "{" not in v)
    assert AGENT_NAME in i18n.t(key, lang="en")
    assert not any(legacy in i18n.t(key, lang="en") for legacy in _LEGACY)
