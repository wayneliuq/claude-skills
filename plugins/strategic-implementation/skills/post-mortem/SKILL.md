---
name: post-mortem
description: Reviews deviation logs from a completed session, synthesizes learnings, updates project-learnings.md, and writes a session post-mortem artifact. Triggered by executing-plans or manually by the user.
---

# Post-Mortem

Reviews the deviation log for a completed session, cross-references existing learnings, synthesizes new or expanded learning candidates, presents them for user approval, then writes `session-N-postmortem.md` and updates `project-learnings.md`.

---

## You Receive

**When invoked by executing-plans:**
- Feature folder path
- Session number N
- Session plan path
- Deviation log path (or `none` if clean execution)
- Implementation guide path

**When invoked manually:** ask the user for each of the above.

---

## Step 1 — Check for Deviation Log

If deviation log path is `none` or the file does not exist:
> "Session N: clean execution — no deviations logged. No post-mortem needed."

Exit. Do not continue.

Load the deviation log.

---

## Step 2 — Load All Context

Read in full:
- Session plan (`session-N-plan.md`)
- Implementation guide (`implementation-guide.md`)
- `<feature-folder-path>/spec.md`
- `docs/strategic-implementation/project-learnings.md` — if absent, note "no prior learnings" and treat as empty

---

## Step 3 — Count Total Session Logs

Count all `session-*-log.md` files across all feature folders:
`docs/strategic-implementation/*/session-*-log.md`

Store the count. If count < 3: skip Step 7 (cross-session grep). If count ≥ 3: Step 7 runs.

---

## Step 4 — Per-Deviation Analysis

For each `DEV-NNN` entry in the deviation log, note:
- Agent category tag
- Plan gap? value
- Downstream impact? value
- One-sentence summary of what this deviation reveals about planning or execution

---

## Step 5 — Review Existing Learnings

From `project-learnings.md`, extract learnings whose agent category matches any category from Step 4.

For each applicable learning, check: was the WHEN condition present in this session plan?
- **Yes, DO guidance followed:** record as `[L-NNN] ✓ applied — [brief note]`
- **Yes, DO guidance absent or violated:** record as `[L-NNN] not applied — [what happened instead]`
- **No (WHEN condition not present):** skip

---

## Step 6 — Synthesize Learning Candidates

For each deviation (or cluster of related deviations), determine:

**a) New learning candidate**
- Situation not covered by any existing learning
- Format: `WHEN [specific situation], DO [specific action]`
- Tag: `#single-session` (new learnings always start here)
- Evidence: this deviation

**b) Expansion candidate**
- An existing learning this deviation extends
- **Expansion rule:** change WHEN (broader situation) OR DO (refined action) — NEVER both simultaneously
- Valid only when this deviation is a second concrete case (the original learning had one; this is the second)
- Show: existing learning, proposed change (exactly which part changes), both evidence references

**c) Conflict candidate**
- This deviation's evidence contradicts an existing learning
- Show: existing learning text, contradicting evidence, recommendation (keep / modify / retire)
- User decides — do not pre-apply

If a deviation is a pure execution error (typo, environment issue, nothing recurring): note "no learning candidate — [reason]"

---

## Step 7 — Cross-Session Grep (only if total log count ≥ 3)

From each deviation in this log, extract 2–3 keywords from "What actually happened".
Search for those keywords across all other `session-*-log.md` files.

If a keyword pattern appears in 2+ other sessions: flag it as a potential multi-session pattern with the matching sessions listed. This is advisory — it does not automatically promote a learning to `#multi-session`. Promotion requires explicit user confirmation.

---

## Step 8 — Check Implementation Guide for Missed Updates

Re-read Session N's `#### Meaningful Deviations` block.
Compare against deviation log entries where `**Downstream impact?** yes`.

If any `downstream-impact=yes` deviation is not in the Meaningful Deviations block: add it now.
If any downstream session is missing a `⚠️ REVISION NEEDED` flag it should have: add it now.

---

## Step 9 — Present to User

Present before writing anything to disk:

```
## Post-Mortem: Session N — [session name]
Date: YYYY-MM-DD

### Existing Learning Application
[L-NNN ✓ applied / not applied notes, or "No applicable existing learnings."]

### Proposed Learning Updates
[For each candidate — New / Expansion / Conflict — show learning text, evidence, and for expansions: before/after]

### Cross-Session Patterns (if Step 7 ran)
[Pattern and session references, or "None identified."]
```

Ask: "Approve these updates? You can approve all, individually, or reject any. Conflicts require a decision."

Wait for response before writing.

---

## Step 10 — Write Artifacts

**Write `<feature-folder-path>/session-N-postmortem.md`:**

```markdown
# Session N Post-Mortem: [session name]
_Feature: [feature folder name]_
_Date: YYYY-MM-DD_
_Deviations reviewed: [count]_

## Learning Application
[From Step 5]

## Approved Learning Updates
[Each approved candidate with L-NNN reference]

## Rejected Candidates
[Any rejected, with reason if given]

## Cross-Session Patterns
[From Step 7, or "Not applicable — fewer than 3 sessions logged."]

## Implementation Guide Updates
[Meaningful Deviations or REVISION NEEDED flags added in Step 8]
```

**Update `docs/strategic-implementation/project-learnings.md`:**

If file does not exist, create it with this header:

```markdown
# Project Learnings
_Last updated: YYYY-MM-DD_
_Sessions tracked: 1_

> **Tag semantics:**
> - `#single-session`: applied only during session plan review. One session of evidence.
> - `#multi-session`: applied during both implementation guide review and session plan review.
>   Promoted from `#single-session` when expanded with evidence from a second session.
>   Requires explicit user confirmation.
>
> **Expansion rule:** Change WHEN (broader situation) OR DO (refined action) — never both simultaneously.
> An expansion requires citing a second concrete case as evidence.
>
> **Pruning rule:** Prune only if the referenced component/pattern no longer exists or has changed
> so fundamentally that the learning is misleading. Requires explicit user confirmation.

---
```

For each approved **new** learning: append under the appropriate `## [category] Learnings` heading. If no section for this category exists yet, create it first:

```markdown
## [category] Learnings
```

Then append the entry:

```markdown
### L-NNN: [Short title]
**WHEN** [specific situation], **DO** [specific action]
**Tags:** `#[agent-category]` `#single-session`
**Source:** [feature folder name, session N]
**Evidence:** [1–2 sentences on what deviation led to this]
**Last reviewed:** YYYY-MM-DD
**Application notes:**
```

For each approved **expansion**: update the existing entry's WHEN or DO (not both); append new evidence to Evidence field; update `**Last reviewed:**`. If user confirmed it's now `#multi-session`, update the tag.

For each approved **conflict resolution**: apply user's decision (keep / modify / retire).

Update `_Sessions tracked: N_` and `_Last updated: YYYY-MM-DD_` at top.

---

## After Step 10

Invoke `superpowers:finishing-a-development-branch`.
