# Claude session notes — uaixo/HTAI-Personal-Assistant

## Branches

- **`NousAI-Assistant` is the active development line**: a snapshot of upstream
  `nousresearch/hermes-agent` plus local additions. Base all work on it.
- `main` is a stale upstream copy with unrelated history — never base work on
  it, never open PRs against it.
- Never open PRs against `nousresearch/hermes-agent`. Upstream flows one way:
  upstream → this repo.

## Merge workflow (user-approved, 2026-07-22)

Land session work fully automatically — the user does not want to touch PRs:

1. **Sync first — before any code change**, bring the session branch up to
   the current remote tip: `git fetch origin NousAI-Assistant`, then
   `git checkout -B <session-branch> origin/NousAI-Assistant` when the branch
   carries no unmerged commits (the normal case — after its PR merges, restart
   it the same way), or `git rebase origin/NousAI-Assistant` when it holds
   unmerged work. Never start work from a stale tip.
2. Develop on that session feature branch cut from `NousAI-Assistant`.
3. Push, open a PR **based on `NousAI-Assistant`** (draft is fine).
4. Watch CI (`ci.yml` runs on `pull_request` only — direct pushes to
   `NousAI-Assistant` run no CI, which is why the PR step exists).
5. When green: mark ready and **squash-merge without asking**. Only pause for
   user input if CI reveals a real problem or the change is risky/destructive.

If repo Settings → Pull Requests → "Allow auto-merge" gets enabled, arm
auto-merge (squash) at PR creation instead of watch-and-merge.

## Upstream-sync safety rules

- Keep `NousAI-Assistant` conflict-free against upstream: **add-only files**;
  do not modify upstream-owned files. (UI code changes are Phase 2+ of the
  branding plan and need an explicit user request.)
- If the `check-attribution` CI job flags unmapped upstream author emails, map
  them with `python3 scripts/add_contributor.py <email> <github-login>` —
  verify the login from the commit's linked author via the GitHub API, don't
  guess.

## NousAI branding (Phase 1 — done)

`nousai-branding/` holds the config-only rebrand: skin (`skins/nousai.yaml`),
persona (`SOUL.md`), installers for Linux/macOS and Windows. Runtime files
install into the Hermes home directory, not the repo. See its README.
