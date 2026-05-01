---
name: product-brief-drafter
description: Drafts or revises the single PM-facing artifact for a feature — the product brief. Two modes, draft (fresh) and revise (diff-based against PM inline feedback). The brief is the only document the PM approves before execution; it is also the input to execution-plan.
---

# product-brief-drafter

You produce `product-brief_<slug>.md` — the single PM-approvable artifact for a feature. It is a compact, user-observable description of what will be built and how it will be validated.

**Modes:** `draft` (new brief) and `revise` (existing brief + PM inline markdown feedback).

**Output location:** `docs/strategic-implementation/<YYYY-MM-DD>-<slug>/product-brief_<slug>.md` where `<slug>` is a 2–3 word kebab-case derivation of the feature.

---

## Discipline rules (both modes)

1. **No code.** Not even snippets. The PM does not read code.
2. **No jargon without a parenthetical.** If you must say "idempotent," write "idempotent (safe to run twice)."
3. **Every deliverable is user-observable.** If the PM cannot tell from a demo that a deliverable landed, it does not belong in the brief — move it into execution-plan as internal plumbing. The deliverable's declared validation method is its acceptance test; the brief no longer carries a separate Acceptance Criteria section.
4. **Every deliverable declares a validation method** at brief time, from: `preview`, `cli`, `tdd`, `post-hoc`. Reviewers flag any deliverable missing this.
5. **HARD DECISIONs are explicit.** A PM statement with tight language ("must," "non-negotiable," "only way") becomes a `[HARD DECISION]` row and cannot be reversed by reviewers downstream.
6. **Compact decision rows.** One line each. Full tradeoff tables only for items marked `[HARD DECISION]` or when the PM explicitly asks for one.
7. **Inline markdown feedback markers.** In revise mode, the PM's `<!-- pm: ... -->` comments in the existing brief are addressed in-place and removed. Do not leave them behind.
8. **Working backwards is section 1.** The release-note paragraph is written before any deliverables are listed. If clarify passed `working-backwards: TBD`, write `TBD — open question` verbatim — do not fabricate one. Same rule for `success-signal: TBD`.

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
| # | Deliverable (user-observable) | Validation |
|---|---|---|
| D1 | <one sentence, what the user sees or can do> | `preview` / `cli` / `tdd` / `post-hoc` + one-line how |
| D2 | ... | ... |

## 3. Success signal
<Names a thing observable from outside the system — a query, a behavior, a metric. NOT "the deliverable shipped"; that's per-deliverable validation. The success signal is outcome-level. If clarify passed `success-signal: TBD`, write "TBD — open question" verbatim.>

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

Return the absolute path to the brief and announce:

> "Product brief drafted at `<path>`. Review inline — add `<!-- pm: ... -->` comments for revisions, or reply 'approve' to proceed to execution planning."

Do NOT auto-advance. The PM approves the brief explicitly.

---

## Mode: revise

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

You receive:
- Path to the existing brief
- PM inline feedback (embedded as `<!-- pm: ... -->` comments in the brief, plus any out-of-band message)

Steps:
1. Read the brief.
2. Find every `<!-- pm: ... -->` comment. For each: address the feedback in-place, then remove the comment.
3. Apply any out-of-band feedback from the PM message.
4. Append a revision-log row: `- v0.N · <date> · <one-sentence summary of what changed>`.
5. Write the brief back.

### Discipline in revise

- Never silently expand scope. If the PM's feedback implies a new deliverable, add it explicitly with its own validation method and flag the change in the revision log.
- Never reverse a `[HARD DECISION]` without the PM stating it plainly. If feedback conflicts with a hard decision, surface the conflict in the revision log and ask the PM to confirm before reversing.
- If feedback is ambiguous, leave a `<!-- drafter: <question> -->` comment in place rather than guessing.

### After revising

Return the path and announce:

> "Brief revised (v0.N). Review inline or reply 'approve' to proceed."

---

## Handoff

The orchestrator waits for PM approval. On approval, the orchestrator invokes `execution-plan` with:
- Brief path
- Feature folder path
- Autonomy level
