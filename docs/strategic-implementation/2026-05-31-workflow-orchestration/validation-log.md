# Validation log
_Feature: workflow-orchestration · Started: 2026-06-01 · Autonomy: auto_

## Commit-number mapping (ED → D, execution order)
- D1 = ED1 (macro concept + criteria + template marker)
- D2 = ED7 (capture validation approach)
- D3 = ED2 (validation-approach recall load step)
- D4 = ED3 (tests reviewer macro e2e rule)
- D5 = ED4a (spike: workflow agent edit-visibility)
- D6 = ED4b (macro single-workflow execution)
- D7 = ED5 (graceful fallback + resume reconciliation + sequential decision line)

## SPIKE FINDING — D5 (ED4a): workflow agent edit-visibility + index.lock
**Method:** post-hoc (probe Workflow `wf_2063d77b-ce3`, 2 parallel agents, throwaway `.workflow-probe/` cleaned up)
**Edits land in:** the MAIN working tree. Both agents ran with cwd = repo root, `git rev-parse --show-toplevel` = repo root, each wrote its file AND saw the other's file in a shared index (`git add -A` staged both). Verified from the main session: both probe files present with correct content after the run.
**index.lock contention:** none observed — concurrent `git add -A` + `git reset` from both agents completed without lock errors. (Weak negative; not a guarantee under exact simultaneity.)
**2nd-diff-apply:** moot — shared tree needs no diff-apply harvest.
**Verdict / chosen ED4b (D6) mechanism:** **shared-tree-disjoint is the PRIMARY path** — domain agents write disjoint file sets directly in the shared working tree; the main thread performs the single atomic commit. The detached-worktree + `git diff | git apply` harvest is demoted to a theoretical fallback (only if a future macro-deliverable cannot guarantee file-disjointness or hits real contention). `agent(isolation:'worktree')` remains forbidden. Belt-and-suspenders: ED4b still requires build agents to run ZERO git commands (main thread owns all git), which makes the index.lock question moot regardless of the probe's weak-negative.
