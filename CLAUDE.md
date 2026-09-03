# Claude session notes — uaixo/HTAI-Personal-Assistant

## Standing user instructions (apply to every session and every task)

- "Please do not make any assumptions. Please ask any questions when things
  are not clear or certain." — When a decision point is ambiguous, when
  evidence is missing, or when multiple reasonable interpretations exist,
  stop and ask the user (AskUserQuestion) instead of picking one silently.
  Verify claims against the actual repo/CI/API state before acting on them.
- Autonomy boundary, so the rule above doesn't over-trigger: ASK before
  anything destructive, irreversible, outward-facing, or scope-changing, and
  whenever requirements genuinely allow more than one reading. PROCEED
  without asking for reversible mechanical steps that follow directly from
  the agreed task — running checks/tests, syncing the session branch, and
  the recorded PR → CI → squash-merge flow.
- **Upstream sync first (user-approved 2026-07-29)**: at the start of every
  request, check whether `origin/NousAI-Assistant` is behind
  `nousresearch/hermes-agent:main`; if it is, run the conflict replay and
  execute the sync yourself via the merge-commit PR flow (see "Executing an
  upstream sync" below) BEFORE acting on the prompt itself. Do not hand the
  sync back to the user or defer to GitHub's "Sync fork" button.

## Branches

- **`NousAI-Assistant` is the active development line**: a snapshot of upstream
  `nousresearch/hermes-agent` plus local additions. Base all work on it.
- `main` mirrors upstream `main`, resynced in bursts rather than continuously,
  so its staleness swings wildly — it was ~1,588 commits behind on 2026-08-28
  and sat exactly AT upstream `main` (`63279301bc`, 0 behind) on 2026-09-03.
  Never quote a staleness figure from this file; measure it:
  `git rev-list --count origin/main..upstream/main`. Current or not, `main`
  carries none of the NousAI carve-outs (no `nousai-branding/`,
  `DEFAULT_SKIN_NAME = 'nous'`) — never base work on it, never open PRs
  against it.
  (Historical note: it originally had unrelated history; since ~2026-08 it
  shares normal ancestry with `NousAI-Assistant`, so the reason to avoid it
  is simply that it is not the development line, not ancestry.)
- Never open PRs against `nousresearch/hermes-agent`. Upstream flows one way:
  upstream → this repo.

## Merge workflow (user-approved, 2026-07-22)

Land session work fully automatically — the user does not want to touch PRs:

1. **Sync first — before any code change**: `git fetch origin NousAI-Assistant`
   so work never starts from a stale tip.
2. **Fresh branch per change (user-approved 2026-07-22)**: cut a NEW branch
   `claude/nousai-<topic>` from `origin/NousAI-Assistant` for every change.
   Never reuse a branch whose PR has merged — reuse forces non-fast-forward
   pushes, which the permission classifier blocks and the stop hook flags.
   Fresh branches keep every push a plain fast-forward.
3. Push with plain `git push -u origin <branch>` (no force flags), open a PR
   **based on `NousAI-Assistant`** (draft is fine).
4. Watch CI (`ci.yaml` — renamed from `ci.yml` upstream 2026-08-19 — runs on
   `pull_request` only — direct pushes to
   `NousAI-Assistant` run no CI, which is why the PR step exists).
5. When green: mark ready and **squash-merge without asking**. Only pause for
   user input if CI reveals a real problem or the change is risky/destructive.
   After the merge, leave the remote feature branch alone (the user deletes
   merged branches from the GitHub UI); never push more commits to it.

If repo Settings → Pull Requests → "Allow auto-merge" gets enabled, arm
auto-merge (squash) at PR creation instead of watch-and-merge.

## Executing an upstream sync (PRs #13/#16/#18/#19 precedent)

1. Fetch both sides (`git fetch origin NousAI-Assistant`; fetch upstream
   `main` with enough depth), sanity-check the merge base (latest sync
   point must be an ancestor of upstream/main), then replay with
   `git merge-tree --write-tree origin/NousAI-Assistant upstream/main`.
2. Even when the replay is textually clean, check the MERGED TREE for
   semantic conflicts before executing: brand carve-out values intact, and
   the drift grep (`git grep "Hermes Desktop" <tree> -- apps/desktop/src
   apps/desktop/electron`) — PR #19 caught a new upstream test pinning a
   rebranded i18n string this way; fix such tests in lockstep on the sync
   branch.
3. Fresh branch `claude/nousai-sync-upstream-<date>` from
   `origin/NousAI-Assistant`, real merge, push, draft PR based on
   `NousAI-Assistant` with a "merge with MERGE COMMIT — do not squash"
   warning in the body.
4. When CI is green: mark ready and merge with **merge_method "merge"**
   (merge commit — NEVER squash a sync PR; squashing flattens upstream
   history and breaks future syncs). Then fast-forward local.
- **Review label gate (user-approved 2026-07-29)**: if the sync touches
  CI-sensitive workflow files, the "Review label gate" job fails until the
  PR carries the `ci-reviewed` label. Review the workflow diffs yourself;
  if benign, apply the label — repo automation re-runs the gate once the
  CI run has completed (a manual re-run is rejected while it's in
  progress). ASK the user first only if a workflow change looks risky
  (new/unpinned actions, secrets or permissions changes, trigger changes,
  outbound network calls).
- **Label-rerun push hazard (learned 2026-08-22, PR #72)**: after the
  `ci-reviewed` label is applied, `label-rerun.yml` starts a waiter that
  reruns the CI run's failed jobs once that run completes. Pushing a new
  commit while the waiter is alive cancels the old run, which the waiter
  treats as completion — it reruns the OLD head's run, and that rerun
  enters the `ci-<ref>` concurrency group and cancels the NEW head's run
  seconds into `detect`. A run whose detect was cancelled reports a
  VACUOUS green ("All required checks pass" succeeds with every lane
  skipped in ~30s) — never trust a green whose lanes all skipped.
  Recover: cancel the old run's rerun attempt, then rerun ALL jobs (not
  just failed) of the new head's run. Avoid: don't push to a labeled PR
  until the label-rerun waiter's run has completed.
- **MCP catalog security review gate (user-approved 2026-08-15)**: the same
  "Review label gate" job also fires when a sync touches the MCP catalog
  paths. The trigger set lives in `scripts/ci/classify_changes.py`
  (`_MCP_CATALOG_PATHS` / `_MCP_CATALOG_FILES`, consumed by
  `_is_mcp_catalog`) and is exactly two things: **any file under
  `optional-mcps/`** — a directory PREFIX match, not just
  `**/manifest.yaml`, though all 65 files there are manifests today — and
  **the single file `hermes_cli/mcp_catalog.py`**. Corrected 2026-09-03:
  this file used to also list `hermes_cli/web_routers/mcp.py`, which is
  WRONG — that file exists (23,618 bytes) but appears nowhere in the
  classifier or in `.github/`, and a PR touching only it classifies
  `mcp_catalog=false`. Verify with
  `printf 'PATH\n' | python3 scripts/ci/classify_changes.py`. Same
  terms as the workflow gate: review it yourself against the gate's four
  criteria and self-apply `ci-reviewed` when clean. Clean means: transport
  is remote (`type: http`/`sse`) with OAuth to the vendor's own official
  HTTPS endpoint, no `command`/`args`, no `install` refs, no env
  vars/secrets requested. `post_install` is print-only documentation
  (mcp_catalog.py just prints it), not an execution hook. ASK the user
  first if any entry adds a **stdio/local-command transport**, an
  **install ref** (git+/npx/uvx/pip bootstrap), or **requests env
  vars/secrets** — those are the surfaces that can execute code or
  exfiltrate on the user's machine.
  **Fail-open blind spot (verified 2026-09-03) — this gate can go silently
  OFF.** Unlike every other lane, `mcp_catalog` is deliberately excluded
  from the classifier's catch-all: `classify_changes.py` ends that branch
  with `# explicitly skip mcp catalog here`. So an empty changed-file list
  turns every other lane ON but leaves `mcp_catalog=false` (verified:
  `printf '' | python3 scripts/ci/classify_changes.py` → `python=true
  ci_review=true mcp_catalog=false`). That matters here because the fork's
  own 300-file guard below deliberately empties that list on big sync PRs.
  Normally upstream's `pull_request_changed_files()` recovery refills it and
  the gate computes correctly — but when the recovery ALSO fails (non
  `pull_request` event, `gh` error, or its 30s `--paginate` timeout on a
  very large PR) the gate is off while CI still looks green. On any sync PR
  large enough to trip the guard, check by hand and review the hits
  yourself rather than trusting the gate's silence:
  `git diff --name-only <base>..HEAD | grep -E '^optional-mcps/|^hermes_cli/mcp_catalog\.py$'`

## Upstream-sync safety rules

- Keep `NousAI-Assistant` conflict-free against upstream: **add-only files**;
  do not modify upstream-owned files — EXCEPT the Phase 2 brand-pack carve-out
  below (user-approved 2026-07-22). Widening that carve-out needs an explicit
  user request.
- **Phase 2 carve-out** — these upstream-owned files intentionally diverge and
  may conflict on upstream syncs; resolve by keeping upstream's changes and
  re-asserting the NousAI brand values:
  - `assets/banner.png` (NousAI banner)
  - `apps/desktop/assets/icon.{png,ico,icns}` (NousAI icons) +
    `apps/desktop/public/apple-touch-icon.png` (same artwork — electron
    main.ts APP_ICON_PATHS feeds it to app.dock.setIcon at runtime,
    overriding the bundle icns; also the onboarding provider-row logo)
  - `apps/desktop/package.json` (productName/executableName `NousAI`, appId
    `ai.nous.desktop`, artifactName `NousAI-…` — full-brand internals,
    user-approved 2026-07-22; only the `hermes://` protocol scheme and npm
    `name` stay upstream)
  - `apps/desktop/scripts/test-desktop.mjs` + `apps/desktop/e2e/fixtures.ts`
    (packaged-app paths derive from package.json productName/executableName
    instead of hardcoding `Hermes` — required because CI packages the app
    and asserts those paths)
  - `hermes_cli/main.py` (brand-agnostic packaged desktop app lookup on
    macOS — user commit)
  - `apps/desktop/src/components/chat/intro.tsx` +
    `apps/desktop/src/components/chat/intro-copy.jsonl` (empty-session hero:
    WORDMARK `NOUS AI ASSISTANT`, intro copy de-Hermes'd — user-approved
    2026-07-23)
  - `apps/desktop/electron/main.ts` (one line: APP_NAME default `'NousAI'` —
    drives macOS menu "About/Quit X", about panel, app.setName; the
    HERMES_DESKTOP_APP_NAME env override is upstream and unchanged)
  - `apps/desktop/src/components/brand-mark.tsx` (BrandMark renders the added
    `public/nousai-mark.png` instead of `nous-girl.jpg`; upstream's asset file
    stays untouched — user-approved 2026-07-23)
  - "Hermes Desktop" → "NousAI Desktop" everywhere the app displays it
    (user-approved full sweep 2026-07-23, re-swept 2026-07-26 after upstream
    added new onboarding strings and the `ar` locale; scope widened to
    `apps/shared/src` 2026-08-29, user-approved — **re-check after every
    upstream sync**:
    `grep -rn "Hermes Desktop" apps/desktop/src apps/desktop/electron apps/shared/src`
    and rebrand source + any test that pins those strings, in lockstep):
    `apps/desktop/src/i18n/{en,ja,zh,zh-hant,ar}.ts`,
    `src/components/desktop-install-overlay.test.tsx`,
    `src/store/onboarding.ts`, `src/lib/desktop-{git,fs}.ts`,
    `electron/{remote-lifecycle,hardening}.ts`, the pinned string in
    `src/i18n/runtime.test.ts`, and `apps/shared/src/websocket-url.ts`
    (OAuth ticket error message; the test pinning it matches only the
    unbranded half of the sentence). On upstream-sync conflicts, keep
    upstream's sentence and re-apply the product name.
    **That grep should return EXACTLY 2 hits, not 0 (verified 2026-09-03).**
    `src/app/settings/model-settings.test.tsx` and
    `src/lib/code-skew-error.test.ts` each quote a Python backend 503 detail
    verbatim, emitted by `hermes_cli/web_server.py` ("…use Restart backend
    in Hermes Desktop, or quit and reopen the app"). `web_server.py` is
    upstream-owned and outside this rebrand carve-out, so rebranding the
    fixtures would make them assert a string the backend never sends. Leave
    them. Treat >2 hits as real drift and 0 hits as a sign someone
    "fixed" these two — check before celebrating.
    **Known blind spot — LOCALIZED product names are invisible to this grep
    (verified 2026-09-03, NOT yet approved to fix).** The sweep matches only
    the ASCII string "Hermes Desktop", so localized product-name forms slip
    through: `src/i18n/zh.ts` carries 4 (`Hermes 桌面版` at lines 68, 76,
    3760, 3761), one of which (`boot.ready`) is pinned by
    `src/i18n/runtime.test.ts:21`, and `src/i18n/ja.ts:1474` carries
    `'Hermes デスクトップを設定'`. This is PRE-EXISTING, not sync drift:
    the counts are identical at the merge base, the fork tip, and
    upstream/main. Do NOT rebrand these on your own initiative — the
    recorded sweep is scoped to the literal product name, and widening it
    to localized forms is a NEW divergence that needs an explicit user
    request (it would also require editing `runtime.test.ts` in lockstep).
    Beware two false positives when checking: `ar.ts`/`zh-hant.ts` use
    localized "desktop" generically ("the desktop app"), and the KEY name
    `startingHermesDesktop` in `en.ts`/`ru.ts`/`types.ts` is not display
    copy — those values already read "NousAI Desktop".
  - `apps/desktop/index.html` (`<title>NousAI — Hermes</title>` — must keep
    the word `Hermes`: `e2e/boot.spec.ts` asserts it)
  - `apps/desktop/src/themes/presets.ts` (`nousaiTheme`, BUILTIN_THEMES entry,
    `DEFAULT_SKIN_NAME = 'nousai'`) + `presets.test.ts` (upstream's test pins
    `expect(DEFAULT_SKIN_NAME).toBe('nous')` — re-assert `'nousai'` in
    lockstep after every sync; learned 2026-08-25, PR #74, where GitHub log
    truncation disguised this deterministic assertion as a crash)
  - `web/src/themes/presets.ts` (`nousaiTheme` + BUILTIN_THEMES entry)
  - `hermes_cli/web_server.py` (one `nousai` row in `_BUILTIN_DASHBOARD_THEMES`)
- **CI runner carve-out (user-approved 2026-08-22)**: upstream pins several
  CI jobs to GitHub larger runners (`ubuntu-latest-32-core`,
  `ubuntu-latest-96-core`, `windows-latest-32-core`), an organization-plan
  feature this personal-account fork cannot provide — the jobs queue forever
  and CI never completes. On this fork those jobs run on standard hosted
  runners; **re-assert after every upstream sync** (sweep:
  `grep -rn -- "-core" .github/workflows/` and patch any `runs-on`/matrix
  `runner:` hits). Change only the functional lines; leave upstream's
  surrounding comments (they describe upstream's runners) untouched:
  - `js-tests.yml`: `runs-on: ubuntu-latest`, timeout 60 (upstream: 32-core, 30),
    and `run-workspace-checks.mjs --concurrency 1` (user-approved 2026-09-03,
    PR #88). Upstream passes no flag, so the default is
    `min(units, availableParallelism())` — sized for its 32-core runner. On
    4 cores that starts 4 check units at once, each forking its own
    vitest/tsc/eslint worker pool; the oversubscription pushes
    wall-clock-budgeted tests past their timeouts. PR #88 hit six such tests
    across three units (`web` SessionsPage #99387 @5s, `ui-tui`
    cursorDriftRegression @30s + virtualHistoryOffsetCache, `apps/desktop`
    local-models-settings ×2 + toolset-config-panel @15s) — ALL of which pass
    in isolation. Measured: at the default (4 on a 4-core box) all six fail;
    at `2` five recover but web's #99387 still misses its 5000ms budget by
    47ms; run alone the web suite passes 5/5 (291 tests each), hence `1`.
    Serial costs ~19min of the 60min timeout. Same reasoning as
    `HERMES_TEST_WORKERS: 8` in tests.yml.
    NOTE when diagnosing this lane: `run-workspace-checks.mjs` ends with
    `process.exit(1)`, which drops its own unflushed `=== summary ===` and
    `::error::` lines, so the CI log NEVER names the failing unit and the
    check run's output fields are empty. Reproduce locally instead:
    `node .github/scripts/run-workspace-checks.mjs`.
  - `tests.yml` "Run tests": `runs-on: ubuntu-latest`, timeout 120,
    `HERMES_TEST_WORKERS: 8` (upstream: 96-core, 30, 96)
  - `tests-os.yml` Windows matrix row: `runner: windows-latest`
  - `rust-tests.yml`: `runs-on: ubuntu-latest`
  - `nix.yml` flake-check job: `runs-on: ubuntu-latest`
  - `e2e-desktop.yml`: `runs-on: ubuntu-latest`
  - `docker.yml` is deliberately NOT patched: its build/publish jobs are
    gated `if: github.repository == 'NousResearch/hermes-agent'` and can
    never run on this fork.
  If the consolidated Python suite overruns 120 min on the 4-core runner,
  ask the user before escalating (fallback: restore a sharded matrix).
- **Compression de-flake carve-out (user-approved 2026-08-29, PR #82)** —
  previously undocumented, recorded 2026-09-03: `tests/agent/
  test_compression_review_76354.py` diverges from upstream in the S3
  stall-fallback test. The load-bearing part is the budget: the fork asserts
  `silence < idle * 1.5` where **upstream asserts `idle * 1.8`**. 1.8 is too
  loose to be meaningful on this fork — under the old buggy behaviour the
  measured silence lands ~0.75s against a 0.72s bar, so the test could
  false-PASS; 1.5 restores a real margin on both sides. The fork also adds a
  `cc.resolve_compression_fallback_route()` pre-warm plus a 0.01s pre-touch
  sleep and `touched_at` anchoring. **Re-assert `idle * 1.5` after every
  upstream sync** — a conflict here resolves silently toward upstream's 1.8
  and the test then passes for the wrong reason. NOTE the pre-warm's 5-line
  comment is now STALE: upstream added `stall_fallback=False` to the timed
  call, so the config load it warms is no longer paid inside the timed
  region. The call is harmless (cheap, idempotent) but the comment claims a
  mechanism that no longer applies; fixing that comment is a separate
  follow-up, not a sync task.
- **Runner-size test carve-out (user-approved 2026-09-03, PR #88)**:
  `tests/hermes_cli/test_local_quickstart.py` gains a
  `_fits_any_catalog_model(monkeypatch)` helper that pins `probe_budget` to a
  large budget, called from `test_quickstart_runs_all_three_legs` and
  `test_quickstart_skips_satisfied_legs`. Without it the quickstart route
  409s "no catalog model fits this machine": the smallest catalog entry
  (`qwen3.8-27b`) needs 16.5 GB and this fork's standard runner probes
  ~13.5 GB usable, so `select_variant` rejects all 4 entries. Upstream's
  377 GB runner always fits, so upstream never sees it. This is DETERMINISTIC,
  not a flake, and is the same root cause as the runner carve-outs above.
  The test already stubs downloads, the runtime install and the state
  endpoint but not the hardware probe — the gap is upstream's. Do NOT extend
  the helper to `test_quickstart_refuses_when_nothing_fits`: that test wants
  the real small budget and its 409 is the assertion. **Re-assert after every
  upstream sync**; on conflict keep upstream's test body and re-add the
  helper call.
- **Detect 300-file-cap carve-out (user-approved 2026-08-25, PR #74/#75)**:
  upstream's `.github/actions/detect-changes/action.yml` reads the changed
  files from the compare API, which hard-caps the list at 300 files. Sync
  PRs here routinely exceed that; files past the cap are invisible, so
  lanes with real changes get silently skipped and "All required checks
  pass" goes green vacuously (PR #74: Docs Site, Installer tests, and
  lockfile-diff all skipped over real changes). The fork adds a guard
  after the retry loop: at >=300 files, blank `CHANGED` so the classifier
  fails open (all lanes run). **Re-assert after every upstream sync**; on
  conflict keep upstream's version of the action and re-insert the guard.
  Symptom check for any big sync: PR diff >300 files + a skipped lane =
  verify the skip against the real diff before trusting the green.
  **DO NOT delete this guard as "redundant" (control flow traced
  2026-09-03).** Upstream since added a `pull_request_changed_files()`
  recovery in `scripts/ci/classify_changes.py`, which looks like it
  supersedes the guard. It does not — it is *downstream* of it. `main()`
  reads stdin and only calls the recovery `if not any(f.strip() for f in
  files)`, so **blanking `CHANGED` is precisely what triggers the
  recovery**, which then re-fetches the COMPLETE list from
  `pulls/{pr}/files --paginate` (cap 3000, well above any sync here).
  Remove the guard and the classifier goes back to deciding lanes from a
  silently truncated 300-file list — strictly worse than before. Confirmed
  end-to-end on PR #88: 1258 files, compare capped at 300, guard blanked
  it, and the bot then reported `ci_review_files` holding 8 real `.github/`
  paths — a populated list only possible if the recovery returned the full
  set. Caveat worth knowing: the recovery returns `[]` on a non
  `pull_request` event, on `gh` failure, or on its 30s `--paginate`
  timeout, and `classify([])` then hits the catch-all — which turns every
  lane on EXCEPT `mcp_catalog` (see the MCP gate's fail-open blind spot
  above).
- Deliberately NOT forked: `ui-tui/` default theme/content (runtime skin
  already themes the TUI; upstream tests hardcode the Hermes brand there).
- If the `check-attribution` CI job flags unmapped upstream author emails, map
  them with `python3 scripts/add_contributor.py <email> <github-login>` —
  verify the login from the commit's linked author via the GitHub API, don't
  guess.

## NousAI branding (Phase 1 + 2 — done)

`nousai-branding/` holds the config-only rebrand: skin (`skins/nousai.yaml`),
persona (`SOUL.md`), installers for Linux/macOS and Windows. Runtime files
install into the Hermes home directory, not the repo. See its README.

Phase 2 (brand pack) lives in the carve-out files listed above: NousAI
banner/icons, desktop app identity, and first-class `nousai` desktop/web
theme presets (desktop default; web default set via `dashboard.theme` in
config, which the installers write).
