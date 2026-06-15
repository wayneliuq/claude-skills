---
name: product-brief-drafter
description: Drafts or revises the single PM-facing artifact for a feature — the product brief. Two modes, draft (fresh) and revise (diff-based against PM inline feedback). The brief is the only document the PM approves before execution; it is also the input to execution-plan.
---

# product-brief-drafter

You produce `product-brief_<slug>.md` — the single PM-approvable artifact for a feature. It is a compact, user-observable description of what will be built and how a human, using the product, would confirm it works.

**Modes:** `draft` (new brief) and `revise` (existing brief + PM inline markdown feedback).

**Output location:** `docs/strategic-implementation/<YYYY-MM-DD>-<slug>/product-brief_<slug>.md` where `<slug>` is a 2–3 word kebab-case derivation of the feature.

---

## Discipline rules (both modes)

1. **No code.** Not even snippets. The PM does not read code.
2. **No jargon without a parenthetical.** If you must say "idempotent," write "idempotent (safe to run twice)."
3. **Every deliverable is user-observable.** If the PM cannot tell from a demo that a deliverable landed, it does not belong in the brief — move it into execution-plan as internal plumbing.
4. **Define the user.** §2 must open with `**Who is the user of this feature:**` naming a concrete audience — the segment of the product's userbase, an internal team, a specific role, etc. For internal-team users, also name the team's interaction surface (a specific skill, Claude Code, a dashboard, a shared doc, a CLI). `TBD — open question` is allowed only when the user is genuinely ambiguous; never fabricate a persona. The named user is what every acceptance step must be performable by.
5. **Every deliverable declares user-facing acceptance steps** — a short numbered list answering the question *"how would the named target user, using this product, know this worked?"* Outcome-only. Every step must be performable by that user within the limits of their declared tooling/interaction surface. End-user (client) targets: only actions through the shipped product. Internal-team targets: only actions inside the team's declared surface. No implementation details, no test names, no methods. The brief intentionally does **not** name an implementation method (`preview` / `cli` / `tdd` / `integration-test` / `post-hoc`) — that choice belongs to execution-plan, derived from these steps plus integration-risk class. Naming a method here would bias downstream review and limit honest test selection. Reviewers flag any deliverable missing user-facing acceptance steps.
6. **No implementation leakage in §2 or §5.** Deliverable descriptions, acceptance steps, and HARD DECISION rows must not name a specific library, package, file path, function name, framework feature, data structure, algorithm, schema column, wire-format detail, or test artifact. The forbidden altitude is anything a non-engineer wouldn't recognize from using the product. **Allowed at strategic altitude:** the named target user's interaction surface; couplings of the form "shared with component X" or "reuses the existing X model" (component identity is allowed, technique is not); the user-observable thing itself, if that thing IS a specific tool/skill being adopted. Implementation belongs in execution-plan, not the brief.
7. **HARD DECISIONs are explicit AND stay at strategic altitude.** A PM statement with tight language ("must," "non-negotiable," "only way") becomes a `[HARD DECISION]` row and cannot be reversed by reviewers downstream. Each HARD DECISION must be one of: (a) a user-observable behavior the PM is locking in; (b) a coupling at "shared with component X" altitude; (c) a PM-verbatim constraint. A HARD DECISION must not name a specific library/package/technique unless that technique is itself the user-observable thing being decided.
8. **Compact decision rows.** One line each. Full tradeoff tables only for items marked `[HARD DECISION]` or when the PM explicitly asks for one.
9. **Conversational feedback.** In revise mode, the PM's feedback arrives in chat (not as edits to the brief file); the drafter applies it and re-emits the brief record. The brief is output-only and is never hand-edited to convey feedback.
10. **Working backwards is section 1.** The release-note paragraph is written before any deliverables are listed. If clarify passed `working-backwards: TBD`, write `TBD — open question` verbatim — do not fabricate one. Same rule for `success-signal: TBD`.

---

## Mode: draft

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

You receive:
- The clarified request (output of `clarify`)
- Document locations: architecture doc, UX/PMF doc, security policy, schema/ERD (whatever `clarify` collected)
- Autonomy level (`supervised` | `auto` | `yolo`) — affects tone of open-decisions section only

Compute the feature folder: `docs/strategic-implementation/<today-YYYY-MM-DD>-<slug>/`. Create the folder. Write the brief to `product-brief_<slug>.md` inside it.

### Brief structure

```markdown
# Product Brief: <Feature Name>
_Slug: <slug> · Date: <YYYY-MM-DD> · Autonomy: <level>_

## 1. Working backwards (≤5 sentences, release-note voice)
> <One paragraph in release-note voice — "the X now does Y," not "we will build." Describes what the user observably gets if this shipped tomorrow. ≤5 sentences. If clarify passed `working-backwards: TBD`, write "TBD — open question" verbatim and do not fabricate.>

## 2. What the user does / sees

**Who is the user of this feature:** <Name a concrete audience — a specific segment of the product's userbase, an internal team, a role. For internal-team users, also name the team's interaction surface (a specific skill, Claude Code, a dashboard, a shared doc, a CLI). Write `TBD — open question` verbatim only if the user is genuinely ambiguous; do not fabricate.>

For each deliverable, write the user-observable description and the acceptance steps the named user above would take to confirm it works, within the limits of their declared tooling/interaction surface. No implementation methods, no test names — outcome-only steps the named user could perform.

### D1 — <one-sentence user-observable description>
**How a user verifies:**
1. <Concrete action the named user takes within their interaction surface — open page X, run feature Y from the UI, observe field Z>
2. <Next step / observation>
3. <...continue until the outcome is unambiguously confirmed>

### D2 — <...>
**How a user verifies:**
1. ...

## 3. Success signal
<Names a thing observable from outside the system — a query, a behavior, a metric. NOT "the deliverable shipped"; deliverable-shipped is covered by §2's per-deliverable user-acceptance steps. The success signal is outcome-level: a single thing that, observed from outside, says the feature is working in aggregate. If clarify passed `success-signal: TBD`, write "TBD — open question" verbatim.>

## 4. Boundaries
**In scope:** <bulleted>
**Out of scope:** <bulleted — what we deferred or won't do this round>
**Anti-goals (philosophy-level — we deliberately will not):** <bulleted — temptations we'd reject even if free; not the same as out-of-scope. Out-of-scope = "not now"; anti-goals = "we'd reject this even if free.">

## 5. Decisions
| Decision | Choice | Status |
|---|---|---|
| <one line> | <choice> | `[HARD DECISION]` or `settled` or `open` |

<!-- For HARD DECISIONs only, add a tradeoff table below each -->

## 6. Risks & unknowns
- Bulleted. If a risk is large, name it and who owns resolution.

## 7. References & revision log
**Document references:**
- Architecture: <path or "none">
- UX/PMF: <path or "n/a — backend only">
- Security policy: <path or "none">
- Schema/ERD: <path or "n/a — no data storage">

**Revision log:**
- v0.1 · <date> · initial draft
```

### After writing

Run the **Leakage gate** (see below) before announcing to the PM. The gate runs the fast leakage reviewer against the freshly written brief. The announcement and path-return are gated on PASS or explicit PM override.

After leakage gate PASS, also emit the **specialist recommendation sidecar** (see below) — `brief-meta.yaml` in the feature folder. This is the drafter's narrow hint to `review` about which specialists the brief actually warrants; it bypasses the trigger-token pre-filter's tendency to over-trigger.

On PASS, return the absolute path to the brief and announce:

> "Product brief drafted at `<path>`. Review it (open the local mirror via the store cache); describe any revisions in chat and I'll re-emit it, or reply 'approve' to proceed to execution planning."

Do NOT auto-advance. The PM approves the brief explicitly.

---

## Leakage gate (both modes)

Invoke the fast leakage reviewer after writing the brief, before the PM announcement. The reviewer is invoked inline via the `Agent` tool with `model: "sonnet"` (no standalone agent file). Inline prompt:

> You are a fast leakage reviewer for product briefs. Your only job is to find implementation details that leaked into a brief that should be implementation-agnostic.
>
> Read the brief at `<brief-path>` in full.
>
> **What counts as leakage (FLAG)** — a phrase in §1 (Working backwards), §2 (What the user does / sees, including the target-user line, deliverables, and acceptance steps), §3 (Success signal), §4 (Boundaries), or §5 (Decisions / HARD DECISIONs) that names any of:
> - a specific library, package, framework, or runtime;
> - a specific file path, module path, function name, class name, or symbol;
> - a specific algorithm or data structure;
> - a specific API/endpoint shape, schema column, or wire format;
> - an internal artifact a non-engineer wouldn't recognize from using the product;
> - a test name, test file, or test framework reference;
> - an implementation technique below the "shared with component X" altitude.
>
> **Allowed (do NOT flag):**
> - the named target user and their declared interaction surface (required content);
> - couplings of the form "shared with component X" or "reuses the existing X model";
> - a phrase that IS the user-observable thing being decided (e.g., the brief is literally about adopting a specific tool as the user-facing thing);
> - §6 (Risks & unknowns) and §7 (References & revision log) — these sections may name files/paths/agents;
> - any "Affected skill files" subsection of §7 — explicitly internal plumbing.
>
> **Subject-matter caveat.** If the brief's *product* is a skill, an agent, or some specific internal tool, then references to those skills/agents in §1–§5 are the user-observable things being decided — not leakage. However, naming a *different* tool used to IMPLEMENT them (e.g., "uses library X for the reviewer") is still leakage.
>
> Return a terse JSON object (cap ~600 tokens):
> ```json
> { "status": "PASS | FLAG",
>   "findings": [ { "section": "§N or deliverable id", "line_excerpt": "...", "why_leakage": "one sentence" } ],
>   "notes": "one-sentence overall judgment" }
> ```

**Gate semantics.**

- **PASS:** proceed to the PM announcement.
- **FLAG:** surface findings to the PM with line excerpts.
  - In `auto`/`yolo`: drafter MAY attempt one self-revision pass on obviously safe findings (e.g., swap a specific library name for "shared with component X" framing) before surfacing the remainder. Self-revision counts as a brief edit and appends a revision-log entry. After self-revision, re-run the gate once; whatever findings remain go to the PM.
  - In `supervised`: do not self-revise; surface findings as-is.
- The drafter never returns the success announcement (and never returns a brief path as "ready for execution-plan") until status is PASS.
- If the PM explicitly overrides a finding ("override this — `<one-line justification>`"), append the justification to §7 revision log and treat the finding as resolved. Override protocol is intentionally minimal; richer override syntax may be added when needed.

**Fallback.** If the `Agent` tool's `model` override is unavailable at call time, invoke with the default model and the same prompt — slower but functionally equivalent. The discipline still holds.

---

## Specialist recommendation sidecar (both modes)

After the leakage gate PASSes, write `brief-meta.yaml` to the feature folder alongside the brief. This sidecar is **not** PM-facing — it is consumed by `execution-plan` and forwarded to `review` to narrow specialist selection. The brief itself stays PM-clean.

### Sidecar format

```yaml
# Internal metadata for review. Not PM-facing.
specialists_recommended:
  - <one of: boundaries, runtime-risk, frontend-engineer, technical-expert>
notes: <one sentence explaining the selection>
```

`tests` is always run by `review` and is not listed here. Omit `specialists_recommended:` entirely (or leave empty list) when no specialist warrants explicit recommendation — the pre-filter still applies its mandatory triggers.

### Selection rule

Recommend a specialist only when the brief itself names a concern in that specialist's domain. The bar is "the brief talks about this," not "this might be relevant downstream."

| Specialist | Recommend when the brief explicitly names |
|---|---|
| `boundaries` | auth/permission/role surfaces, new endpoints, schema changes, secrets/credentials/PII handling, externally-reachable surfaces |
| `runtime-risk` | non-trivial dependencies (especially those from clarify's integration-risk list), caching/queues/background work, hot paths, latency-sensitive surfaces |
| `frontend-engineer` | a new screen, a flow with ≥2 user-visible steps, an information-architecture change, or a UI mockup was produced |
| `technical-expert` | adoption of a new library/framework/runtime, or a step-ordering risk the brief itself surfaces |

Default to **fewer** recommendations. An empty list is the correct answer for backend-only refactors or single-control UI tweaks. Over-recommendation is the failure mode this sidecar exists to prevent.

---

## Mode: revise

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

You receive:
- Path to the existing brief
- PM feedback, given conversationally in chat

Steps:
1. Read the brief (via the store cache / `store.sh read`).
2. Apply each point of the PM's chat feedback to the brief.
3. (merged into step 2 — all feedback is conversational.)
4. Append a revision-log row: `- v0.N · <date> · <one-sentence summary of what changed>`.
5. Write the brief back.

### Discipline in revise

- Never silently expand scope. If the PM's feedback implies a new deliverable, add it explicitly with its own user-facing acceptance steps and flag the change in the revision log.
- Never reverse a `[HARD DECISION]` without the PM stating it plainly. If feedback conflicts with a hard decision, surface the conflict in the revision log and ask the PM to confirm before reversing.
- If feedback is ambiguous, leave a `<!-- drafter: <question> -->` comment in place rather than guessing.

### After revising

Run the **Leakage gate** (see above) before announcing to the PM. The gate must PASS (or the PM must override remaining findings) before the announcement.

If the revision changed scope (added/removed a deliverable, changed an interaction surface, added a HARD DECISION, added/removed an integration-risk-relevant dependency), refresh `brief-meta.yaml` per the **Specialist recommendation sidecar** section. Otherwise leave the sidecar as-is.

On PASS, return the path and announce:

> "Brief revised (v0.N). Review inline or reply 'approve' to proceed."

---

## Handoff

The orchestrator waits for PM approval. On approval, the orchestrator invokes `execution-plan` with:
- Brief path
- Feature folder path
- Autonomy level

---

## Record routing — externalized artifact store

Per-feature **records** (brief / plan / validation-log / checkpoint / reports / mockup / brief-meta) route through the store adapter, not the feature folder directly: wherever a step says write/read `<feature-folder>/<file>`, use the store address `<repo-id>/<date-slug>/<file>` with in-repo fallback. Full read/write/fallback protocol: [`scripts/store/README.md`](../../scripts/store/README.md#record-routing-protocol-agent-facing). **Durable tier — `project-learnings.md`, `documentation-registry.md` — stays in-repo, never routed to the store.**
