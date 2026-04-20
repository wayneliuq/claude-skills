---
name: prune-tests
description: Explicit user-invoked skill. Removes line-level unit tests that were intentionally kept sparse pre-GA. Gated by the GA state flag — refuses to run post-GA. Preserves acceptance/goal-level tests. Per-batch PM confirmation before deletion.
---

# prune-tests

This skill is **only invoked by explicit PM request** (e.g., "prune the pre-GA tests"). It is never auto-invoked. Its purpose is to clean up line-level unit tests that accumulated during pre-GA development, where v2's validation model intentionally favored goal-level acceptance tests over line-level coverage.

---

## Step 1 — Check GA state

Read `<repo-root>/.strategic-implementation/ga-state.json`.

- If the file does not exist: treat as `pre-ga`. Proceed.
- If `state: "pre-ga"`: proceed.
- If `state: "ga-prep"`: proceed — this is the expected state for prune.
- If `state: "ga"`: **refuse.** Announce:

> "GA state is `ga`. Post-GA test deletion is an explicit code change requiring its own brief. Aborting."

Exit without changes.

See `plugins/strategic-implementation/docs/ga-state-schema.md` for state semantics.

---

## Step 2 — Classify tests

Find every test file in the repo (glob for conventional names: `*.test.*`, `*.spec.*`, `test_*.py`, `*_test.go`, etc.). For each test within each file:

**Survives (acceptance/goal-level):**
- Tests whose name or description references a user flow, a brief acceptance criterion, or an end-to-end behavior.
- Tests tagged `@acceptance` / `@e2e` / `@integration` (whatever the project's convention is).
- Tests in files named `acceptance.*`, `e2e.*`, `integration.*`.

**Candidate for deletion (line-level unit):**
- Tests that exercise a single function's branches with synthetic inputs.
- Tests named after a function name (`test_calculate_discount`, `describe('parseUrl')`).
- Tests whose only assertions are on return values or property shapes of pure helpers.

**Ambiguous:** present to PM alongside candidates; do not delete by default.

---

## Step 3 — Present preview diff

Group candidates by test file. For each group, show:

```
File: <path>
Tests to delete: <count>
Tests to keep: <count>
Diff preview:
  - describe('parseUrl', ...) ← delete
  - describe('URL parsing flow (acceptance)', ...) ← keep
  ...
```

Do not delete anything yet.

---

## Step 4 — Per-batch confirmation

Group files by directory. For each directory batch, ask the PM:

> "Directory `<path>` — <N> candidate tests across <M> files. Approve, skip, or show details?"

Only delete a batch on explicit `approve`. `skip` leaves it untouched. `details` shows the full per-test list for that batch.

---

## Step 5 — Delete + commit

For each approved batch:
1. Apply deletions (remove individual `describe`/`it`/`test` blocks, or delete whole files if all tests within were candidates).
2. Run the surviving test suite immediately. If anything breaks unexpectedly, roll back the batch and report.
3. Stage + commit in a **separate commit per batch** titled `prune: remove pre-GA unit tests in <path>`.

---

## Step 6 — Run surviving suite

After all approved batches: run the full surviving suite. Report:
- Tests before: N
- Tests after: M
- Deleted: N - M
- Run result: pass/fail
- Commits: list of commit hashes

If any test fails after prune: **do not declare success.** Report the failure — the PM decides whether to restore or fix.

---

## Step 7 — Offer GA-prep transition

If the state was `pre-ga` and the prune completed cleanly, offer:

> "Prune complete. Transition ga-state to `ga-prep`? (This marks release-imminent and tightens later prune gates.)"

Only transition on explicit PM confirmation. Update `.strategic-implementation/ga-state.json` with new `state` and `transitioned_at`.

---

## Refusal conditions (summary)

- `state: "ga"`: refuse.
- Uncommitted working tree: refuse — require clean tree so the prune commits are isolated.
- No test files detected: no-op with a note.
