---
name: sessionize
description: Converts an approved specification document into a sessionized implementation plan. Runs scope-limiter, simplify (whole-plan + per-session), and the full agent panel in sequence, synthesizes findings, and presents the plan for user approval.
---

# Sessionize

You are converting a finalized, user-approved specification document into a sessionized implementation plan — the concrete breakdown of what gets built in which order, used to drive session planning and execution.

This skill owns the full agent review round for the implementation plan. Agents do not run on the spec document — only on the sessionized plan.

You receive:
- The finalized specification document
- The feature folder path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/`) — passed by the orchestrator, established by implementation-drafter

---

## Step 1 — Read the Spec

Read the full specification document. Extract:
- **What is being built** (Section 2 and Section 4)
- **Success criteria** (Section 3)
- **Scope boundary** (Section 5) — sessions must not cross these exclusions
- **Hard decisions** (Section 6, marked with `[HARD DECISION]`) — these are fixed; sessions must implement them as specified
- **Open decisions** (Section 6) — if any remain, surface them to the user before sessionizing. Do not build sessions around unresolved decisions.
- **Risks and unknowns** (Section 7) — high-risk items should be addressed in earlier sessions where possible, to fail fast
- **Revision log** (bottom of doc) — review for any patterns that might affect session design

**If there are unresolved open decisions in Section 6:** stop. Surface them to the user and ask for resolution before proceeding. Sessionizing around open decisions produces a plan that cannot be executed.

---

## Step 2 — Collect Document References

Before running agents, ask the user for two document locations if not already provided:

1. **Security policy document** — "Is there a security policy document for this project? If so, where is it?"
2. **Schema design / ERD** — "Is there a schema design document, entity-relationship diagram, or data dictionary? If so, where is it?"

Only ask for what's relevant to the change (skip schema if no data storage is involved). Pass these locations to the security and data-model agents. If none exists, pass that information so the agents can flag it correctly.

---

## Step 2a — Load Project Learnings

1. Check if `docs/strategic-implementation/project-learnings.md` exists. If not: skip this step entirely.
2. Read the file. For each agent in the panel (Step 5), identify:
   - The agent's category tag (see agent files — each lists its category)
   - Filter learnings to those tagged with that agent's category AND tagged `#multi-session`
     (sessionize context applies multi-session learnings only — single-session learnings are not yet proven broadly)
3. If filtered learnings exist for an agent, prepare a "Project Learnings" block to inject into that agent's prompt in Step 5:

```
## Project Learnings (apply per your "Processing Project Learnings" section)
Context: implementation guide review — apply #multi-session learnings only.

[paste each applicable L-NNN entry in full]
```

Store these blocks; inject them in Step 5 when launching agents.

---

## Step 3 — Draft Sessions

Break the specification into sessions using the implementation guide template (`skills/implementation-guide.md`).

Rules for session design:
- **One clear goal per session.** A session's goal is one sentence. If you can't state it in one sentence, the session is doing too much.
- **Each session is self-contained.** A developer reading only that session block should know what to build, what files to touch, and how to verify it — without needing to read other sessions.
- **Fail-fast ordering.** Sessions that validate the riskiest or most uncertain parts of the plan come first where possible. Do not build a large foundation on top of an unvalidated assumption.
- **Hard decisions are locked.** Sessions must implement hard decisions as specified. Do not design sessions that would require reversing them.
- **Size constraint.** S = <200 LOC, M = 200–500 LOC, L = 500–1000 LOC. Any session estimated larger than L must be split. When in doubt, split — it is easier to merge sessions than to discover mid-execution that a session is too large.
- **Success criteria coverage.** Every success criterion from Section 3 of the spec must be verifiable by at least one session's deliverables. Check this explicitly before moving on.

For each session, draft:
- Goal (one sentence)
- Deliverables & Tests (each deliverable paired with its verification method)
- Files affected (specific file paths)
- Docs to update
- Estimated size (S / M / L)
- Hard decisions applied (any [HARD DECISION] items from the spec that this session implements — name them explicitly so the executor sees them)
- **Review agents** — assess which contextual agents are relevant to this specific session:
  - `frontend-engineer`: does this session create, modify, or significantly interface with UI components, pages, or frontend state?
  - _(additional contextual agents follow the same pattern as they are added)_

  Set `Review agents` to the agent name(s) if clearly applicable. If the session only touches a domain peripherally (e.g., one env-var read, a single CSS class, a minor label change), set `Review agents: none` and add a `Contextual notes` field with 1–2 sentences describing that peripheral touch — enough for always-on agents to account for it without a full dedicated review.

For the plan's **Overview** section, carry forward:
- All entries from spec Section 6 "Already decided" → **Key decisions** field
- This includes hard decisions AND other significant settled choices (library selections, architectural patterns, approach decisions)

Leave "Session Order & Dependencies" blank — the scope-limiter generates this.

---

## Step 4 — Run Scope Limiter

Run `strategic-implementation:scope-limiter` with the drafted sessions as input.

The scope-limiter will:
- Review sessions for scope creep and sizing
- Recommend any splits or merges
- Generate the session order and dependency map

Apply the scope-limiter's session order and dependency map to the plan. Address any sizing flags (split sessions that exceed L) before proceeding to the full agent panel.

---

## Step 4a — Run Simplify Agent

### Phase 1: Whole-plan simplicity check

Announce: "Running simplicity check against spec."
Launch `strategic-implementation:simplify` in whole-plan mode, passing: the full sessionized plan and the original spec. Wait for result.

**If STATUS: ALTERNATIVE:**

Present to the user under a `## Simplicity Review — Alternative Path Found` heading, rendering the agent's actual DISTILLED PLAN, ALTERNATIVE PATH, and FLAGS sections as received. Then ask:

> "A simpler path to the spec's success criteria was identified above. Do you want to rewrite the implementation guide along this path? Reply `yes` to rewrite, or `no` to proceed with the current plan."

Wait for explicit user response.

- **If yes:**
  1. Announce: "Rewriting implementation guide along the shorter path."
  2. Re-run Step 3 (Draft Sessions) using the alternative path description, the original spec, and the previous implementation guide as inputs. The alternative path description drives the session design; the spec's hard decisions and scope boundary remain fixed.
  3. Re-run Step 4 (Scope Limiter) on the new sessions.
  4. Proceed to Phase 2 below with the rewritten guide.

- **If no:** proceed to Phase 2 with the current guide.

**If STATUS: PASS:** store the Phase 1 FLAGS and RECOMMENDATIONS to include in Step 5/6 synthesis alongside Phase 2 outputs. Do not present Phase 1 output to the user — it flows silently into synthesis.

---

### Phase 2: Per-session simplicity check

Announce: "Running per-session simplicity check."
Launch one `strategic-implementation:simplify` sub-agent per session in parallel, using per-session mode. Each sub-agent receives:
- The single session block (goal, deliverables, files affected, estimated size)
- The full sessionized implementation guide (for cross-session redundancy context)
- The spec's success criteria (Section 3) and scope boundary (Section 5)

Wait for all sub-agents to return.

Collect all per-session `## Simplify (Session N: ...)` outputs. These are passed into Step 5 as additional agent outputs — they flow through synthesis exactly as any other agent FLAG or RECOMMENDATION. Do not present them to the user here.

---

## Step 5 — Run Full Agent Panel

Launch all always-on agents in parallel using the Agent tool. Each receives the full sessionized plan as input.

**Always launch:**
- `strategic-implementation:10k-foot`
- `strategic-implementation:technical-expert`
- `strategic-implementation:future-proofing`
- `strategic-implementation:security` (pass: security policy doc location from Step 2)
- `strategic-implementation:data-model` (pass: schema doc location from Step 2)
- `strategic-implementation:api-contract`
- `strategic-implementation:test-coverage`
- `strategic-implementation:performance`
- `strategic-implementation:dependency`

<!-- Agent type names are resolved by the Claude Code plugin registry — see .claude-plugin/plugin.json -->

**Launch conditionally — derived from session annotations:**

Collect the union of all `Review agents` fields across every session in the plan. For each distinct contextual agent name that appears in at least one session:
- Launch that agent with the full sessionized plan as input
- Pass the list of sessions that named this agent as focused context (so the agent knows which sessions to scrutinize most closely)

If no session lists a given contextual agent, do not launch it.

Currently defined contextual agents:
- `frontend-engineer` → `strategic-implementation:frontend-engineer`

Note: the scope-limiter already ran in Step 4 and its output is incorporated. Do not re-run it here.
Note: the simplify agent already ran in Step 4a. Its Phase 1 FLAGS/RECOMMENDATIONS and all Phase 2 per-session outputs are treated as additional agent outputs in synthesis (Step 6). Include them alongside the panel results.

Pass each agent's prepared "Project Learnings" block (from Step 2a) as additional context in its prompt, if one was prepared. Agents with no applicable learnings receive no block.

Wait for all agents to return.

---

## Step 6 — Synthesize Agent Outputs

Read all agent outputs. Apply the standard synthesis rules:

1. Collect all FLAGS and RECOMMENDATIONS.
2. Discard low-utility suggestions — vague, speculative, or not actionable against this specific plan.
3. Reconcile conflicts between agents — choose the more conservative or correct position; note the conflict.
4. Surface any BLOCK statuses to the user immediately. A BLOCK must be resolved before proceeding.
   - **If the BLOCK is resolvable at the session level** (e.g., a session is too large, a dependency is missing, a migration path is unspecified): patch the sessionized plan, re-present.
   - **If the BLOCK requires changes to the specification itself** (e.g., a hard decision needs revisiting, a fundamental scope or design issue was identified): inform the user — _"This BLOCK requires revising the specification before sessionization can proceed. Run the implementation-reviser with the following issue, then re-trigger sessionize."_ Pass the blocker details as the revision input. Do not attempt to patch the sessionized plan for spec-level issues.
5. If FLAGS or RECOMMENDATIONS require user decisions → surface them WITH a recommendation and rationale. Wait for response.
6. Apply the final patch list to the sessionized plan.
7. Run a final consistency check: goal, deliverables, and files consistent across sessions; naming consistent throughout; no orphan references.

---

## Step 7 — Present for Approval

Present the full sessionized implementation plan to the user.

If the user requests changes: apply them, re-run the consistency check, re-present. Do not re-run the full agent panel unless the changes are substantial (use judgment — substantial means a session is added, removed, or a hard decision is reversed).

Once approved:

Present the following:

```
Implementation plan approved.

Sessions:
[numbered list of session names and one-sentence goals]

When you're ready to plan the first session for execution, say "plan session [N]" or invoke the session-plan skill.
```

**Save the implementation guide.** Once the user approves:
- Save to `<feature-folder-path>/implementation-guide.md`
- Confirm: _Implementation guide saved to `<feature-folder-path>/implementation-guide.md`_
- Pass this path (and the feature folder path) to the orchestrator for forwarding to session-plan.

Do not automatically proceed to session planning. The user triggers that separately.
