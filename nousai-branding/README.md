# NousAI Branding — Phase 1 (config-only rebrand)

Phase 1 of the NousAI UI customization plan: rebrand the CLI, TUI, and gateway
replies as **NousAI** using only files in the Hermes home directory
(`~/.hermes/` on Linux/macOS, `%LOCALAPPDATA%\hermes` on Windows).

**Nothing in this folder patches Hermes code.** The runtime files live outside
the repo, so:

- `hermes update` / upstream syncs are unaffected — this folder is new and
  upstream never touches it, so merges and rebases stay conflict-free.
- Reverting is trivial (see Rollback below).

## Contents

| File | Installs to | Purpose |
|---|---|---|
| `skins/nousai.yaml` | `<hermes-home>/skins/nousai.yaml` | Electric-indigo skin: colors, spinner, "NousAI" branding strings for CLI + TUI + desktop chrome |
| `SOUL.md` | `<hermes-home>/SOUL.md` | NousAI persona — how the agent speaks (loaded fresh each message) |
| `install.sh` | — | Installer for Linux/macOS |
| `install.ps1` | — | Installer for Windows |

## Install

Linux/macOS:

```bash
bash nousai-branding/install.sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File nousai-branding\install.ps1
```

The installer respects `HERMES_HOME` if set, backs up any existing `SOUL.md`
before replacing it, and never rewrites an existing `config.yaml` — if you
already have one, activate the skin with `/skin nousai` inside Hermes (the
choice is saved automatically) or set `display.skin: nousai` yourself.

## Messaging bots (optional, no code)

The skin already labels gateway replies as ` ◈ NousAI `. To finish the job on
each platform:

- **Telegram**: @BotFather → `/setname`, `/setuserpic`, `/setdescription`
- **Discord**: Developer Portal → your application → name, avatar, description
- **Slack**: app manifest → `display_information` (name, icon, background color)

## Rollback

- Skin only: `/skin default` inside Hermes.
- Everything: delete `<hermes-home>/skins/nousai.yaml`, restore the
  `SOUL.md.bak-*` backup over `SOUL.md`, and remove `display.skin: nousai`
  from `config.yaml`.

## Credit

Built on [Hermes Agent](https://github.com/nousresearch/hermes-agent) by
Nous Research (MIT).
