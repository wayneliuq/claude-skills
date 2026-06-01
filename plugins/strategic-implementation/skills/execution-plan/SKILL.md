---
name: execution-plan
description: Drafts the execution plan for an approved product brief inside Claude Code plan mode, invokes the review skill to critique the draft, patches the plan with review findings, and exits plan mode on PM approval. The execution plan — not the brief — is what the agent panel reviews.
---

# execution-plan

You convert an approved product brief into a concrete, file-level execution plan. The plan is drafted, reviewed, and approved inside **Claude Code plan mode** — plan mode's native UI is the approval gate.

You receive:
- Brief path (`.../product-brief_<slug>.md`)
- Feature folder path
- Integration-risk dependencies (from clarify; may be empty)
- Mockup path (optional; provided by orchestrator when ui-mockup ran)
- Autonomy level (`supervised` | `auto` | `yolo`)

---

## Step 1 — Enter plan mode

Your **first tool call** is `EnterPlanMode`. Do no work before entering plan mode — subsequent work benefits from plan mode's prompting.

If the environment does not support `EnterPlanMode` in this context, fall back: draft outside plan mode, but still present the final plan as the approval gate (see Step 5 fallback).

---

## Step 2 — Read brief + survey repo

Inside plan mode:

0. **Graph health pre-flight.** Call `mcp__code-review-graph__list_graph_stats_tool`. If the graph is empty (`total_nodes: 0`) or `last_updated` lags the working tree by more than a day, emit `FLAG: graph stale (last-built: <ts>; nodes: <n>)` and continue with file-read mode for this run. If healthy, prefer graph queries throughout Step 2.
1. Read the brief end-to-end. Extract: deliverables (D1…Dn), each deliverable's **user-facing acceptance steps** (the outcome contract — what a human does to confirm it works), the success signal, scope boundary (in / out / anti-goals), hard decisions, document references. The brief deliberately does NOT specify an implementation method (`preview` / `cli` / `tdd` / `integration-test` / `post-hoc`); execution-plan chooses the method, driven by the user-acceptance steps and the integration-risk class. _(Note from v3.2.1: brief no longer carries a separate Acceptance Criteria section — each deliverable's declared validation method is its acceptance test, and the Success signal section names the outcome-level check.)_
2. For each deliverable, identify the concrete files likely to change. **Prefer code-review-graph queries** (`semantic_search_nodes` to find the symbol, `query_graph` for callers/callees/imports/tests, `get_architecture_overview` for module shape, `get_impact_radius` for blast radius); fall back to **Glob** / **Grep** / **Read** only when the graph cannot answer. Verify file paths via Glob before citing them. Unverified paths get `[PATH NOT FOUND]` annotations. Cite graph results as concrete symbols (`function foo at path/file.py:42`, "callers: `bar`, `baz`") rather than paraphrased file content.
3. **Library-lifecycle doc pass.** For each integration-risk dependency from clarify, locate the canonical persistence / lifecycle doc (project README, vendor docs, RFC, or in-repo notes). Read the relevant section. Capture: what state persists across what boundaries (per-connection / per-session / per-process / per-deployment), known gotchas, and the doc URL/path. Time-box: aim for 15–30 minutes total across all libraries; if a library has no good docs, note that explicitly. Empty audit is acceptable only if clarify declared `none`.
4. **Load the documentation registry.** Read `docs/strategic-implementation/documentation-registry.md` if present. For each registry entry, judge whether the deliverables in this brief might invalidate it (touches the path, the area, or the update-trigger condition). Tag each deliverable with `may-invalidate: [doc-paths]` or `may-invalidate: none`. Surface the union of impacted entries in the plan summary at Step 5 so the PM sees what docs this work will require updating.
5. Load `docs/strategic-implementation/project-learnings.md` if it exists. Filter entries for relevance to this brief's deliverables. Inject matching entries when invoking `review`.
6. **Validation-approach recall.** For deliverables that will be cross-domain (`Macro-deliverable`) or `Integration-risk class: a|b|c`, query memory for how similar work was validated before, replacing the former N-most-recent `grep` with a ranked, status-filtered recall over the whole indexed history:

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/memory/recall.sh" "<brief domains + integration-risk class + validation intent>" --domains "<domains>" --k 3
   ```

   This runs once per plan (not per deliverable), so it may use the richer query path (BM25 now; BM25+vector fusion once the vector leg is enabled). It returns ranked distilled approaches with source pointers, drawn from the full corpus and matched by meaning, not just recency or exact wording — and never surfaces aborted/superseded work as precedent. Surface any hits as **advisory** input to the Step 3 validation-method choice (reuse a proven pipeline instead of re-guessing). This is advisory only — it informs, never dictates, the method. Empty output (no index yet, or no good match) → proceed silently (no error, no block). The command degrades to silence on any error.
7. **Load brief sidecar.** Read `<feature-folder>/brief-meta.yaml` if present. Capture `specialists_recommended:` — this list is forwarded to `review` to narrow specialist selection. Absent sidecar or empty list → forward an empty list; `review`'s pre-filter still applies mandatory triggers.

---

## Step 3 — Draft execution plan

Draft the plan using the template below. The plan is structured as a **DAG of deliverables**, not a sequence of sessions.

```markdown
# Execution Plan: <feature name>
_Implements: product-brief_<slug>.md · Date: <date>_

## Context
<2–3 sentences restating what this plan delivers, tying each deliverable back to the brief.>

## Library lifecycle audit
<One subsection per integration-risk dependency from clarify. Omit the section entirely only if clarify declared `none`. A generic "we'll handle errors gracefully" is not an audit — concrete persistence/scope semantics are.>

### <library / runtime / external system name>
- **State that persists:** <what state, scoped to what boundary — e.g. "TEMP TABLE rows live for the lifetime of one DB connection; dropped on disconnect">
- **Quirks / gotchas:** <known surprises — e.g. "persisted DB on disk and runtime VFS are not auto-synced; explicit flush required">
- **Doc consulted:** <URL or in-repo path>

## Deliverables (DAG)

### D1 — <name>
- **Integration-risk class:** <a | b | c | d>
  - `a` — depends on a third-party runtime / SDK with non-trivial lifecycle
  - `b` — depends on real browser / network behavior
  - `c` — depends on cross-component reactive state coordination
  - `d` — none of the above
- **User-acceptance steps (from brief):** <numbered list copied verbatim from the brief's "How a user verifies" for this deliverable — the outcome contract>
- **Macro-deliverable:** <true | false — see authoring rule "Macro-deliverable (narrow exception)". Default false.>
- **Domains & file partition:** <if Macro-deliverable: true, list each domain → its disjoint path-set (authored AND generated outputs); else `n/a`>
- **Validation method (chosen here):** <preview | cli | tdd | integration-test | post-hoc> — <exact command / exact behavior to observe / exact test to write>. Must be the method whose evidence actually demonstrates the user-acceptance steps above.
- **Files:** <specific paths; use [PATH NOT FOUND] if unverified>
- **Steps:** <numbered; each names file(s) and what to write/change/delete>
- **Deps:** <other D-ids, or "none">
- **Pre-flight env check:** <what must be available to run the validation — e.g. dev server, DB migration applied, credentials present>
- **may-invalidate:** <bracketed list of registry doc paths this deliverable might invalidate, or `none`. Surfaces here so executing-plans bundles doc updates into the deliverable's atomic commit.>
- **Visual contract:** <mockup file path if a UI mockup was approved upstream, else `n/a`. Implementation must match this mockup; post-execution prompts a manual visual diff.>
- **Consumer audit:** <required iff this deliverable changes a data shape — interface / type / schema / payload / return type / function signature. Otherwise: "n/a — no shape change.">
  - <consumer file:symbol> — `updated-in-this-deliverable` | `updated-in-D<n>` | `unaffected-because-<reason>` | `explicit-skip-because-<reason>`
  - ...

### D2 — <name>
...

## Parallel groups & order
<textual DAG — which groups run in parallel, which are sequential>

### Workflow decision
<one line per macro-deliverable: name it, state which criteria (a–d) qualify it and why splitting would lose e2e-validateability. This is the plan-time half of the operator-visible workflow-vs-sequential decision. If no macro-deliverable: "none — all deliverables decomposable / sequential.">

## Reused existing patterns
<bulleted — point to existing repo primitives being reused. Prevents duplicate abstractions.>

## Risks & contingencies
<bulleted — what could go wrong, and the fallback>

## Out of scope for this plan
<bulleted — explicit exclusions from the brief's scope boundary>
```

### Authoring rules

1. **One deliverable = one user-observable outcome.** Do not create deliverables for "internal plumbing" unless the plumbing is itself a validation gate.
2. **No LOC budgets.** Size is not a gate in v2. Fitness is a gate.
3. **Validation method honesty.** Choose the method whose evidence actually proves the deliverable's user-acceptance steps. If the steps require visual confirmation, `preview` or `post-hoc` — not `tdd`. If the steps name observable behavior under real I/O, `integration-test` — not `tdd` with a mocked seam. If the chosen method cannot reproduce the user's verification flow, it is wrong. **For a `Macro-deliverable: true` deliverable, the method must prove the INTEGRATED cross-domain outcome end-to-end — never a single domain in isolation.**
4. **Preview-unavailable fallback.** For `preview`-validated deliverables: in `supervised`/`auto`, pause for PM manual validation if the preview tool can't run; in `yolo`, auto-escalate to TDD and proceed.
5. **Verify paths.** Every file path must be confirmed via Glob before the draft is presented for review.
6. **Reuse before creating.** Grep for existing primitives; cite them in "Reused existing patterns."
7. **Validation honesty per integration-risk class.** Class `a`/`b`/`c` deliverables MUST declare validation as `integration-test`, `preview`, or `post-hoc`. They MUST NOT declare `tdd` if the proposed test would mock the very dependency the deliverable's correctness depends on. Class `d` may use any method. A green unit-test suite that mocks the integration point is not validation — it is orthogonal-to-correctness coverage. A `Macro-deliverable` is treated as integration-risk for this rule: its method must exercise the cross-domain seam, not per-domain mocks.
8. **Consumer audit on shape change.** Any deliverable that changes a data shape (interface / type / schema / payload / return type / function signature) MUST grep its consumers and list every one with a status (`updated-in-this-deliverable`, `updated-in-D<n>`, `unaffected-because-<reason>`, `explicit-skip-because-<reason>`). Hand-wavy enumeration is rejected by review.
9. **Macro-deliverable (narrow exception).** Default is normal decomposition — split work into the smallest independently-validateable deliverables. A deliverable may be marked `Macro-deliverable: true` ONLY when ALL hold: (a) the outcome spans ≥2 domains (commonly backend / API-contract / frontend); (b) the domains are NOT independently end-to-end-validateable — splitting them loses the ability to validate any sub-part e2e; (c) together they form ONE user-observable outcome; (d) it is large enough that concurrent build meaningfully beats sequential. PLUS an eligibility gate: the domains must own **disjoint file sets — authored AND generated/derived outputs** (no two domains write the same lockfile / index / generated artifact). Expected domain count is small (≤ ~4). If work *can* be split into independently-validateable pieces, it MUST be — a macro-deliverable is not a license to skip honest decomposition. A macro-deliverable IS one deliverable → one atomic `D<n>:` commit (executing-plans runs its domains in one Workflow). Record it in the template's `Macro-deliverable` / `Domains & file partition` fields and name it under "Workflow decision".

---

## Step 4 — Invoke review

Still inside plan mode, invoke `strategic-implementation:review` with:
- The full plan text
- The brief path
- The document reference locations from the brief
- The filtered project-learnings block (if any)
- `specialists_recommended:` from `brief-meta.yaml` (may be empty list)
- Autonomy level

The `review` skill runs tiered: `alignment` + `simplify` first, then specialists on flags. It returns a consolidated JSON patch list and status.

### Handling review output

- **BLOCK:** Surface the block to the PM inside plan mode. Do not patch. Ask: "resolve by revising brief, or override?"
- **FLAGs + RECOMMENDATIONs:** Apply high-severity patches silently. Present medium/low patches as a numbered list — PM can accept all / reject all / pick.
- **ALTERNATIVE (from simplify):** Present the alternative path. Ask PM whether to rewrite or proceed.

After patches applied, re-run the consistency check (every brief deliverable still covered; the success signal still mappable; no orphan deliverables; no broken DAG edges).

---

## Step 5 — Present for approval

Present the patched plan via plan mode's native UI. The plan must end with an explicit final step so that, if the PM approves via plan-mode's button, the hand-off is committed:

```
Final steps on approval:
1. Save execution plan → <feature-folder>/execution-plan.md
2. Exit plan mode
3. Invoke strategic-implementation:executing-plans
   - Execution plan path: <feature-folder>/execution-plan.md
   - Feature folder path: <feature-folder>/
   - Autonomy level: <level>
```

### Fallback (plan mode not entered)

If Step 1's `EnterPlanMode` call was not supported, present the plan as a normal inline message with this exact trigger callout:

> **Ready to execute.** Reply `go`, `execute`, or `start` to begin. Describe changes to revise.

---

## Step 6 — On approval

1. Save to `<feature-folder>/execution-plan.md`.
2. Call `ExitPlanMode` (if in plan mode).
3. Invoke `strategic-implementation:executing-plans`, passing execution plan path, feature folder path, autonomy level.

---

## Revision loop

If the PM rejects or requests changes: stay in plan mode, apply changes, re-run consistency check, re-present. Only re-invoke `review` if the changes are substantial (new deliverable added, dep introduced, hard decision touched).

---

## Tone discipline

Terse. Substance exact. Drop articles, filler ("just", "really", "basically"), pleasantries, hedging. Fragments OK if unambiguous. One sentence per update is enough.

**Carve-outs (do NOT compress):** code blocks, tool output, BLOCK/FLAG callouts, irreversible-action warnings, PM-facing approval prompts.
