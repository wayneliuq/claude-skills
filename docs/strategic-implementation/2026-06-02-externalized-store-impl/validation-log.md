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
