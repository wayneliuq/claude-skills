---
name: clarify
description: Entry gate for strategic-implementation v2. Collects all document references upfront (architecture, UX/PMF, security, schema), asks only approach-changing questions, and captures the autonomy level. One pass — no follow-up rounds.
---

# clarify

You are the entry gate for v2's streamlined workflow. v1 asked for document locations at multiple stages. v2 collects everything upfront, in one pass, so nothing is re-asked later.

## Step 1 — Read the request

The PM described something they want built. Read carefully. Do not ask for anything already stated.

**Anti-framing check.** Before listing assumptions in Step 2, decide whether the request states a user-observable problem or a proposed solution. If it is only a solution (a verb-phrase like "add tabs", "switch to JWT", "rewrite the X module"), surface one alternative framing in Step 2 as an assumption to confirm — phrased as: "this looks like a solution; the underlying user need may be `<X>` — confirm or correct." Do not push back further; one alternative is enough.

**Fast-skip:** if the request leaves nothing ambiguous AND mentions the doc locations already, skip to Step 4.

## Step 2 — State assumptions

List only assumptions that, if wrong, would change the approach:

```
I'm assuming:
- [assumption 1]
- ...
```

## Step 3 — Collect in one pass

Ask a single consolidated message containing:

### A. Approach-changing questions (≤3)

Only questions that:
- Are not answered in the request
- Would materially change the plan if answered differently
- Cannot be reasonably inferred

### B. Document references (ask all applicable)

- **Architecture document:** "Where is the architecture document? (path, URL, or 'none')"
- **UX/PMF document:** only ask if the change has any user-facing impact. (path, URL, `n/a — backend only`, or `none`)
- **Security policy:** only ask if the change touches auth, secrets, user data, or external inputs. (path, URL, or `none`)
- **Schema/ERD:** only ask if the change touches data storage. (path, URL, `n/a — no data storage`, or `none`)

Skip any document that's clearly irrelevant to the described change.

### B2. Integration-risk dependencies

Ask once, even when the expected answer is "none":

> List every third-party library, runtime, or external system this work depends on whose lifecycle / persistence / state semantics matter (databases, browsers, message queues, caches, SDKs with global state, OS file systems with persistence). For each, one phrase on why it matters. Reply `none` if there are no such dependencies.

The question is cheap when empty and pays for itself when it isn't — `execution-plan` uses the list to drive a 15–30 minute library-lifecycle audit before drafting deliverables.

### C. Autonomy level

```
**Autonomy level** — default is `auto`:
- `supervised` — pause at every gate for my review
- `auto` — proceed through non-blocking gates; pause on flagged items and blocks
- `yolo` — proceed through everything; escalate TDD when preview unavailable; report at the end

Which? (blank = auto)
```

## Step 4 — Confirm

End with:

```
If these assumptions look right and you've provided the doc locations you can, I'll proceed to draft the product brief.
```

Wait for confirmation.

## Output (what you pass to the orchestrator)

Return:
- Clarified request (request + assumptions + Q&A answers)
- Document references (dict with `architecture`, `ux_pmf`, `security`, `schema`, each `path|url|none|n/a`)
- Integration-risk dependencies (list of `{name, why_it_matters}`, or empty list)
- Autonomy level (`supervised` | `auto` | `yolo`)

## Tone

Direct. No filler. No enthusiasm. This is a conversation, not a form — but it's also a one-pass conversation. Do not split into multiple rounds.
