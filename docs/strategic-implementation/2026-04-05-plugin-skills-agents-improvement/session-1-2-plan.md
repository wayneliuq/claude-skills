## Session Plan: Session 1 — Research Phase
_Implements: Implementation Plan § Session 1_
_Date: 2026-04-05_

### Goal
Gather and synthesize current best practices for all 10 review agent domains via parallel web research, producing a prioritized findings document.

### Pre-conditions
- [ ] Prior sessions complete: none — this is Session 1
- [ ] Docs available: implementation plan at `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/implementation-guide.md`
- [ ] Output directory exists: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/`
- [ ] Read Session 3's "Files affected" list in the implementation guide to confirm the canonical 10 agent domain names and ordering before beginning Steps 1 and 2 — `research-findings.md` must use this same order

### Steps
1. Research best practices for the following 5 agent domains via web search [parallel group: A]
   - Domains: `10k-foot` (broad architectural alignment review), `technical-expert` (pitfall identification / deep technical review), `scope-limiter` (scope creep detection), `test-coverage` (test strategy review), `dependency` (dependency vetting)
   - What: For each domain, perform 1–3 targeted web searches; identify ≤5 ranked, actionable findings per domain (≥20 words each); note source URL or publication for each finding
2. Research best practices for the following 5 agent domains via web search [parallel group: A]
   - Domains: `security` (security review at plan level), `data-model` (schema/migration review), `api-contract` (API interface review), `performance` (performance review at plan level), `future-proofing` (structural quality / maintainability review)
   - What: For each domain, perform 1–3 targeted web searches; identify ≤5 ranked, actionable findings per domain (≥20 words each); note source URL or publication for each finding
3. Synthesize all 10 domains' findings into `research-findings.md` _(sequential — after steps 1 and 2)_
   - Files: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/research-findings.md` (new)
   - What: Create the file with:
     - First line: `_Research date: 2026-04-05_`
     - Exactly 10 `###` sections (one per agent domain, in canonical agent panel order from Session 3's file list)
     - Under each section: one-sentence intro describing the domain's review purpose, then a numbered list of findings (≤5 items, ≥20 words each, ranked highest-impact first)
     - Each finding includes its source (URL or publication) inline

### Deliverables & Tests
- [ ] Deliverable: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/research-findings.md` exists with a section for each of the 10 agent domains
  Test: File exists; `grep -c "^### " research-findings.md` returns 10; each section contains ≥1 and ≤5 numbered findings; no finding entry is shorter than 20 words; `grep -c "http" research-findings.md` returns ≥1 (at least one source present)

### Constraints
- Target: <200 LOC (this ceiling is a guard rail, not a target — the estimate is S)
- Do not implement anything from Sessions 2, 3, or 4
- Flag any unexpected scope expansion to user before proceeding
- If a step reveals a pre-condition is not met: stop and surface to user before continuing

---

## Session Plan: Session 2 — Tier 1: Portability, Correctness, and File Surfacing
_Implements: Implementation Plan § Session 2_
_Date: 2026-04-05_

### Goal
Fix all 6 correctness and portability issues in the plugin's orchestration skills and standardize file surfacing across all skills that create or edit files.

### Pre-conditions
- [ ] Prior sessions complete: none — Sessions 1 and 2 run in parallel (no dependency)
- [ ] Docs available: implementation plan at `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/implementation-guide.md`
- [ ] Verify: Run `grep -r "strategic-implementation:" plugins/strategic-implementation/skills/` to confirm the `strategic-implementation:X` invocation pattern is already used in existing cross-skill calls — use these as the source of truth for the replacement format (note: `plugin.json` does not list agent type names; the convention is resolved by Claude Code's plugin registry)
- [ ] Verify: Read `plugins/strategic-implementation/skills/sessionize/SKILL.md` Step 2a and `plugins/strategic-implementation/skills/session-plan/SKILL.md` Step 2a — confirm both read the agent's category tag dynamically from the agent file (not from a hardcoded enum); if either uses a hardcoded enum, surface to user before proceeding
- [ ] Verify: Run `grep -r "superpowers:writing-plans" plugins/strategic-implementation/` — expect results in `strategic-implementation/SKILL.md`; also expect a result in `_copied-skills/executing-plans.md` (this is a snapshot/backup file — not an active skill, ignore it); if results appear in any other active skill file, stop and surface to user

### Steps
1. Read `sessionize/SKILL.md` Step 2a and `session-plan/SKILL.md` Step 2a; run grep for `strategic-implementation:` pattern; run grep for `superpowers:writing-plans` — complete all pre-condition verifications [parallel group: A]
2. Edit `plugins/strategic-implementation/skills/sessionize/SKILL.md` — replace all absolute agent file paths (`/Users/...`) with their registered type names (`strategic-implementation:X`); add inline comment immediately after the agent list: `<!-- Agent type names are resolved by the Claude Code plugin registry — see .claude-plugin/plugin.json -->` [parallel group: B]
3. Edit `plugins/strategic-implementation/skills/session-plan/SKILL.md` — two combined changes in one atomic edit: (a) replace all absolute agent file paths with registered type names and add the same inline comment; (b) add Glob verification instruction to Step 2 rule 9: instruct the executor to use the Glob tool to verify that every file path referenced in session steps exists; annotate any unverified paths with `[PATH NOT FOUND]` [parallel group: B]
4. Edit `plugins/strategic-implementation/agents/future-proofing.md` — two combined changes: (a) change the learning category tag from `#architecture` to `#future-proofing` wherever it appears in the file, including both the tag declaration and the learning-injection filter description line in "Processing Project Learnings"; (b) verify no `#architecture` references remain [parallel group: B]
5. Edit `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` — remove the `superpowers:writing-plans` fast-path invocation; replace with inline instructions to: create `implementation-guide.md` at `docs/strategic-implementation/<date>-<slug>/implementation-guide.md`, populate it with the approved spec content, and invoke `strategic-implementation:executing-plans` [parallel group: B]
6. Edit `plugins/strategic-implementation/skills/executing-plans/SKILL.md` — three combined changes in one atomic edit: (a) add branch check to Step 0: run `git branch --show-current`; if result is `main` or `master`, display a warning and require explicit user confirmation before proceeding to Step 1; (b) update the deviation category enum to include `future-proofing` (replacing `architecture`); (c) add `_saved to docs/strategic-implementation/..._` announcement format to the deviation log creation block; add `_updated —_` format to implementation guide status update steps [parallel group: B]
7. Edit `plugins/strategic-implementation/skills/post-mortem/SKILL.md` — one change only: add `_saved to_` announcement to each Step 10 write block (post-mortem reads category tags dynamically from deviation log entries — there is no hardcoded enum to update) [parallel group: B]
8. Edit `plugins/strategic-implementation/skills/bug-fix/SKILL.md` — two combined changes: (a) update the deviation category enum to include `future-proofing` (replacing `architecture`); (b) add `_saved to_` announcement to the Step 3e deviation log creation block [parallel group: B]

### Deliverables & Tests
- [ ] Deliverable: All absolute paths removed from `sessionize/SKILL.md` and `session-plan/SKILL.md`; agent references replaced with registered type names; inline comment added to each file
  Test: `grep -r "/Users/" plugins/strategic-implementation/skills/sessionize/ plugins/strategic-implementation/skills/session-plan/` returns no results; `grep -c "strategic-implementation:" plugins/strategic-implementation/skills/sessionize/SKILL.md` returns ≥9

- [ ] Deliverable: `future-proofing` learning tag corrected throughout `future-proofing.md`; deviation category enum updated in `executing-plans` and `bug-fix`
  Test: `grep "#architecture" plugins/strategic-implementation/agents/future-proofing.md` returns no results; `grep "#future-proofing" plugins/strategic-implementation/agents/future-proofing.md` returns ≥1 match; `grep "future-proofing" plugins/strategic-implementation/skills/executing-plans/SKILL.md` returns a match; same in `bug-fix/SKILL.md`

- [ ] Deliverable: Branch check added to `executing-plans` Step 0
  Test: Read `executing-plans/SKILL.md` Step 0 — contains `git branch --show-current`, names `main` and `master` as branches requiring user confirmation, waits for explicit confirmation before proceeding to Step 1

- [ ] Deliverable: Glob verification added to `session-plan` Step 2 rule 9
  Test: Read `session-plan/SKILL.md` Step 2 rule 9 — contains the phrase "Glob tool"; describes `[PATH NOT FOUND]` annotation for unverified paths

- [ ] Deliverable: `superpowers:writing-plans` removed from `strategic-implementation/SKILL.md` fast-path; replaced with inline implementation guide creation
  Test: `grep "superpowers:writing-plans" plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` returns no results; fast-path block contains instructions to create and save `implementation-guide.md` and invoke `strategic-implementation:executing-plans`

- [ ] Deliverable: File surfacing announcements added to `executing-plans`, `post-mortem`, and `bug-fix`
  Test: Read `executing-plans/SKILL.md` — Step 3 deviation log creation block contains `_saved to docs/strategic-implementation/..._`; implementation guide status update steps contain `_updated —_`. Read `post-mortem/SKILL.md` — Step 10 write blocks contain `_saved to_`. Read `bug-fix/SKILL.md` — Step 3e deviation log creation contains `_saved to_`

### Constraints
- Target: ≤ ~500 LOC edited or written this session (guide estimate: M)
- Do not implement anything from Sessions 3 or 4
- Combine all edits to a shared file into a single atomic edit (no partial writes to the same file)
- Flag any unexpected scope expansion to user before proceeding
- If pre-condition verification reveals unexpected results (e.g., `superpowers:writing-plans` in additional active skill files beyond the expected two), stop and surface to user before continuing
