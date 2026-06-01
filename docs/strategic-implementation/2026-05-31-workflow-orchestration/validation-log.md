# Validation log
_Feature: workflow-orchestration · Started: 2026-06-01 · Autonomy: auto_

## Commit-number mapping (ED → D, execution order)
- D1 = ED1 (macro concept + criteria + template marker)
- D2 = ED7 (capture validation approach)
- D3 = ED2 (validation-approach recall load step)
- D4 = ED3 (tests reviewer macro e2e rule)
- D5 = ED4a (spike: workflow agent edit-visibility)
- D6 = ED4b (macro single-workflow execution) + folded ED5 fallback/resume (see DEV-001)
- D7 = ED5 remainder (no-macro / sequential decision line + consolidated fallback validation)

## DEV-001
**Type:** ambiguity-decision
**Deliverable:** D6
**Plan said:** ED4b (D6) = macro workflow execution; ED5 (D7) = fallback + resume reconciliation + sequential decision line, as separate deliverables.
**Actually:** Folded ED5's capability-fallback + resume-reconciliation into D6's `Step 2-macro` block (as `Step 2-macro-fallback`), because the fallback is contiguous with the workflow path in the same file/section and reads coherently only adjacent to it.
**Resolution:** Pre-sanctioned by the plan's simplify section ("optionally fold ED5's fallback precondition into ED4's Step 2-macro authoring"). D7 narrows to the remaining ED5 piece: the no-macro / sequential decision line (brief D5 negative case) + the consolidated fallback validation.
**Downstream impact?** yes — D7 scope narrowed (see updated mapping below).
**Agent category:** technical

## SPIKE FINDING — D5 (ED4a): workflow agent edit-visibility + index.lock
**Method:** post-hoc (probe Workflow `wf_2063d77b-ce3`, 2 parallel agents, throwaway `.workflow-probe/` cleaned up)
**Edits land in:** the MAIN working tree. Both agents ran with cwd = repo root, `git rev-parse --show-toplevel` = repo root, each wrote its file AND saw the other's file in a shared index (`git add -A` staged both). Verified from the main session: both probe files present with correct content after the run.
**index.lock contention:** none observed — concurrent `git add -A` + `git reset` from both agents completed without lock errors. (Weak negative; not a guarantee under exact simultaneity.)
**2nd-diff-apply:** moot — shared tree needs no diff-apply harvest.
**Verdict / chosen ED4b (D6) mechanism:** **shared-tree-disjoint is the PRIMARY path** — domain agents write disjoint file sets directly in the shared working tree; the main thread performs the single atomic commit. The detached-worktree + `git diff | git apply` harvest is demoted to a theoretical fallback (only if a future macro-deliverable cannot guarantee file-disjointness or hits real contention). `agent(isolation:'worktree')` remains forbidden. Belt-and-suspenders: ED4b still requires build agents to run ZERO git commands (main thread owns all git), which makes the index.lock question moot regardless of the probe's weak-negative.
