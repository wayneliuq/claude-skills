---
status: in-progress
domains: [github, gh-cli, store-adapter, filesystem, skill-rewiring]
outcome: TBD
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
