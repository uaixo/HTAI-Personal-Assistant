# Branding

The product name people see is **not** the name the code is written in. The code keeps its upstream
identifiers (the `hermes` command, `HERMES_*` environment variables, `~/.hermes`, the `hermes_*`
modules, `hermes://` links, HTTP headers, API object names) so that merges from upstream stay cheap;
only text a person reads carries the brand.

## Where the brand comes from

- `hermes_brand.py` (stdlib-only, import-safe) holds `AGENT_NAME`, `VENDOR` and `SYMBOL`, plus
  `brand_text()`, the one rule that turns the upstream product name into the brand.
  `apps/shared/src/brand.ts` is its TypeScript mirror; keep the two in step.
- **Catalogs are branded as they load.** `agent.i18n_layers.flatten` brands every text leaf of every
  layer (bundled `locales/*.yaml`, user overlays, plugin packs; core, `tui` and `desktop` surfaces).
  `brandCatalog()` does the same for the bundled desktop, dashboard and TUI catalogs. The catalog
  files stay byte-identical to upstream.
- **Literals are branded at rest** by `scripts/rebrand.py`: Python string constants (never docstrings
  or comments), TypeScript/JavaScript literals and JSX text, and line mode for Markdown, YAML, shell,
  PowerShell, Nix, Rust, JSON, HTML and plists. It never touches catalogs, third-party plugin cards,
  contributor records, lockfiles or the brand machinery itself.
- The CLI skin engine derives the default skin's `agent_name`, `response_label`, `welcome` and
  `goodbye` from `hermes_brand`; `banner.py` carries the block-letter logo and hero art.
- The desktop product identity (`apps/desktop/product-identity.cjs`) brands `display` and `pascal`
  (window titles, installer and archive names) and keeps `kebab` (appId, payload CLI name), so an
  installed build's state and single-instance lock stay where they are.

## What `brand_text` leaves alone

Identifiers, URLs and the upstream model family. The rule is word-bounded on both sides:

<!-- rebrand: keep-start -->
| Stays | Why |
|---|---|
| `hermes doctor`, `~/.hermes`, `hermes_cli` | lowercase identifiers |
| `HERMES_HOME` | uppercase identifiers |
| `X-Hermes-Token`, `Hermes-Setup.exe` | hyphen-joined |
| `NousResearch.Hermes` | dot-joined |
| `OpenHermes`, `HermesCLI` | letter-joined |
| `Hermes 4`, `Hermes 3 & 4`, `Hermes-3-Llama` | the model family |

`Hermes.app` / `Hermes.exe` **are** renamed: the desktop bundle is named after the product. A
possessive without an s (`Hermes' tool store`) becomes `'s`.
<!-- rebrand: keep-end -->

## Keeping text unbranded

A line that carries `rebrand: keep`, the line after such a comment, or a `rebrand: keep-start` …
`rebrand: keep-end` block is left alone by the script. Use it for text that must match what older
installs wrote to disk (`hermes_cli/default_soul.py` does this for the auto-seeded SOUL.md).

## After a merge from upstream

```bash
git merge upstream/main          # resolve conflicts in favour of upstream where only wording differs
python scripts/rebrand.py        # re-brand whatever the merge brought in (idempotent)
python scripts/rebrand.py --check   # exit 1 while anything still carries the upstream name
```

The script's own contracts live in `tests/scripts/test_rebrand.py`; the brand rule's in
`tests/test_hermes_brand.py` and `apps/shared/src/brand.test.ts`.
