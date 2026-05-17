# Product Brief: User-First Spec Drafting & Implementation-Leakage Review
_Slug: spec-user-first-and-leakage-review · Date: 2026-05-17 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)
> The strategic-implementation skill now produces product briefs that name a concrete target user for each feature and frame every deliverable and acceptance step as something that user can do and observe — implementation choices no longer leak into the brief. A new fast-model leakage reviewer scans drafts before the PM sees them and rejects briefs that smuggle in libraries, packages, or strategy below the "shared with component X" altitude. A new generalist user-validation reviewer joins the plan-review tier, stages the named user's end-to-end walkthrough, and blocks plans where the user-visible path is unreachable (e.g., client built but no DB pipeline). Together: spec drafting is less biased by premature implementation, and plans cannot pass review with broken user-validation paths.

## 2. What the user does / sees

**Who is the user of THIS feature:** the developer/agent operator running `/strategic-implementation` on a feature request (i.e., me/the PM using this orchestrator). Validation is performed by running the skill on a real or synthetic feature request and inspecting the artifacts and review output.

### D1 — Brief defines the feature's target user
**How a user verifies:**
1. Run `strategic-implementation` on any feature request.
2. Open the resulting `product-brief_<slug>.md`.
3. Section 2 ("What the user does / sees") opens with a `**Who is the user of this feature:**` line that names a concrete audience (e.g., "scientists running a plot session", "internal QA engineers", "the developer integrating stat X") rather than a generic "user".
4. Acceptance steps for every deliverable are framed as actions that named user can take and observations that user can make.

### D2 — Brief deliverables and acceptance steps contain no implementation details
**How a user verifies:**
1. Read any newly drafted brief.
2. No deliverable description names a library, package, file path, function name, framework feature, data structure, or algorithm.
3. No acceptance step says "test X passes," "endpoint Y returns Z," or names an internal artifact — every step is an action the named target user can perform within the limits of their own tooling. End-user (client) target: only actions the user can take through the shipped product. Internal-team target: the brief explicitly names the team's interaction surface (a specific skill, Claude Code, a dashboard, a shared doc, a CLI they already run) and acceptance steps stay inside that surface.

### D3 — HARD DECISIONs stay at strategic altitude
**How a user verifies:**
1. Open a brief with at least one `[HARD DECISION]` row.
2. Each hard decision either (a) names a user-observable behavior ("must work offline"), or (b) names a coupling at the "shared with component X" altitude ("shares filetree node model with the existing project tree"), or (c) names a constraint the PM stated verbatim.
3. No hard decision names a specific library, package, or implementation technique unless that technique is itself the user-observable thing being decided.

### D4 — Leakage reviewer rejects briefs that smuggle implementation in
**How a user verifies:**
1. Hand the orchestrator a feature request that the drafter would historically over-specify (e.g., "add a stat" or "feature parity with X").
2. Before the brief is presented for PM review, a fast leakage check runs and either passes the brief or returns a list of violations with line references.
3. Inject an implementation phrase into a draft brief manually (e.g., "uses Plotly to render," "Redis for caching") and re-run the leakage check — it flags those lines specifically.
4. The leakage check completes noticeably faster than the existing generalist tier (sonnet-class, single agent).

### D5 — User-validation reviewer joins plan review and walks the target user's path
**How a user verifies:**
1. Run `strategic-implementation` to plan-mode handoff on a non-trivial feature.
2. The plan-review output names a new reviewer that walks step-by-step through how the brief's named target user would perform the acceptance steps against what the plan actually builds.
3. The reviewer's output enumerates each user-acceptance step and pairs it with the plan deliverables that make it reachable, or flags it as unreachable.

### D6 — User-validation reviewer catches the "client-built-but-no-pipeline" loophole
**How a user verifies:**
1. Construct a synthetic execution plan where the UI deliverables look complete but the data/DB/pipeline deliverable required for the user to actually see a result is absent or stubbed.
2. Run the plan review.
3. The new reviewer returns BLOCK (or HIGH FLAG) naming the specific user-acceptance step that cannot be performed because the supporting deliverable is missing.

### D7 — Generalist tier composition and reviewer boundaries are documented
**How a user verifies:**
1. Open `skills/review/SKILL.md`. The generalist tier section lists the three parallel agents (`alignment`, `simplify`, `user-validation`) and explains the role of each.
2. Open `agents/alignment.md`. Its scope list contains exactly five dimensions: brief alignment, consumer audit on shape change, architecture-doc conformance, future-proofing/naming/repo-coherence, specialist routing. PMF is no longer in alignment's scope.
3. Open the new `agents/user-validation.md`. Its scope owns: named target user, interaction surface, per-acceptance-step walkthrough, end-to-end reachability of the user path (including the "client-built, pipeline-missing" loophole), and the deliverable-recognizability gut-check formerly nominally under alignment's PMF.
4. Both files include anti-overlap rules: `user-validation` does not flag missing deliverables (alignment's job), does not review architecture conformance, does not review validation-method honesty (`tests`'s job); `alignment` does not perform user walkthroughs or user-reachability checks.

## 3. Success signal
A representative pre-existing brief in this repo (e.g., one from `docs/strategic-implementation/`), re-drafted under the updated skill, contains zero library/package/file-path mentions in §2 and §5 of the brief, and a synthetic plan with a missing pipeline deliverable is BLOCKED by the new reviewer.

## 4. Boundaries
**In scope:**
- `product-brief-drafter` SKILL.md updates (target-user requirement, no-implementation discipline, HARD DECISION altitude rule).
- A new fast-model leakage reviewer wired into the brief-draft handoff.
- A new generalist user-validation reviewer agent.
- `review` orchestrator update to launch the new generalist alongside `alignment` and `simplify`.
- Documentation of the generalist tier composition.

**Out of scope:**
- Re-drafting existing briefs in the repo.
- Changes to specialist reviewers (`boundaries`, `runtime-risk`, `tests`, `frontend-engineer`, `technical-expert`).
- Changes to `executing-plans`, `post-execution`, `clarify`, `ui-mockup`, `execution-plan`.
- Auto-fix of leakage by the reviewer (it reports, the drafter or PM remediates).

**Anti-goals (we deliberately will not):**
- Add an LLM-based "user persona generator" that fabricates a user when the PM didn't name one — if the user is genuinely ambiguous, the brief surfaces it as an open question.
- Allow the leakage reviewer to silently rewrite the brief — it returns findings only.
- Couple the leakage check to the slow generalist tier — its value comes from being fast and dedicated.
- Overload `alignment` with user-validation walkthroughs (decision rationale in §5).

## 5. Decisions
| Decision | Choice | Status |
|---|---|---|
| Where the user-validation walkthrough lives | New generalist agent in parallel with `alignment` + `simplify` | `[HARD DECISION]` |
| PMF ownership | Moves wholly to `user-validation`. `alignment` drops PMF from its scope (5 dimensions, not 6) — no split, no overlap. | `[HARD DECISION]` |
| Leakage reviewer placement | Runs after brief is drafted, before PM sees it; blocks handoff on violations until drafter revises | `[HARD DECISION]` |
| Leakage reviewer model class | Fast model (sonnet-class) — operator-configurable, but defaults explicit | settled |
| Target-user line location in brief | Top of §2, mandatory; `TBD — open question` allowed if genuinely unknown | settled |
| Acceptance-step framing | Every step must be performable by the named target user within the limits of that user's declared tooling/interaction surface | settled |

### HARD DECISION: User-validation reviewer is NEW, not a refinement of `alignment`

**Tradeoffs:**

| Option | Pros | Cons |
|---|---|---|
| Refine `alignment` to also do user-validation walkthrough | One fewer agent in generalist tier; PMF dimension already nominally covers user outcomes; shared learnings across dimensions | Alignment already caps at ~1500 tokens across 5 dimensions (brief, consumer-audit, architecture, PMF, future-proofing, specialist routing) — adding a walkthrough dimension dilutes existing coverage; the failure mode named ("client built, no pipeline, user can't validate") is structurally a missing-deliverable-vs-user-path check, distinct from brief delivery; one agent doing six dimensions tends to shallow output on all of them; harder to give it a sharp adversarial brief ("stage the walkthrough and find the break") when it's also reconciling architecture and PMF. |
| **New generalist agent (chosen)** | Dedicated output budget and adversarial stance focused on one job: "act as the named target user, attempt every acceptance step against this plan, identify what breaks"; structurally orthogonal to alignment's brief-vs-plan diff; gives the user-validation walkthrough its own BLOCK authority on unreachable-user-path; scales without further bloating `alignment` | Three parallel generalist agents instead of two — modest token cost increase on every plan review; `review` orchestrator needs to know about the new agent; potential overlap with alignment on "did we drop a deliverable" must be scoped out by the new agent's prompt. |

### HARD DECISION: Leakage reviewer blocks brief handoff

**Tradeoffs:**

| Option | Pros | Cons |
|---|---|---|
| Advisory only (warnings printed, PM sees brief regardless) | Faster path to PM review; PM can override casually | Defeats the purpose — the goal is to prevent biased downstream plan review caused by implementation leakage; PMs typically don't re-read a brief carefully enough to catch leaked implementation phrasing. |
| **Block handoff until clean (chosen)** | Discipline is enforced at the cheapest point in the workflow; downstream reviewers and the PM see only clean briefs; cheap to override per-line if drafter justifies | One extra synchronous step before PM review; if the fast model is wrong, drafter has to push back (loop friction). |

## 6. Risks & unknowns
- **False positives in the leakage reviewer.** Some phrases ("shared with the existing filetree component") are allowed; "uses the filetree library" is not. The drafter needs an unambiguous discipline rule and the reviewer needs example-driven prompting. Owner: drafter — must clearly document the allowed-altitude rule so the reviewer can apply it.
- **Generalist tier token budget.** Three parallel agents per plan vs. two. We accept this as the cost of the fix; measurable by review-output size pre/post.
- **The new user-validation agent's overlap with `tests`.** `tests` reviews validation-method honesty; the new agent reviews whether the plan can support user-validation at all. Boundary must be drawn in the new agent's prompt to avoid duplicate flags.
- **`alignment` ↔ `user-validation` boundary.** Alignment owns *structural* diff (brief→plan, shapes, architecture, naming); user-validation owns *user-perspective* judgment (named user, walkthrough, reachability). Anti-overlap rules in both agents' prompts: user-validation never flags "deliverable missing" (alignment's BLOCK); alignment never performs walkthroughs. When both fire on the same root cause (alignment: "D5 absent"; user-validation: "step 3 unreachable because D5 missing"), the `review` orchestrator's dedup-with-corroboration logic raises severity rather than duplicating flags.
- **Existing in-flight features.** Briefs already drafted under the old discipline will look noisier compared to new briefs. Not a regression — out of scope to retro-fix.

## 7. References & revision log
**Document references:**
- Architecture: n/a (this is a process/skill change, not a product feature)
- UX/PMF: n/a
- Security policy: none
- Schema/ERD: n/a

**Affected skill files (for execution-plan's grounding, not PM-facing):**
- `skills/product-brief-drafter/SKILL.md`
- `skills/review/SKILL.md`
- `agents/alignment.md` (boundary clarification only — to avoid overlap with the new agent)
- New: `agents/user-validation.md` (or similar)
- New: leakage-review hook in `skills/product-brief-drafter/` or a dedicated sub-skill
- `skills/strategic-implementation/SKILL.md` (Step 3 handoff to include leakage check)

**Revision log:**
- v0.1 · 2026-05-17 · initial draft
- v0.2 · 2026-05-17 · D2.3 acceptance-step framing refined to "within the limits of the user's declared tooling/interaction surface"; PMF moved wholly from `alignment` to `user-validation` (added as HARD DECISION); D7 expanded to assert the alignment-scope reduction and anti-overlap rules; risk row added for the alignment↔user-validation boundary.
