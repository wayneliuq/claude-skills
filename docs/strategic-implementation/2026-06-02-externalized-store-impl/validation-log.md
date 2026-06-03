---
status: complete
domains: [github, gh-cli, store-adapter, filesystem, skill-rewiring]
outcome: GitHub-backed store adapter + locator + read-through cache; stages rewired fallback-safe; conversational feedback
supersedes: none
---
# Validation log
_Feature: externalized-store-impl · Started: 2026-06-02 · Autonomy: auto_

## APPROACH — D1
**Method:** integration-test (live)
**Domains:** github / gh-cli
**Approach:** ran `bootstrap.sh` directly against real GitHub → created private `wayneliuq/strategic-artifacts` (asserted `isPrivate=true`), wrote `store-locator.yaml` (repo-id `wayneliuq-claude-skills` + coords, secret-grep=0), re-ran → no-op (idempotent). gh pre-flight (auth+rate_limit) gated the run.

## DEV-001
**Type:** retry
**Deliverable:** D1
**Plan said:** assert private-by-default on the repo-reuse path.
**Actually:** first impl compared `gh`'s `visibility` enum (`PRIVATE`, uppercase) to `"private"` — create path passed via a lowercase sentinel, but the idempotent reuse path falsely refused.
**Resolution:** switched the check to the boolean `isPrivate` field (`true`/`false`). Re-validated: idempotent re-run exits 0.
**Downstream impact?** no
**Agent category:** boundaries

## APPROACH — D2
**Method:** integration-test (live)
**Domains:** github / gh-cli / store-adapter
**Approach:** drove `store.sh` against the real store repo — wrote a probe (non-ASCII + trailing newline), read back `diff` byte-identical, listed the feature, asserted a stale `--handle-in` surfaces a conflict (exit 3) and a correct handle updates, listed a never-written feature → empty; all probe paths deleted via `gh api -X DELETE` in an EXIT trap.

## DEV-002
**Type:** retry
**Deliverable:** D2
**Plan said:** `list` maps 404 → empty set (spec §6.1).
**Actually:** `gh api --jq` on a 404 leaked the GitHub error JSON to stdout (gh prints the error body to stdout on HTTP failure), so an empty feature "listed" the 404 object.
**Resolution:** capture `gh api` stdout first; on non-zero exit return empty; otherwise pipe through `jq -r '.[]?.path // empty'`. Re-validated: never-written feature lists truly empty.
**Downstream impact?** no
**Agent category:** technical

## APPROACH — D4
**Method:** integration-test (synthetic-flow harness, live) + close-read
**Domains:** skill-rewiring / github / cross-component routing
**Approach:** appended the Record-routing convention to all 8 record-touching stages (incl. `review` reader + orchestrator session-entry bootstrap) and added a tested fallback-safe `store.sh put` primitive. Harness drove the rewired write sequence for a synthetic `__e2e__` feature via `put` → 4 records listed in the store, zero happy-path fallback files, no `__e2e__` artifacts in the repo, durable tier untouched; FALLBACK test (fake failing `gh` on PATH) → `put` wrote the in-repo fallback path (nothing dropped); conflict surfaced (exit 3) without fallback. SKILL routing prose verified by close-read; runtime activation deferred to plugin-update (cutover caveat).
**Note:** simplify F-01 (unused `si_locator_exists`) resolved here — wired as the locator-presence check in `store.sh put`.

## APPROACH — D5
**Method:** post-hoc (grep + close-read)
**Domains:** skill-rewiring
**Approach:** retired the file-edit feedback channels — `<!-- pm: -->` brief/mockup comments, `mockup-feedback.md`, `<!-- pm-disposition: -->` — replacing each with conversational feedback (chat → re-emit the output-only record) per spec §9. Validated by grepping the SKILL set → zero surviving channel instructions, and confirming the brief/mockup revise flows + simplify disposition positively restate conversational feedback.

## DEV-004
**Type:** ambiguity-decision
**Deliverable:** D5
**Plan said:** D5 Files = product-brief-drafter, ui-mockup, simplify, executing-plans.
**Actually:** the feedback channels also lived in the orchestrator (`strategic-implementation/SKILL.md` brief + mockup revision loops) and `post-execution/SKILL.md` (disposition reference); the planned file list was incomplete. The post-hoc grep caught them.
**Resolution:** extended D5 to edit those two files too (within the same deliverable) so no channel survives. Confirmed by re-grep → none.
**Downstream impact?** no
**Agent category:** alignment

## APPROACH — D3
**Method:** integration-test (live)
**Domains:** github / gh-cli / filesystem
**Approach:** seeded a probe feature in the store, ran `cache.sh hydrate` → records mirrored to `~/.cache/strategic-artifacts/<repo-id>/<slug>/` byte-identical; verified the cache dir is outside the repo (git-status clean); `rm -rf` + re-hydrate → intact; hydrated from a repo subdir → identical path (CWD-independent via git-resolved repo-id); `cache.sh session` resolves the active feature from state.json and `--background` returns instantly. Probe + cache cleaned in an EXIT trap.

## DEV-003
**Type:** retry
**Deliverable:** D3
**Plan said:** SessionStart hydrate detaches and returns instantly.
**Actually:** `cache.sh session` re-invoked itself via `exec "$0"` / `nohup "$0"`, which hit a "cannot execute / permission" error on the relative path.
**Resolution:** re-invoke through `bash "$0" hydrate …` (foreground `exec bash`, background `nohup bash`) instead of exec'ing the path directly. Re-validated: session rc=0, --background returns instantly.
**Downstream impact?** no
**Agent category:** technical
