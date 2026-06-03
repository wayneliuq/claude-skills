# Execution Plan: Externalized Artifact Store — Implementation
_Implements: product-brief_externalized-store-impl.md · Date: 2026-06-02_

## Context

The approved spec (`docs/strategic-implementation/2026-06-02-externalized-artifacts/spec.md`) defines a backend-neutral externalized artifact store; this plan builds it against GitHub. Phase 1 (D1–D3) lands the infrastructure — a GitHub-backed adapter, a per-repo locator, a read-through cache, and first-run bootstrap — each validated by **real** I/O against the live private store `wayneliuq/strategic-artifacts`. Phase 2 (D4–D5) rewires the skill stages to route records through the adapter (with an in-repo fallback during transition) and replaces file-edit feedback with conversational feedback. Migration is forward-only (existing artifacts untouched); the durable tier stays in-repo.

**Cutover caveat (load-bearing for validation):** SKILL.md/hooks/scripts execute from the installed plugin cache (`${CLAUDE_PLUGIN_ROOT}`), not this repo's source. Source edits do not change the *running* skill this session. Therefore: adapter scripts (D1–D3) are validated by **direct invocation** of the source scripts against the live repo (real I/O, no reinstall needed); the SKILL rewiring (D4) is validated by a **synthetic-flow harness** that drives the adapter through the exact sequence a rewired stage performs. True activation (the running skill uses the new wiring) requires a plugin update + fresh session — a documented follow-up, explicitly out of scope this pass.

## Library lifecycle audit

### GitHub (via `gh` CLI 2.92.0; authenticated as `wayneliuq`, scopes incl. `repo`)
- **State that persists:** each record is a file on a branch of `wayneliuq/strategic-artifacts`; every write is a commit (free history). Updating an existing file requires its current **blob SHA**; a stale/missing SHA is rejected (HTTP 422/409) rather than silently overwritten — this is the optimistic-concurrency surface for the opaque version-handle (spec §6.3).
- **Quirks / gotchas:** `gh api .../contents/<path>` returns base64-wrapped JSON by default; raw markdown needs `-H "Accept: application/vnd.github.raw"` (or decode `.content`). Create-vs-update differ only by presence of `sha`. Listing a dir → `gh api .../contents/<prefix>` (≤1000 entries) or the git-trees API recursive for deeper. Authenticated REST ~5k req/h (non-binding). Repo creation: `gh repo create wayneliuq/strategic-artifacts --private` (idempotent guard: `gh repo view` first). Network/auth absence must degrade, not crash.
- **Doc consulted:** store-evaluation findings (run `wf_b78710fd-d9e`); GitHub REST Contents API; `gh auth status` (confirmed live this session).

### Local filesystem (read-through cache)
- **State that persists:** cache at `~/.cache/strategic-artifacts/<repo-id>/<date-slug>/` — outside any worktree, so it never appears in `git status` (no `.gitignore` entry needed; mirrors the `~/.claude/.../.memory-venv` out-of-repo precedent). Keyed by record address; disposable; re-hydratable from the store.
- **Quirks / gotchas:** worktrees share no working tree, so the cache must key off `repo-id`+address, never a checkout path. A deleted cache must transparently re-fetch. `XDG_CACHE_HOME` should be honored if set, else `~/.cache`.
- **Doc consulted:** `.gitignore` (memory precedent), `scripts/memory/refresh.sh` (session-start background pattern).

### git (the committed locator)
- **State that persists:** one committed file per repo (`docs/strategic-implementation/store-locator.yaml`) holding `repo-id` + store coordinates (owner/repo + branch). No secret. Bootstrap writes it once; thereafter read-only input.
- **Quirks / gotchas:** committed → travels per-branch; keep content near-static (no catalog) so divergence is low-stakes (spec §11). `repo-id` frozen at bootstrap (slug of git origin remote) so a remote change doesn't move the namespace.
- **Doc consulted:** spec §11; clarify decisions.

## Deliverables (DAG)

House style for all new scripts (from the Explore of `scripts/memory/`): `#!/usr/bin/env bash`, `set -uo pipefail`, `HERE="$(cd "$(dirname "$0")" && pwd)"`, degrade-to-silence on non-fatal paths, no secret ever echoed/written. Skills invoke via `bash "${CLAUDE_PLUGIN_ROOT}/scripts/store/<script>.sh" …`.

### D1 — First-run bootstrap: store + namespace + committed locator (no secret, idempotent)
- **Integration-risk class:** a (gh CLI lifecycle/auth)
- **User-acceptance steps (from brief):**
  1. In a repo that has never used the store, run the skill on any feature.
  2. Confirm the shared private store exists on GitHub and now contains this repo's namespace.
  3. Confirm the repo has exactly one new committed pointer file and that it shows no secret/token — only coordinates + namespace.
  4. Run again in the same repo; confirm it reuses the existing pointer (no duplicate setup).
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** integration-test (live) — run `scripts/store/bootstrap.sh` directly in this repo with real `gh`: assert (a) `gh repo view wayneliuq/strategic-artifacts` succeeds and visibility is private; (b) `docs/strategic-implementation/store-locator.yaml` now exists with `repo-id` + coordinates and contains NO token (grep for token-shaped strings → none); (c) re-running bootstrap is a no-op (idempotent — no second repo create, no locator rewrite churn). repo-id = slug of `git remote get-url origin`.
- **Validation note (per user-validation FLAG):** D1's brief step 1 trigger ("run the skill") is substituted by direct `bootstrap.sh` invocation this pass (cached-plugin caveat); the *outcomes* are observable now, the *running-skill trigger* only after activation. Step 2 ("store contains this repo's namespace") is **partially deferred to D2's probe write** — with lazy namespace creation, D1 asserts repo-exists + locator, not a pre-seeded namespace entry.
- **Files:** `plugins/strategic-implementation/scripts/store/common.sh` (shared: `repo_id()`, locator read/write, `gh_ok()`, **`assert_valid_address()`**, **`assert_no_secret()`**), `plugins/strategic-implementation/scripts/store/bootstrap.sh`, `plugins/strategic-implementation/scripts/setup.sh` (add `gh` dependency check), `docs/strategic-implementation/store-locator.yaml` (created by the run — the one committed pointer).
- **Steps:**
  1. `common.sh`:
     - `repo_id()` — slug of `git remote get-url origin`, **normalized identically for ssh (`git@github.com:owner/repo.git`) and https (`https://github.com/owner/repo.git`) forms, trailing `.git` stripped**; **no-origin case → deterministic fallback id (e.g. slug of the repo dir name) + warn, never crash** (the value is frozen into the locator, so it must be stable). [technical-expert]
     - `gh_ok()` — auth+network probe, degrade-to-silence; **its `gh auth token` value is never echoed, logged, or written**. [boundaries]
     - **`assert_valid_address(addr)`** — whitelist shape `<repo-id>/<date-slug>/<artifact-name>`: each segment matches only `[A-Za-z0-9._-]`, reject any segment `.`/`..`, reject leading `/`, embedded `//`, NUL, shell metacharacters; assert the resolved path is prefixed by `<repo-id>/`. Called by **every** `store.sh`/`cache.sh` op before any `gh`/path interpolation; args passed to `gh` as discrete argv, never a constructed shell string / `eval`. [boundaries — HIGH, was the block]
     - **`assert_no_secret(text)`** — grep concrete patterns: `ghp_|gho_|ghu_|ghs_|ghr_|github_pat_`, `AKIA[0-9A-Z]{16}`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`, `Authorization:`/`Bearer `, and long high-entropy runs (`[A-Za-z0-9+/=]{32,}`). **Block** (refuse write) on the locator; **warn** (log, don't fail the write) on record bodies (spec §10: no secret in any record, but avoid false-positive write failures on legitimate content). [boundaries]
  2. `bootstrap.sh`: probe gh; `gh repo view wayneliuq/strategic-artifacts --json visibility || gh repo create … --private`; **on the reuse path, hard-fail (non-zero, no locator/record write) if `visibility != private`** — private-by-default is asserted, not assumed. [boundaries] Ensure namespace **lazily on first write** (prefer over a `.keep` seed); write locator if absent (idempotent); never write a credential (`assert_no_secret` on the locator).
  3. `setup.sh`: add a `gh` check mirroring the `jq` check — **presence + `gh auth status` capability + a version floor (≥2.0)**, not bare `command -v`. [runtime-risk]
- **Deps:** none
- **Pre-flight env check:** `gh auth status` succeeds; network reachable; `git remote get-url origin` resolves (else the documented fallback id).
- **may-invalidate:** `[plugins/strategic-implementation/scripts/setup.sh]` (registry row — dependency added).
- **Consumer audit:** n/a — new scripts; no existing shape changed.

### D2 — Adapter: write / read / list records (byte-identical markdown, best-effort conflict)
- **Integration-risk class:** a
- **User-acceptance steps (from brief):**
  1. After the skill produces a feature's records, list that feature's records directly against the store and see every expected artifact.
  2. Open one record from the store and confirm it is the same markdown the skill produced.
  3. Confirm two close-together writes do not silently clobber — a conflicting write is reported, not lost (where supported).
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** integration-test (live) against `wayneliuq/strategic-artifacts` — write a record at `<repo-id>/__selftest__/probe.md` whose body **includes a trailing newline + a non-ASCII char**, `read` it back and `diff` byte-identical (exercises the raw round-trip, not just plain ASCII); `list <repo-id>/__selftest__/` shows it; perform a stale-version-handle write and assert a **surfaced conflict** (non-zero exit + message), not a silent overwrite; clean up the probe path **in a trap so a failed run never leaves probe files** a later `list` would surface. Real `gh`, no mocks. **Disclosure:** the stale-handle test proves the API-level conflict guarantee (GitHub rejects a stale-SHA write server-side regardless of local concurrency) — a serial-replay proxy for "two simultaneous actors", which is the honest proxy for a CLI adapter. [tests]
- **Files:** `plugins/strategic-implementation/scripts/store/store.sh` (subcommands `write <address> <file>`, `read <address>`, `list <prefix>`, `--capabilities`; each calls `assert_valid_address` first; emits/accepts the opaque version-handle), reuses `common.sh`.
- **Steps:**
  1. `read`: fetch raw content via `-H "Accept: application/vnd.github.raw"` → stdout byte-identical (avoids base64 line-wrap/`\n` reassembly bugs); emit the file's **git blob SHA** (from the contents GET) as the **opaque** handle via `--handle-out`/stderr — **never written into any record body** (spec §6.3). [technical-expert]
  2. `write`: **create-vs-update** — GET the path first: `404` → create (PUT with `content` base64, **omit `sha`**); `200` → update (PUT **with the current blob `sha`**; absent/stale → 422/409 → surfaced "conflict: stale handle"). Base64-encode the **full** body (incl. trailing newline, UTF-8) and pass via `gh api --input`/stdin JSON, **not** `-f content=<string>` (arg-length/newline mangling). Emit the new handle **from the PUT response** (authoritative — avoids read-after-write GET staleness). Run `assert_no_secret` (warn) on the body. [technical-expert, runtime-risk, boundaries]
  3. `list`: `gh api contents/<prefix>` → addresses; **map `404` → empty set** (no file under a never-written feature; spec §6.1). **≤1000 entries; beyond → git-trees recursive** (which itself truncates at ~100k/7MB — a defined ceiling at this scale, not silent truncation). [runtime-risk, technical-expert]
  4. Capability flags surfaced via `--capabilities`: `conflict-surfacing: yes`, `bulk-migration: trivial`.
- **Deps:** D1 (common.sh, locator, store exists)
- **Pre-flight env check:** locator present (D1 ran); `gh auth status`; network.
- **may-invalidate:** none.
- **Consumer audit:** the `store.sh` CLI is the adapter contract; its consumers are SKILL.md invocations — none exist yet (added in D4). `unaffected-because-no-current-consumers`. Callers treat the version-handle as an **opaque pass-through token**; only `store.sh` interprets it as a blob SHA. [alignment]

### D3 — Read-through cache: active feature local, gitignored-by-location, disposable, always-latest
- **Integration-risk class:** a (gh) + b (filesystem)
- **User-acceptance steps (from brief):**
  1. During a session, find the active feature's records in a local scratch location and open them.
  2. Confirm that location is excluded from version control (never in `git status`).
  3. Delete the mirror, continue, confirm records still intact (re-fetched).
  4. From a second worktree / fresh session, confirm the same feature's current records are available locally with no manual copy.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** integration-test (live) — `cache.sh hydrate <date-slug>` fetches the probe feature's records into `~/.cache/strategic-artifacts/<repo-id>/<date-slug>/`; assert files present + **byte-identical (diff, not just existence)** to store; assert path is outside the repo (so `git status` is clean — verify); `rm -rf` the cache dir then re-hydrate → **diff identical**; simulate a second worktree by hydrating from a different CWD of the same repo and confirm same content.
- **Files:** `plugins/strategic-implementation/scripts/store/cache.sh` (`hydrate <feature>`, `refresh <address>`, `path`), `plugins/strategic-implementation/hooks/hooks.json` (add a SessionStart entry to background-hydrate the active feature, mirroring `memory/refresh.sh --background`).
- **Steps:**
  1. `cache.sh hydrate`: resolve cache root (`${XDG_CACHE_HOME:-$HOME/.cache}/strategic-artifacts/<repo-id>/`); **before writing any hydrated file, canonicalize the resolved cache path and assert it is still inside the cache root (realpath-prefix check) — reject + degrade-to-silence otherwise** (a store address with `..` must never escape the cache dir). [boundaries — HIGH, was the block] `store.sh list` the feature, `store.sh read` each → write to cache, keyed by address.
  2. `cache.sh refresh <address>`: called by `store.sh write` post-write; **seed the mirror from the PUT response body emitted by `store.sh write`, NOT a follow-up GET** (GitHub may serve a stale GET right after a PUT — §6.2 always-latest). Best-effort (the skill's own authoritative reads go via `store.sh read`; the cache is for human browsing). [runtime-risk]
  3. `hooks.json`: SessionStart → `cache.sh hydrate` for the active feature — **mirror `memory/refresh.sh` exactly: (a) detach (nohup/fork) and `exit 0` so session start never blocks (the gh network fetch runs in the detached worker, never the hook); (b) `timeout: 10` on the hooks.json entry; (c) a no-active-feature guard → clean no-op when no active feature is resolvable; degrade-to-silence**. (Affects future installs, not this session.) [runtime-risk]
- **Deps:** D2 (uses store read/list)
- **Pre-flight env check:** D2 adapter working; writable cache dir.
- **may-invalidate:** `[plugins/strategic-implementation/hooks/hooks.json]` (registry row — SessionStart hook added).
- **Consumer audit:** n/a — new scripts; hooks.json gains an entry, no existing entry changed.

### D4 — Rewire skill stages: records → store, repo stays clean, in-repo fallback during transition
- **Integration-risk class:** c (cross-component routing across the skill stages)
- **User-acceptance steps (from brief):**
  1. Run the skill on a feature (or the validation feature).
  2. Confirm the feature's records now exist in the store under this repo's namespace.
  3. `git status` shows no new per-feature artifact files — only the pointer.
  4. Durable shared documents (project learnings, documentation registry) are untouched and still in the repo.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** integration-test (synthetic-flow harness, live) — because the running skill is the cached copy, drive the adapter through the exact write sequence a rewired stage performs for a synthetic feature `__e2e__`: write brief/plan/validation-log/checkpoint records via `store.sh`, then assert (a) `gh api` lists them under `<repo-id>/__e2e__/`; (b) `git status` shows no new artifact files (only the locator from D1); (c) durable tier files unchanged. **(d) FALLBACK TEST [tests — HIGH]: simulate `gh_ok`=false (e.g. unset/blank auth or unreachable) and assert a record write lands at the in-repo fallback path — not silently dropped** — this is the only proof of the "never loses an artifact" hard decision. Clean up `__e2e__` in a trap. **Ceiling disclosure:** the SKILL.md routing edits themselves are verified only by **close-read** this pass (not machine-executed — the running skill is cached); machine verification of the routing + fallback branch is **deferred to the plugin-update + fresh-session activation follow-up**. The close-read is the weaker half; the harness (live I/O) is the strong half. [tests, user-validation]
- **Files:** the per-feature-record stages under `plugins/strategic-implementation/skills/`: `strategic-implementation/SKILL.md` (session-entry bootstrap + cache hydrate), `product-brief-drafter/SKILL.md`, `ui-mockup/SKILL.md`, `execution-plan/SKILL.md`, `executing-plans/SKILL.md`, `post-execution/SKILL.md`, `simplify/SKILL.md`, **`review/SKILL.md` (a per-feature-record READER — reads execution-plan / brief / brief-meta; spec §7; MUST route its reads through the adapter too, or it reads stale/absent in-repo paths once writers route to the store) [alignment + technical-expert — HIGH]**. Each: replace "write/read the feature-folder file" with the routing convention. Durable-tier reads/writes (`project-learnings.md`, `documentation-registry.md`) stay in-repo, unchanged.
- **Steps:**
  1. Define the routing convention as **literal repeated prose echoed into each stage** (NOT a new include/indirection mechanism — 8 stages echoing one ~3-line convention is simpler to grep-verify than a shared-include abstraction [simplify]): a record read/write goes through `store.sh`; **the store-vs-fallback decision is evaluated PER RECORD OPERATION, not once per session** — `gh_ok`/locator-presence is checked immediately before every read and write, and a write that fails mid-run (auth expiry / network drop after an earlier success) falls back to the in-repo feature-folder path **within the same operation** (attempt store → on failure, write in-repo + log fallback) so no record hangs or is dropped. [runtime-risk — HIGH]
  2. Edit each stage's record read/write instructions to use the convention; leave durable-tier handling untouched. **Prior-feature record reads (execution-plan reads prior features "live", post-execution, review) resolve via `store.sh list`/`read` (live, §6.2) — NOT the active-feature cache (D3 scopes the cache to the active feature only).** [alignment]
  3. Wire session-entry bootstrap + cache-hydrate into the orchestrator `strategic-implementation/SKILL.md`.
- **Deps:** D2, D3 (skills call adapter + cache)
- **Pre-flight env check:** D1–D3 green; synthetic-flow harness runnable with live gh.
- **may-invalidate:** `[plugins/strategic-implementation/skills/execution-plan/SKILL.md, plugins/strategic-implementation/skills/executing-plans/SKILL.md, plugins/strategic-implementation/skills/simplify/SKILL.md, plugins/strategic-implementation/skills/review/SKILL.md]` (registry rows for the rewired stages).
- **Consumer audit:** n/a — no code data-shape change (prose + script-invocation edits). The adapter CLI's consumers (the SKILL invocations, incl. `review` as a reader) are all added/updated here.

### D5 — Conversational feedback replaces artifact-file editing
- **Integration-risk class:** d (skill-prose change; no live dependency)
- **User-acceptance steps (from brief):**
  1. Ask the skill to revise a brief by describing the change in chat; it re-emits the record without you editing a file.
  2. Same for a mockup revision and for accepting/deferring a review finding.
  3. No step in the flow asks you to edit a record file to give feedback.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** post-hoc — read the revised `product-brief-drafter` (revise), `ui-mockup` (revise), `simplify` / `executing-plans` (disposition) flows; confirm each positively restates feedback as conversational (chat → re-emit record); `grep` the SKILL.md set for surviving `<!-- pm:` / `mockup-feedback.md` / `<!-- pm-disposition:` instructions → none remain as feedback channels. **The grep covers the three known patterns; the close-read is the backstop for any file-edit instruction the grep misses. Ceiling disclosure: this proves source-level intent; runtime verification of chat-driven re-emit is deferred to the plugin-update + fresh-session activation follow-up (same as D4).** [tests]
- **Files:** `plugins/strategic-implementation/skills/product-brief-drafter/SKILL.md`, `ui-mockup/SKILL.md`, `simplify/SKILL.md`, `executing-plans/SKILL.md`.
- **Steps:**
  1. In each, remove the file-edit feedback instruction; replace with "PM gives feedback in chat; the skill re-emits the record" (per spec §9).
  2. Update the announce/prompt strings that currently invite inline-comment editing.
- **Deps:** D4 (same SKILL files; sequence to avoid edit conflicts)
- **Pre-flight env check:** none.
- **may-invalidate:** `[plugins/strategic-implementation/skills/simplify/SKILL.md]` (already covered by D4's set; ensure registry row current).
- **Consumer audit:** n/a.

## Parallel groups & order

- Strictly sequential: **D1 → D2 → D3 → D4 → D5**. D2 needs D1's `common.sh` + locator + live store; D3 needs D2's adapter; D4 needs D2+D3; D5 edits the same SKILL files as D4 (sequence to avoid conflicts).
- Phase boundary: D1–D3 (infrastructure, live-validated) complete and green **before** D4–D5 (rewiring) begin.

### Workflow decision
none — all deliverables decomposable and sequential; no macro-deliverable (no cross-domain disjoint-file-set concurrency).

## Reused existing patterns

- **`scripts/memory/` house style** — shebang, `set -uo pipefail`, `HERE=` path discovery, degrade-to-silence, interpreter/dep resolution; the new `scripts/store/` set mirrors it.
- **`scripts/memory/refresh.sh --background` + SessionStart hook** ([hooks.json:3-13]) — the precedent for D3's background session-start cache hydrate.
- **`${CLAUDE_PLUGIN_ROOT}/scripts/...` invocation** ([execution-plan/SKILL.md:40], [executing-plans/SKILL.md:177]) — the established SKILL→script call pattern D4 reuses.
- **Out-of-repo cache precedent** (`~/.claude/strategic-implementation/.memory-venv`) — the cache lives outside the repo, so no `.gitignore` entry is needed.
- **`setup.sh` `have <tool>` dependency check** ([setup.sh:52,83-85]) — D1 adds the `gh` check the same way.
- **`documentation-registry.md` schema + per-deliverable `Last Updated` bump** — registry rows updated inside each deliverable's atomic commit.

## Risks & contingencies

- **Cutover ≠ activation (cached plugin).** Source edits to SKILL.md/hooks don't change the running skill this session; this pass *lands + validates the mechanism*, it does not flip the live skill. Contingency: validation uses direct-invocation (D1–D3) and a synthetic-flow harness (D4); a final note documents the plugin-update + fresh-session step to truly cut over. Fallback removal stays out of scope.
- **Real external side effects.** This pass creates `wayneliuq/strategic-artifacts` and writes probe/`__e2e__` paths. Contingency: private repo; probe paths under `__selftest__`/`__e2e__` cleaned up after each validation; `gh` pre-flight gates every live deliverable.
- **Auth/network absence.** Live deliverables fail without `gh`/network. Contingency: pre-flight `gh auth status`; the adapter degrades-to-silence and the rewiring's in-repo fallback prevents data loss.
- **Secret leakage into the committed locator or a record.** Contingency: `assert_no_secret()` (concrete token patterns) blocks the locator write and warns on record bodies; `gh auth token` is never echoed/persisted; D1 validation greps the locator.
- **Address path-traversal / namespace-escape (security).** A `..`/metachar-bearing address could escape the per-repo namespace on the `gh` wire or escape the cache dir on disk. Contingency: `assert_valid_address()` (whitelist + argv-not-shell-string) before every op (D2); realpath-prefix containment before every cache write (D3). This was the review BLOCK — resolved by these guards.
- **Mid-run fallback gap.** If `gh` dies after an earlier successful write, a once-per-session fallback check would strand later writes. Contingency: fallback evaluated per record op; a failed store write falls back in-repo within the same op (D4); the fallback path is explicitly tested (D4 validation d).
- **Read-after-write staleness.** GitHub can serve a stale GET right after a PUT. Contingency: the new handle + mirror seed come from the PUT *response*, not a follow-up GET (D2/D3).
- **Invasive multi-stage edits.** Contingency: phased; in-repo fallback retained; D4 validated end-to-end (synthetic) before D5; this feature's own artifacts stay in-repo.
- **Success signal fully observable only after activation.** The brief §3 "run the skill → records in store, repo clean" is *validated* this pass via direct-invocation (D1–D3) + the synthetic-flow harness (D4), but is *observable by running the skill* only after the plugin-update + fresh-session follow-up (the running skill is the cached, un-rewired copy). This is disclosed, bounded, and the documented next step — not a silent gap.

## Out of scope for this plan

- Migrating the existing ~73 artifacts (forward-only).
- Removing the in-repo fallback (deliberate later call once the store is proven in real use).
- Headless / cron operation.
- Publishing the plugin update / flipping the running skill to the new wiring (documented follow-up).
- Moving the durable tier (`project-learnings.md`, `documentation-registry.md`) out of the repo.

## Verification (end-to-end)

1. **D1:** `bash plugins/strategic-implementation/scripts/store/bootstrap.sh`; `gh repo view wayneliuq/strategic-artifacts --json visibility`; open `docs/strategic-implementation/store-locator.yaml` (coords + repo-id, no token); re-run → no-op.
2. **D2:** round-trip a probe record (write → read → `diff`), `list`, stale-handle write → surfaced conflict; cleanup.
3. **D3:** `cache.sh hydrate`; confirm files under `~/.cache/strategic-artifacts/<repo-id>/…`, `git status` clean; delete + re-hydrate intact.
4. **D4:** synthetic-flow harness writes a `__e2e__` feature's records via the adapter; `gh api` lists them; `git status` shows only the locator; durable tier unchanged; **then simulate `gh_ok`=false and confirm a write lands at the in-repo fallback path (not dropped)**; cleanup in a trap.
5. **D5:** `grep -r "<!-- pm:" "mockup-feedback.md" "<!-- pm-disposition:"` across the rewired SKILL set → no surviving feedback-channel instructions.

## Review outcome (tiered review, 2026-06-02)

Ran: alignment, simplify, user-validation (generalists); boundaries, runtime-risk, technical-expert, tests (specialists). Initial status: **BLOCK** (boundaries — missing input validation), resolved in-plan by the security patches below (no brief change, no locked-decision reversal). Plan-gate: all specialist patches kept (in-scope hardening / coverage / validation-honesty), none rejected. simplify: PASS. Patches applied above:
- **High / security (cleared the BLOCK):** `assert_valid_address()` on every op (path-traversal / namespace-escape) [D2]; realpath cache-path containment [D3].
- **High:** add `review/SKILL.md` to D4 (a per-feature-record reader); per-record-op fallback (not once/session); explicit in-repo fallback test.
- **Med:** create-vs-update SHA handling; base64 raw round-trip tested with trailing-newline + non-ASCII [D2]; private-by-default asserted on the repo-reuse path [D1]; gh version-floor + auth check [D1]; SessionStart hydrate mirrors refresh.sh [D3]; read-after-write → seed mirror from PUT response [D3]; concrete no-secret patterns [D1]; close-read ceiling disclosed [D4]; stale-handle serial-replay proxy disclosed [D2].
- **Low:** repo-id slug normalization [D1]; opaque-handle never in record body [D2]; list pagination/404→empty [D2]; prior-feature reads live via adapter [D4]; D1 namespace deferral disclosed; D5 grep+close-read ceiling [D5].
- **simplify minor (accepted):** `cache.sh refresh` best-effort + seeded from PUT response; routing convention as literal repeated prose.
