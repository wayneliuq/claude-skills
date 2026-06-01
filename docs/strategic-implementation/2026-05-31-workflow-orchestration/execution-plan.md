# Execution Plan: Cross-Domain Macro-Deliverable Execution
_Implements: product-brief_workflow-orchestration.md · Date: 2026-06-01 · Autonomy: auto_

## Context

Self-referential change: edits the `strategic-implementation` plugin itself (markdown SKILL.md files + one agent definition; no code runtime). Teaches the skill to recognize one user-validateable outcome spanning domains (backend / API-contract / frontend) that *can't* be split without losing e2e-validateability, execute its domains in ONE Claude Code Workflow, validate them together, and land ONE atomic commit — while all other work keeps running through today's sequential, decomposed flow. Adds macro-aware validation review + a narrow validation-approach memory (capture + recall).

Load-bearing findings from review:
1. **A macro-deliverable is exactly ONE deliverable → one `D<n>:` commit.** `hook-bash-counter.sh` (counts HEAD subject `^D[0-9]+:`, idempotent via `last_counted_sha`) and `hook-stop-orchestrator.sh` (chapter rotation by array length) stay correct **with no edits** — provided no intermediate per-domain commits leak onto the branch (an invariant, verified inside ED4b's acceptance, not a script change). ED8 dropped as standalone (simplify).
2. **The worktree-merge mechanism is NOT solved by `learnings-benchmark`.** Its harvest (`cp $WORK/output`) copies an output dir, never merges source edits; `agent(isolation:'worktree')` is explicitly forbidden there. So the mechanism for getting concurrent domain edits into one commit is a genuine unknown → **resolved by a spike (ED4a) before implementation (ED4b)**.
3. **`pipeline()` has no barrier** — contract-before-domains requires `await agent(contract)` THEN `parallel(domains)`, not `pipeline()`.
4. **L-005 (plugin-cache drift):** in-session skill/agent invocations load from the plugin cache, not the working tree. So validations that "run the edited reviewer/skill" are dishonest — replaced with working-tree `grep` + post-hoc. (Direct `bash` execution by path is unaffected.)

## Library lifecycle audit

### Workflow capability (Claude Code v2.1.154+ / Opus 4.8)
- **State that persists:** A run is resumable *within* a session (completed `agent()` calls cached) but does **not** survive Claude Code exit (restarts fresh). No mid-run user input (only agent permission prompts pause). Background; caps 16 concurrent / 1000 total agents.
- **Quirks / gotchas:** Version-gated; disable-able (`CLAUDE_CODE_DISABLE_WORKFLOWS=1`). A skill instructing the agent to call `Workflow` is a documented opt-in path. **Open until ED4a:** whether a workflow `agent()`'s file edits are visible in the main working tree (vs. an isolated context), and `.git/index.lock` contention when parallel agents run git ops. `agent(isolation:'worktree')` forks un-sanitized HEAD — avoid; the proven harvest is detached-worktree + diff-apply. Cannot be unit-tested — it is the integration seam.
- **Doc consulted:** `Workflow` tool spec (in-session); code.claude.com/docs/en/workflows (feasibility research).

## Deliverables (DAG)

### ED1 — Macro-deliverable concept, criteria gate, plan-template marker, and plan-time decision line (brief D1, D3; absorbs old ED6 template line)
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** D1 1–3; D3 1–2.
- **Validation method (chosen here):** cli — `grep` the edited `execution-plan/SKILL.md` for semantic keywords (`Macro-deliverable`, `disjoint`, criteria a–d, `Workflow decision`); confirm template still parses. Plus post-hoc: PM judges criteria quality. (L-004: keywords, not exact phrases.)
- **Files:** `plugins/strategic-implementation/skills/execution-plan/SKILL.md`
- **Steps:**
  1. Step 3 authoring rule "Macro-deliverable (narrow exception)": criteria ALL of (a) spans ≥2 domains, (b) not independently e2e-validateable, (c) one user-observable outcome, (d) large enough that concurrent build beats sequential; PLUS eligibility: domains own **disjoint file sets — authored AND generated/derived outputs** (no two domains write the same lockfile/index/bundle target), else not eligible without the ED4b worktree-harvest path. Expected domain count is small (≤ ~4) so `parallel(domains)` stays well under the 16-agent ceiling — do not generalize to large fan-out.
  2. Template fields after `User-acceptance steps`: `- **Macro-deliverable:** <true|false>` and `- **Domains & file partition:** <domain → disjoint path-set, or n/a>`.
  3. Add a per-macro "Workflow decision" line to the template's "Parallel groups & order" area (why it qualifies) — the plan-time half of brief D5.
- **Deps:** none
- **may-invalidate:** [`execution-plan/SKILL.md` row]
- **Consumer audit:** n/a — additive template fields.

### ED2 — Validation-approach recall load step (brief D7 recall)
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** D7 2–3.
- **Validation method (chosen here):** cli — `grep` the edited `execution-plan/SKILL.md` for the recall instruction keywords (`validation-approach recall`, `integration-risk`, `advisory`, `read-only`, silent-degrade wording). **No live skill invocation** (L-005). Post-hoc on phrasing.
- **Files:** `plugins/strategic-implementation/skills/execution-plan/SKILL.md`
- **Steps:**
  1. New Step 2 load sub-step after step 5 (project-learnings), before step 6 (brief-meta): "Validation-approach recall — for cross-domain / integration-risk deliverables, read-only `grep` the N most-recent prior `docs/strategic-implementation/*/validation-log.md` for captured approaches matching this brief's integration-risk class / domains; surface as advisory input to Step 3 method selection. Absent/none → proceed silently."
  2. State: advisory only; read-only.
- **Deps:** none (tolerates ED7 absence).
- **may-invalidate:** [`execution-plan/SKILL.md` row]
- **Consumer audit:** n/a.

### ED3 — Tests reviewer holds a macro-deliverable to end-to-end validation (brief D6)
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** D6 1–3.
- **Validation method (chosen here):** cli — `grep` the edited `agents/tests.md` for keywords [`Macro-deliverable`, `HIGH`, `cross-domain`, `end-to-end`, `integrated outcome`]; post-hoc for wording quality. **No live invocation of the reviewer** (L-005 trap — it would load the frozen cached agent). If a live check is ever wanted, prepend an explicit plugin reinstall.
- **Files:** `plugins/strategic-implementation/agents/tests.md`; one-line nudge in `execution-plan/SKILL.md` Step 3 rules 3 & 7.
- **Steps:**
  1. In `tests.md` Scope: "If a deliverable is `Macro-deliverable: true`, its validation method MUST demonstrate the *integrated cross-domain outcome* end-to-end — per-domain-only validation is a HIGH-severity FLAG (BLOCK if no method could prove the integrated outcome). Name the concrete cross-domain method."
  2. Tag note: `#macro` / reuse `#validation`.
  3. `execution-plan/SKILL.md` rules 3 & 7: a macro-deliverable's method must prove the integrated outcome, never a single domain.
- **Deps:** ED1.
- **may-invalidate:** [`execution-plan/SKILL.md` row]
- **Consumer audit:** n/a.

### ED4a — SPIKE: resolve workflow agent-edit visibility + git-contention (de-risks ED4b)
- **Integration-risk class:** a
- **User-acceptance steps (from brief):** none directly — investigation that gates D2's mechanism.
- **Validation method (chosen here):** post-hoc — the spike's output IS a written finding in `validation-log.md`. Run a throwaway 2-`agent()` workflow that each write a distinct file and run `git status`; observe (1) whether edits land in the main working tree or an isolated context, (2) `.git/index.lock` contention when both run git ops, (3) whether `agent(isolation:'worktree')` edits are recoverable. Record the verdict.
- **Files:** none (throwaway; finding recorded in `validation-log.md`).
- **Steps:**
  1. Author + run the probe workflow.
  2. Record finding: "main-tree-visible / isolated"; "index.lock safe / contends"; whether a SECOND domain diff applies cleanly after the first (clean `git apply` / context-conflict needs `--3way` / must sequential-rebuild); chosen ED4b mechanism (shared-tree-disjoint vs detached-worktree+diff-apply-harvest).
- **Deps:** none. **Must complete before ED4b.**
- **Pre-flight env check:** Workflow tool available; if unavailable, ED4a is skipped and ED4b proceeds to the sequential-only mechanism (still satisfies the one-commit macro unit; concurrency deferred) — log a deviation.
- **may-invalidate:** none.
- **Consumer audit:** n/a.

### ED4b — Macro-deliverable execution as a single workflow (brief D2; absorbs old ED6 announce + old ED8 counter check)
- **Integration-risk class:** a
- **User-acceptance steps (from brief):** D2 1–3.
- **Validation method (chosen here):** post-hoc dry-run + **explicit deviation**. Per PM decision: the in-session live trial would likely validate cached behavior (L-005), so concurrency in `/workflows` is **not** gated here — log a `validation-honesty` deviation ("macro concurrency path unproven in-session; live proof deferred to a manual fresh-session follow-up"). What IS asserted post-commit: exactly one `D<n>:` commit touching all domains + `checkpoint.md` + `validation-log.md`, NO intermediate per-domain commits, and (folded from ED8) running `bash plugins/strategic-implementation/scripts/hook-bash-counter.sh` by path against that commit increments `deliverables_done_in_chapter` by exactly 1 and advances `last_counted_sha` once (runs by path → bypasses L-005 cache).
- **Files:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
- **Steps:**
  1. **Amend Step 1 (Read plan / Extract)** to PARSE the new `Macro-deliverable` + `Domains & file partition` fields (the missing parse step technical-expert flagged).
  2. New "Step 2-macro" fired when `Macro-deliverable: true` AND Workflow available: author a Workflow with a **barrier** — `const seam = await agent(buildContract); parallel(domains.map(d => agent(buildDomain_d, { contract: seam })))` — the `await` is the barrier (`pipeline()` has none), and `seam` is threaded into each domain agent so the barrier is also a data handoff (domains build against the agreed contract, not just after it). Mechanism for getting edits into one tree = whatever **ED4a validated** (shared-tree-disjoint if edits are main-tree-visible + agents run zero git ops + disjoint generated outputs; else detached-worktree-per-domain + `git -C $WT diff | git apply` harvest, falling back to `git apply --3way` or sequential-rebuild on apply conflict per ED4a's finding; NOT `isolation:'worktree'`).
  3. **No-nested-subagents:** workflow agents build only; validation (2c), simplify, and the single commit (2d) run on the **main thread after** the workflow returns. Manual-preview deliverables → build + auto-checks inside, hand back for human preview after return.
  4. One atomic commit `D<n>:` (invariant: no per-domain commits). Emit the **execution-time decision line** (brief D5): `macro-deliverable: <reason> → workflow`.
  5. **Deferred concurrency proof (named, not floating):** post-execution surfaces a one-line action — "Operator: in a fresh session (cache reloaded), re-run this macro-deliverable and confirm concurrent domains in `/workflows`; record the result as a follow-up note in `validation-log.md`." This gives the deferred D2-step-2 observable an owner and a closing record.
- **Deps:** ED1, ED4a.
- **Pre-flight env check:** Workflow tool available (else ED5); tree clean before commit.
- **may-invalidate:** [`executing-plans/SKILL.md` row]
- **Consumer audit:** n/a — instruction change.

### ED5 — Graceful fallback + resume reconciliation + the sequential decision line (brief D4, D5 sequential half)
- **Integration-risk class:** a
- **User-acceptance steps (from brief):** D4 1–3; D5 (sequential-path line).
- **Validation method (chosen here):** cli — simulate unavailability (`CLAUDE_CODE_DISABLE_WORKFLOWS=1` / "tool absent" precondition) and `grep` the edited `executing-plans/SKILL.md` to confirm the sequential build path, the always-emitted decision line, and the resume-reconciliation branch are present. **Plus post-hoc manual trial** for D4 step 3 (actually interrupt a run and resume) — the one honest way to demonstrate it; env-var sim cannot.
- **Files:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
- **Steps:**
  1. Step 2-macro precondition: "If the `Workflow` tool is unavailable/disabled OR this is a resume after interruption → build domains sequentially in-tree (contract first), then the same single atomic commit. Surface: `workflow unavailable → built sequentially`."
  2. **Resume reconciliation** (runtime-risk): if `checkpoint.md` shows a macro-deliverable in-flight AND the tree is dirty with its declared domain paths, reset those paths to HEAD before the sequential rebuild (or require a clean tree and surface the discarded partial work). Backs the "no lost work" HARD DECISION deterministically.
  3. **Sequential / no-macro decision line** (brief D5 negative case — alignment + user-validation): emit `decomposable / below-threshold → sequential` on runs with no macro-deliverable, so D5 step 2 is observable independent of the workflow path.
- **Deps:** ED4b.
- **may-invalidate:** [`executing-plans/SKILL.md` row]
- **Consumer audit:** n/a.

### ED7 — Capture the validation approach in validation-log (brief D7 capture)
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** D7 1.
- **Validation method (chosen here):** cli — `grep` the edited `executing-plans/SKILL.md` to confirm the additive `Approach:` field in the validation-log append; confirm old logs without it still read (additive).
- **Files:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
- **Steps:**
  1. Step 2c/2d: for cross-domain / integration-risk deliverables, append `**Approach:** <pipeline/infra actually used>` to the validation-log entry (greppable by ED2).
  2. Additive only — no change to the header or DEV-NNN block shape (back-compat).
- **Deps:** none (enables ED2's usefulness).
- **may-invalidate:** [`executing-plans/SKILL.md` row]
- **Consumer audit:** validation-log entry shape — additive field; consumers `post-execution` learnings-synthesis, ED2 recall, AND `hook-validation-log-watcher.sh` all `unaffected-because-additive` (watcher keys on append/existence, not field schema — confirmed in ED7).

## Parallel groups & order
- Suggested linear order (file-contention aware): **ED1 → ED7 → ED2 → ED3 → ED4a → ED4b → ED5.**
- `execution-plan/SKILL.md` touched by ED1, ED2, ED3(nudge) → sequence. `executing-plans/SKILL.md` touched by ED4b, ED5, ED7 → sequence.
- ED4a (spike) MUST precede ED4b. ED5 after ED4b.
- **Workflow decision (this plan):** NOT a macro-deliverable. Its deliverables are file-disjoint markdown edits, individually validateable — correct to decompose normally and execute sequentially. The feature is not used to build itself.

## Reused existing patterns
- `learnings-benchmark/SKILL.md` Phase 3 — detached-worktree pattern referenced for ED4b's harvest fallback ONLY (corrected: diff-apply, not `cp $WORK/output`; never `isolation:'worktree'`). Not edited.
- `hook-bash-counter.sh` / `hook-stop-orchestrator.sh` — reused unchanged; ED4b's acceptance asserts they stay correct.
- Existing `Announce:` one-liner convention — reused by ED4b (macro) + ED5 (sequential).
- Existing validation-log append + DEV-NNN schema — extended additively by ED7; deviation rows used by ED4b (concurrency-unproven) and ED4a (spike finding).
- `Workflow` primitives (`agent`/`parallel`/`phase`) — used by ED4a/ED4b with an explicit await-barrier (no `pipeline()` for the seam→fanout boundary).

## Risks & contingencies
- **ED4a may find edits are isolated/non-recoverable.** Then ED4b's only safe path is detached-worktree + diff-apply harvest; if that too proves unreliable, ED4b ships sequential-only (one commit, macro unit + honest validation + memory all still land) and concurrency is deferred — logged as a deviation. The brief's macro-deliverable VALUE (honest e2e validation of one cross-domain unit) survives even without concurrency.
- **L-005 across the board.** All reviewer/skill-edit validations are working-tree `grep` + post-hoc, not live invocation. D2 concurrency explicitly deferred to a manual fresh-session trial (deviation logged).
- **Disjoint-file assumption.** Enforced as an ED1 eligibility gate; non-disjoint → worktree-harvest path or normal decomposition.
- **Wall-clock speed claim is observational-only**, not a gated acceptance check (brief success-signal's speed half). Stated, not silently assumed.
- **Back-compat of validation-log (ED7).** Additive field; ED2 + post-execution + the watcher tolerate its absence.

## Out of scope for this plan
- Inter-deliverable / independent-group concurrency (rejected in brief).
- Reviewer-step parallelism (dropped).
- A general skill-memory subsystem (ED2/ED7 are validation-approach-only).
- Editing the hook scripts (verified unnecessary; ED4b acceptance asserts it — edit only if the assertion fails).

## Final steps on approval
1. Save execution plan → `docs/strategic-implementation/2026-05-31-workflow-orchestration/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans` — plan path above, feature folder `docs/strategic-implementation/2026-05-31-workflow-orchestration/`, autonomy `auto`.
