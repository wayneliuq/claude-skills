# Execution Plan: User-First Spec Drafting & Implementation-Leakage Review
_Implements: docs/strategic-implementation/2026-05-17-spec-user-first-and-leakage-review/product-brief_spec-user-first-and-leakage-review.md · Date: 2026-05-17 · Revised: simplify ALTERNATIVE adopted, alignment FLAGs applied_

## Context

The strategic-implementation skill currently lets briefs leak implementation details into deliverables and HARD DECISIONs, and its generalist plan-review tier (alignment + simplify) misses a class of failure where the user-visible path is unreachable (UI built, pipeline missing). This plan modifies the drafter to enforce user-first framing, adds a fast leakage reviewer that gates brief handoff to the PM, and adds a third generalist reviewer (`user-validation`) that walks the named target user's path against the plan and BLOCKs if any acceptance step is unreachable. `alignment` drops PMF from its scope to give `user-validation` clean ownership.

All skill/agent files live at the cached plugin path `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/`. Upstream source repo: **GitHub `wayneliuq/strategic-implementation`**. Edits land in the cache for this environment; post-execution surfaces the edited-file list for upstream sync.

## Library lifecycle audit
_Clarify declared no integration-risk dependencies. Section omitted._

## Deliverables (DAG)

### ED1 — Drafter discipline + leakage gate (single SKILL.md pass)
Merges previously-drafted ED1 + ED2 + ED3 per simplify's ALTERNATIVE. The leakage reviewer is invoked via an inline `Agent` call with `model: sonnet` — no standalone `agents/leakage-reviewer.md` file.

- **Integration-risk class:** d
- **User-acceptance steps (from brief D1, D2, D3, D4):**
  1. Run `strategic-implementation` on any feature request. Brief's §2 opens with `**Who is the user of this feature:**` naming a concrete audience.
  2. No deliverable description names a library, package, file path, function name, framework feature, data structure, or algorithm. Every acceptance step is performable by the named user within their declared tooling/interaction surface.
  3. Each `[HARD DECISION]` either names a user-observable behavior, a coupling at "shared with component X" altitude, or a PM-verbatim constraint. No HARD DECISION names a specific library/package/technique unless that technique is itself the user-observable thing being decided.
  4. Before the brief is presented to the PM, a fast leakage check runs and either passes or returns violations with line references. Injecting a leakage phrase into a draft brief triggers a flag pointing to those exact lines. The check is materially faster than the existing generalist tier.
- **Validation method (chosen here):** cli — combined inspect-and-run:
  - post-hoc inspect the edited `product-brief-drafter/SKILL.md`: discipline rules updated, brief template includes the `Who is the user of this feature:` slot at top of §2, HARD DECISION altitude rule present, "Leakage gate" section present with inline sonnet prompt, gate runs before PM-facing announcement.
  - **Leakage-injection smoke test** — take a snapshot of an existing brief (use `/Users/qiangliu/Documents/Development/axiph/docs/strategic-implementation/2026-05-17-spec-user-first-and-leakage-review/product-brief_spec-user-first-and-leakage-review.md` itself), inject a leakage phrase (e.g., `"uses Plotly to render"`) into a deliverable line in a scratch copy, invoke the drafter in `revise` mode on the scratch copy, confirm the leakage gate flags the injected line with line reference.
  - **Success-signal validation (addresses alignment FLAG #2)** — pick one representative pre-existing brief from `docs/strategic-implementation/` (e.g., the most recent prior brief in that directory), re-draft it in a scratch path under the updated drafter, confirm zero library/package/file-path mentions in §2 and §5.
  - **Latency check (addresses alignment FLAG #1)** — during the leakage-injection smoke test, record wall-clock for the sonnet leakage call and for any one alignment-tier run available in session history; assert sonnet leakage call < alignment call. If no alignment call is available to compare against, document the sonnet wall-clock alone and defer the comparative assertion to first post-execution review.
- **Files:**
  - `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/skills/product-brief-drafter/SKILL.md`
- **Steps:**
  1. Add discipline rules: target-user requirement (mandatory `Who is the user of this feature:` at top of §2; internal-team interaction surface declared when applicable; `TBD — open question` allowed); no-implementation-leakage rule (no library/package/file-path/function/algorithm names in §2 deliverables, acceptance steps, or §5 HARD DECISIONs); altitude rule for HARD DECISIONs.
  2. Update the brief template under "## 2. What the user does / sees" to insert the `**Who is the user of this feature:**` line.
  3. Add new section "## Leakage gate (both modes)" after Discipline rules. Inline-author the sonnet prompt covering: scan §1–§5 only; flag library/package/file-path/function/algorithm/internal-artifact/test-name mentions; ALLOW target-user surface, "shared with component X" couplings, the user-observable thing being decided, §6 Risks, §7 References + Affected skill files; subject-matter caveat (when the brief's product IS a skill/agent, references to those skills/agents are not leakage). Drafter invokes `Agent` with `subagent_type: general-purpose`, `model: "sonnet"`, this inline prompt, and the brief path. Output cap ~600 tokens, JSON `{status, findings[], notes}`.
  4. Gate semantics: on FLAG status, drafter surfaces findings to the PM with line excerpts. In `auto`/`yolo`, drafter MAY attempt one self-revision pass on obviously safe findings before surfacing the remainder. Drafter does not return the success announcement until status is PASS. (Override protocol DEFERRED per simplify FLAG #3 — not in brief D4.)
  5. Update "### After writing" (draft mode) and "### After revising" (revise mode) so the leakage gate runs before the PM announcement.
- **Deps:** none
- **Pre-flight env check:** drafter SKILL file readable + writable; `Agent` tool available with `model` override.
- **may-invalidate:** `skills/strategic-implementation/SKILL.md` Step 3 narrative (currently "drafter writes brief and returns path" — still true; path-return is now gated on PASS, but the orchestrator's contract is unchanged). No update needed unless reviewer flags later.
- **Visual contract:** n/a
- **Consumer audit:** drafter's return contract unchanged (same `{path}` shape on success). The new gate only delays success — `unaffected-because-no-shape-change`. No external consumers of drafter beyond the orchestrator's Step 3.

### ED2 — Create user-validation agent
- **Integration-risk class:** d
- **User-acceptance steps (from brief D5, D6):**
  1. Plan-review output names a new reviewer that walks step-by-step through the brief's named target user performing acceptance steps against the plan.
  2. Reviewer enumerates each user-acceptance step paired with the plan deliverables that make it reachable, or flags unreachable.
  3. On a synthetic plan with UI complete but pipeline absent, the reviewer returns BLOCK (or HIGH FLAG) naming the unreachable acceptance step.
- **Validation method (chosen here):** cli — invoke the agent directly via `Agent` with `subagent_type: user-validation` against a synthetic plan + brief and confirm BLOCK with the named unreachable step. (Full review-orchestrator wiring evidence lives in ED3.)
- **Files:**
  - NEW: `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/agents/user-validation.md`
- **Steps:**
  1. Frontmatter: name `user-validation`, description as a generalist reviewer focused on user-perspective walkthrough.
  2. Body sections (mirror `alignment.md` structure):
     - "Adversarial stance" — assume the user cannot complete the walkthrough until you've found the specific step that breaks.
     - "Scope" — owns: named target user, declared interaction surface, per-acceptance-step walkthrough, end-to-end reachability of the user path including the "client-built, pipeline-missing" loophole, deliverable-recognizability gut-check (formerly nominally under alignment's PMF).
     - "Do not review" — explicitly cedes: missing deliverables (alignment), architecture conformance (alignment), consumer audits on shape change (alignment), validation-method honesty (`tests`), simplicity (`simplify`), code/data/security/dep specifics (specialists).
     - "Output schema" — JSON with `status`, `walkthrough[]` (one row per brief-deliverable acceptance step: `step`, `supporting_deliverables[]`, `reachable: yes|partial|no`, `flag`), `flags[]` (dimensions: `user-named`, `interaction-surface`, `walkthrough`, `reachability`, `pmf`), `recommendations[]`. Cap ~1500 tokens. (Simplify FLAG #4 noted schema richness as cosmetic; keep as-is — `walkthrough[]` matrix is the structural artifact that makes the reachability check legible.)
     - "Escalation triggers" — return BLOCK only when: a user-acceptance step is unreachable because a supporting deliverable is absent or stubbed; the brief's named target user has no path through the plan; an interaction surface required by the brief is missing.
     - "Processing learnings" — match alignment's block; tags `#user-validation`, `#pmf`, `#walkthrough`, `#reachability`.
- **Deps:** none
- **Pre-flight env check:** agents/ directory writable.
- **may-invalidate:** review orchestrator (handled by ED3).
- **Visual contract:** n/a
- **Consumer audit:** new agent, no consumers until ED3.

### ED3 — Alignment scope reduction + review orchestrator wiring (joint edit)
Merges previously-drafted ED4 + ED6 per simplify's ALTERNATIVE — these always co-change and validate together.

- **Integration-risk class:** d
- **User-acceptance steps (from brief D5, D7):**
  1. `agents/alignment.md` scope contains exactly five dimensions: brief alignment, consumer audit on shape change, architecture-doc conformance, future-proofing/naming/repo-coherence, specialist routing. PMF absent. (D7.2)
  2. Alignment's "Do not review" section explicitly cedes PMF AND user walkthroughs / user-reachability to `user-validation` (D7.4, addresses alignment FLAG #3).
  3. `skills/review/SKILL.md` generalist tier lists three parallel agents and explains each role. Anti-overlap rules documented. (D5.1, D7.1)
  4. End-to-end run against a synthetic plan (UI deliverable present, pipeline deliverable absent): three generalists run in parallel; `user-validation` BLOCKs naming the unreachable step; `alignment` does NOT flag PMF (because PMF moved); orchestrator surfaces BLOCK with `block_reason`. (D5.2, D5.3, D6)
- **Validation method (chosen here):** cli — joint synthetic-plan run as described in step 4. Inspect orchestrator output.
- **Files:**
  - `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/agents/alignment.md`
  - `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/skills/review/SKILL.md`
- **Steps:**
  1. In `alignment.md`: delete the "Product-market fit / PMF" item from Scope; renumber remaining items (5 dimensions total).
  2. In `alignment.md`: update "Do not review" to add "user-validation walkthroughs and user-reachability — that is `user-validation`'s job; PMF in any form lives there now. Alignment does not perform user walkthroughs or user-reachability checks." (Explicitly per alignment FLAG #3.)
  3. In `alignment.md`: update `flags[].dimension` enum — drop `pmf`; confirm `brief`, `consumer-audit`, `architecture`, `future-proofing` remain.
  4. In `review/SKILL.md` Step 2: launch `alignment`, `simplify`, AND `user-validation` in parallel. Pass brief path to both `alignment` and `user-validation`. Pass `max_tokens: 1500` hint to each.
  5. In `review/SKILL.md` Step 3: union now includes `user-validation.specialists_needed` (e.g., broken UI surface → `frontend-engineer`).
  6. In `review/SKILL.md` Step 5: BLOCK propagation includes `user-validation` BLOCK. Add note: when alignment flags "D5 absent" AND user-validation flags "step 3 of D5 unreachable because D5 absent", merge into one entry with corroboration (existing dedup logic covers this).
  7. In `review/SKILL.md`: add new section "## Generalist tier composition" near the top documenting the three agents, their scope boundaries, and the anti-overlap rules. Cross-link to `agents/alignment.md` and `agents/user-validation.md`.
  8. In `review/SKILL.md` Step 6 (Re-review): user-validation BLOCK alone may trigger a generalist re-run.
  9. In `skills/strategic-implementation/SKILL.md` Step 4 narrative: add user-validation to listed generalists.
- **Deps:** ED2 (user-validation agent file must exist before orchestrator references it).
- **Pre-flight env check:** ED2 complete; `review` skill invokable.
- **may-invalidate:** none beyond files in this deliverable's edit list.
- **Visual contract:** n/a
- **Consumer audit:** TWO shape changes in this deliverable.
  - **(a)** `alignment.md` `flags[].dimension` enum (drops `pmf`). Consumers: `review/SKILL.md` Step 5 synthesis treats flags as opaque records — `unaffected-because-orchestrator-does-not-switch-on-dimension-enum`. Project-learnings tags: any `#pmf` tag currently routed to alignment will, per ED2's "Processing learnings" block, now route to `user-validation` (which lists `#pmf` in its tag set). **This is intentional reassignment, not residue — addresses alignment FLAG #4.** No learnings currently exist with `#pmf` tag (verified via grep of `docs/strategic-implementation/project-learnings.md` if present); reassignment is forward-looking semantic claim.
  - **(b)** `review/SKILL.md` returned JSON (`{status, block_reason, alternative_path, patches, skipped_specialists, ran}`) — shape unchanged; `user-validation` simply contributes to `ran` and may set `status: BLOCK`. `unaffected-because-no-field-added-or-removed`.

## Parallel groups & order

```
Group A (parallel):       ED1, ED2
Group B:                  ED3 (deps: ED2)
```

ED1 is independent of both ED2 and ED3 — drafter changes do not depend on review-tier changes.

## Reused existing patterns

- **Agent file shape** — `agents/alignment.md` is the structural reference for `user-validation.md`.
- **Inline sub-agent invocation with model override** — drafter's leakage gate uses `Agent` with `model: "sonnet"` and an inline prompt rather than a persisted agent file. Empirically validated this session: the same prompt PASSed this very brief.
- **Review orchestrator dedup-with-corroboration** — `skills/review/SKILL.md` Step 5.2 already merges corroborating flags; ED3 adds no new dedup logic, just notes the new corroboration pattern.
- **Skill plan-mode entry-check** — drafter's existing entry-checks at top of draft/revise are preserved; leakage gate hooks in after them.

## Risks & contingencies

- **Plugin cache path.** Edits live in `~/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/`. Upstream source repo confirmed: **GitHub `wayneliuq/strategic-implementation`**. Post-execution surfaces the edited-file list for manual upstream PR.
- **`Agent` tool `model` override availability.** ED1's leakage gate depends on `Agent` accepting `model: "sonnet"` at call time. Empirically supported in this environment (used earlier this session). If the override is unavailable at execution time, fall back to invoking the default model with the leakage prompt — slower but functionally equivalent. The brief's HARD DECISION names model class as "operator-configurable, but defaults explicit" — both paths satisfy.
- **Leakage-reviewer false positives.** Discipline rule + subject-matter caveat in the inline prompt must be unambiguous. Pre-validated this session against this very brief.
- **`user-validation` ↔ `tests` overlap.** Mitigated by ED2's "Do not review" subsection ceding validation-method honesty to `tests`.
- **Synthetic plan for ED3 validation.** No real "client-built, no pipeline" plan exists at hand. ED3 validation authors a ~1-page synthetic plan as part of the cli check.
- **Existing project-learnings with `#pmf` tag.** ED3 consumer audit (a) claims none exist. If grep finds entries, they get auto-rerouted to `user-validation` per its tag set — operator should spot-check after execution.

## Out of scope for this plan

- Re-drafting any existing brief in `docs/strategic-implementation/` (except as a one-shot validation step in ED1).
- Changes to specialist reviewers (`boundaries`, `runtime-risk`, `tests`, `frontend-engineer`, `technical-expert`).
- Changes to `executing-plans`, `post-execution`, `clarify`, `ui-mockup`, `execution-plan`.
- Auto-fix of leakage by the reviewer (drafter optionally self-revises once in `auto`/`yolo`; PM owns final remediation).
- Per-finding leakage-override protocol (deferred per simplify FLAG #3; add when a real false-positive surfaces).
- Generating a target user when the PM didn't name one (brief surfaces TBD).

## Final steps on approval

1. Save execution plan → `docs/strategic-implementation/2026-05-17-spec-user-first-and-leakage-review/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans`
   - Execution plan path: `docs/strategic-implementation/2026-05-17-spec-user-first-and-leakage-review/execution-plan.md`
   - Feature folder path: `docs/strategic-implementation/2026-05-17-spec-user-first-and-leakage-review/`
   - Autonomy level: auto
