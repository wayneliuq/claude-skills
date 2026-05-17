# Product Brief: Regression-check prune + Sonnet for the tests reviewer
_Slug: regression-prune-and-sonnet · Date: 2026-05-17 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> The strategic-implementation plugin now reviews and reports leaner. The reviewer that checks validation methods (`tests`) runs on a cheaper, faster model, returning verdicts noticeably ahead of its sibling specialists with no loss in catch rate. The post-execution regression-check report — historically a 10-section document that surfaced something genuinely new in only roughly one in eight feature cycles — has been pruned to five focused sections; trivial gaps that the maintainer used to disposition by hand are now auto-applied and just noted, leaving the maintainer to disposition only the handful of findings that actually need judgment.

## 2. What the user does / sees

**Who is the user of this feature:** the strategic-implementation skill maintainer (Wayne), operating through Claude Code as the orchestrator runs every feature cycle. The maintainer's interaction surface is the plugin's review tier output and the post-execution report file written into each feature folder.

### D1 — The validation-method reviewer runs on a smaller, faster model.

**How a user verifies:**
1. Start a feature cycle and approve a brief that produces an execution plan with several deliverables.
2. When the review tier launches, watch the specialist verdicts come back: the validation-method reviewer returns visibly ahead of its sibling specialists.
3. Read its output. The verdict still flags the same kinds of mismatches it used to — e.g., a deliverable that claims TDD validation but ships no tests, or a post-hoc claim that doesn't honor a brief's user-acceptance step — without any new false positives.

### D2 — The post-execution regression-check produces a pruned, mostly self-resolving report.

**How a user verifies:**
1. Let a feature cycle run to completion; the orchestrator invokes regression-check automatically on the final deliverable.
2. Open the report file in the feature folder. The body has at most five top-level sections — covering, in plain reader terms: which shared files this feature touched and what else might be affected; whether the artifacts a deliverable claimed to produce actually exist on disk (only when a deliverable was validated by claim-and-verify rather than a live test); a security review of any maintainer-tooling configuration touched (only when such files changed); a final simplicity-review pass; and an overall status line. The rest is either gone entirely or compressed to a single line.
3. Look at the new "auto-applied" subsection. Trivial gaps (a stale registry row, a missing one-line cross-reference of the type the skill already handles inline) appear there with a brief note of what was fixed; the maintainer is not prompted to disposition them.
4. Look at the status line. Only genuinely ambiguous findings — ones that require maintainer judgment — appear as FLAG or BLOCK items requiring disposition.

## 3. Success signal

The next feature cycle Wayne runs after this lands shows the validation-method reviewer completing visibly faster than its sibling specialists, and produces a regression-check report shorter than any of the twenty-four historical regression-check reports in the project archive — with the only items demanding Wayne's attention being ones a reasonable person would call genuinely ambiguous.

## 4. Boundaries

**In scope:**
- The validation-method reviewer's model assignment.
- The structure and section count of the regression-check report.
- The auto-apply behavior for trivial fixes the skill already performs inline.

**Out of scope:**
- Any other reviewer agent's model assignment (the other seven stay as they are).
- The triage and learnings-synthesis modes of post-execution (preserved intact).
- The executing-plans skill and the strategic-implementation orchestrator.
- The review skill itself.
- New telemetry, new metrics, new dependencies.

**Anti-goals (we would reject these even if free):**
- Deleting the regression-check phase entirely. The historical hit rate is small but non-zero, and the catches it produces (structural drift, missed registry entries, post-hoc artifact gaps) are the kind that cause silent breakage downstream — worth keeping a thin version.
- Expanding auto-apply to anything beyond trivial maintenance fixes. Auto-applying simplicity-review findings, test failures, or source-code changes would erase the disposition layer the maintainer relies on.
- Downgrading any reviewer with BLOCK authority on judgment calls. The risk is asymmetric — a missed judgment costs much more than a saved token.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Which reviewer to downgrade | Only the validation-method reviewer (`tests`). The other seven keep their current model. | `[HARD DECISION]` |
| Whether to remove the regression-check phase | Prune, do not remove. Keep cross-contamination + goal-backward + plugin-config + simplify pass + status. | `[HARD DECISION]` |
| Scope of auto-apply | Limited to trivial inline fixes the skill already handles (stale registry rows, missing one-line cross-references). Does not extend to simplify findings, test failures, or source code. | `[HARD DECISION]` |
| Report section verdicts | Cross-contamination / goal-backward (gated) / plugin-config (gated) / simplify final pass / status: KEEP. Test-suite outcome / registry sanity: COMPRESS to one line. Modified-files / acceptance-tests-authored / visual-diff: DROP. | settled |
| Triage and learnings-synthesis modes | Preserved intact; no changes. | settled |

### Tradeoff — downgrade only `tests`

| Path | Pros | Cons |
|---|---|---|
| Downgrade only `tests` (CHOSEN) | Captures the clearest cost-saving candidate (structured matrix walk, low judgment, large surface). No risk to BLOCK-authority reviewers. | Less aggressive on token spend; other reviewers remain on the larger model. |
| Downgrade `tests` + `runtime-risk` | Larger token saving. | `runtime-risk` carries judgment about performance and dependency risk; misses are asymmetric and hard to detect. |
| Downgrade all specialists | Largest token saving. | Specialist judgment loss compounds. Telemetry cannot prove break-even. |

### Tradeoff — prune, not delete, regression-check

| Path | Pros | Cons |
|---|---|---|
| Prune to five sections + auto-apply (CHOSEN) | Keeps the ~12% real-catch rate. Removes the noise the maintainer ignores. Auto-apply cuts disposition load on the trivial cases. | Some surface remains; the maintainer still reads a short report. |
| Delete regression-check entirely | Maximum saving. | The catches it produces (registry drift, post-hoc artifact gaps, cross-contamination of shared files) are structural and silent. Triage mode would not surface them — triage triggers on a maintainer-reported issue, not a quiet drift. |
| Keep all 10 sections | Most thorough on paper. | The historical 24-report audit shows the other sections produce noise, not signal. Maintainer disposition load is wasted. |

### Tradeoff — auto-apply scope

| Path | Pros | Cons |
|---|---|---|
| Trivial inline fixes only (CHOSEN) | Maintainer disposition load drops where it was always rubber-stamp. Risk is bounded — these are the same fixes the skill already performs. | Simplify findings, test failures, and code changes still need disposition. |
| Expand auto-apply to simplify findings | Further disposition load reduction. | Simplify findings are judgment calls (apply/defer/dismiss) — auto-applying erases the layer the maintainer uses to keep design coherent. |
| Expand auto-apply to test failures or code | Maximal autonomy. | Either could cause silent regressions and is far outside the "trivial maintenance" class. |

## 6. Risks & unknowns

- **Sonnet false-negative rate on validation-method review is not measured.** The historical record doesn't tell us whether the larger model was catching adequacy issues the smaller model would miss. Mitigation: D1's acceptance step explicitly checks a known TDD-skipped synthetic case still flags; if quality drops, revert the model field. Owner: maintainer.
- **Pruning a section could remove a low-frequency catch we didn't see in 24 reports.** Mitigation: each dropped section is justified against the audit; if a missed catch surfaces post-merge, the section can be restored without architectural change. Owner: maintainer.
- **Auto-apply could mask a fix that should have been escalated.** Mitigation: the auto-applied subsection lists every fix; nothing happens silently. The maintainer can scan it on each cycle. Owner: maintainer.
- **Plugin hot-reload caveat (carryover from prior cycle):** edits to plugin files inside `~/.claude/plugins/cache/...` may not take effect until a fresh session loads the new agent definitions. The maintainer must restart the session before the success-signal verification.

## 7. References & revision log

**Document references:**
- Architecture: none (plugin-internal change; no axiph architecture surface).
- UX/PMF: n/a — internal-tooling maintainer surface.
- Security policy: none.
- Schema/ERD: n/a — no data storage.

**Affected skill files (internal plumbing, named here for the execution-plan author only):**
- `plugins/strategic-implementation/agents/tests.md`
- `plugins/strategic-implementation/skills/post-execution/SKILL.md`

**Supporting analysis (in this conversation):**
- 24-report regression-check audit (~12% hit rate; section-by-section utility scorecard).
- 5-feature token-report synthesis (median ~300 KB tool-output; cannot isolate per-reviewer cost).

**Revision log:**
- v0.1 · 2026-05-17 · initial draft.
- v0.2 · 2026-05-17 · self-revision after leakage gate: rephrased D2 step 2 to describe each surviving report section by reader-facing purpose rather than internal section label. §5 section-verdict row left as-is — the section labels there are the user-observable decision the maintainer reads in the shipped report (subject-matter caveat).
