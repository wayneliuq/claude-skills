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
1. Read the brief end-to-end. Extract: deliverables (D1…Dn), each deliverable's **user-facing acceptance steps** (the outcome contract — what a human does to confirm it works), the success signal, scope boundary (in / out / anti-goals), hard decisions, document references, and the **§2 Maintainer view block** (reuse couplings + documentation obligation — the brief's second user, per `product-brief-drafter` rule 13). The brief deliberately does NOT specify an implementation method (`preview` / `cli` / `tdd` / `integration-test` / `post-hoc`); execution-plan chooses the method, driven by the user-acceptance steps and the integration-risk class. The Maintainer view is strategic-altitude; execution-plan turns it into operational requirements: reuse-vs-extract decisions (authoring rule 12) and concrete doc updates/creation (Step 4 below).
2. For each deliverable, identify the concrete files likely to change. **Prefer code-review-graph queries** (`semantic_search_nodes` to find the symbol, `query_graph` for callers/callees/imports/tests, `get_architecture_overview` for module shape, `get_impact_radius` for blast radius); fall back to **Glob** / **Grep** / **Read** only when the graph cannot answer. Verify file paths via Glob before citing them. Unverified paths get `[PATH NOT FOUND]` annotations. Cite graph results as concrete symbols (`function foo at path/file.py:42`, "callers: `bar`, `baz`") rather than paraphrased file content.
3. **Library-lifecycle doc pass.** For each integration-risk dependency from clarify, locate the canonical persistence / lifecycle doc (project README, vendor docs, RFC, or in-repo notes). Read the relevant section. Capture: what state persists across what boundaries (per-connection / per-session / per-process / per-deployment), known gotchas, and the doc URL/path. Time-box: aim for 15–30 minutes total across all libraries; if a library has no good docs, note that explicitly. Empty audit is acceptable only if clarify declared `none`.
4. **Load the documentation registry — and the brief's documentation obligation.** Read `docs/strategic-implementation/documentation-registry.md` if present. For each registry entry, judge whether the deliverables in this brief might invalidate it (touches the path, the area, or the update-trigger condition). Tag each deliverable with `may-invalidate: [doc-paths]` or `may-invalidate: none`. **Doc generation, not just invalidation:** the brief's Maintainer view obligation ("documented in keeping with the repo's documentation conventions") means a deliverable that introduces a *new* maintainer-facing surface — a new shared component, a new module boundary, a new config surface, a new convention — must also produce the corresponding doc **in the repo's existing documentation style** (survey how the repo documents comparable surfaces — registry entries, sibling docs, doc-comment conventions — and mirror it; do not impose a new format). Capture this on the deliverable's `Docs to update/create` field. Surface the union of impacted + newly-required docs in the plan summary at Step 5 so the PM sees what docs this work will require. Skip only when the brief's Maintainer view is `n/a — no maintainer-facing surface`.
5. Load `docs/strategic-implementation/project-learnings.md` if it exists. Filter entries for relevance to this brief's deliverables. Inject matching entries when invoking `review`.
6. **Load brief sidecar.** Read `<feature-folder>/brief-meta.yaml` if present. Capture `specialists_recommended:` — this list is forwarded to `review` to narrow specialist selection. Absent sidecar or empty list → forward an empty list; `review`'s pre-filter still applies mandatory triggers.

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
- **Docs to update/create:** <two parts. (1) `may-invalidate:` bracketed list of registry doc paths this deliverable might invalidate, or `none`. (2) `to-create:` any new doc this deliverable must author because it introduces a new maintainer-facing surface (new shared component / module boundary / config surface / convention) — name the doc path and the repo style it mirrors, or `none`. Both surface here so executing-plans bundles doc work into the deliverable's atomic commit. `n/a` only when the brief's Maintainer view is `n/a — no maintainer-facing surface`.>
- **Visual contract:** <mockup file path if a UI mockup was approved upstream, else `n/a`. Implementation must match this mockup; post-execution prompts a manual visual diff.>
- **Consumer audit:** <required iff this deliverable changes a data shape — interface / type / schema / payload / return type / function signature. Otherwise: "n/a — no shape change.">
  - <consumer file:symbol> — `updated-in-this-deliverable` | `updated-in-D<n>` | `unaffected-because-<reason>` | `explicit-skip-because-<reason>`
  - ...
- **Convergence audit:** <required iff this deliverable introduces a behavioral UI element (dialog / picker / menu / modal), a rendering/parsing pipeline, or a write to shared state / a source of truth. Otherwise: "n/a — no new capability." One entry per capability:>
  - <capability> — existing impl: `<symbol at path:line>` (found via graph semantic search by *purpose*, not name — inline re-implementations have no symbol to grep) | `none found — greenfield (searched: <query>)`
  - decision: `reuse` | `extract-shared-primitive-and-converge-both-callsites` | `second-path-routed-through <canonical fn/component>` | `re-implement (justified: <why the existing one genuinely doesn't fit>)` | `create-shared-primitive (consumers: <≥2 current call sites listed | named near-term consumer: D<n> or brief-ref>)` | `scaffold-abstraction-layer (architectural; grounded-in: <architecture-doc ref>; anticipated-consumers: <named surfaces>)`
  - <A second create / write / render path to an existing capability is a design smell — it must be `routed-through` the canonical chokepoint or carry a `re-implement (justified)`. `greenfield` is valid only after a recorded search. The two `create-*` decisions are governed by authoring rule 12 — a leaf shared primitive needs current/named consumers; only a higher-scope abstraction layer may be scaffolded on anticipated reuse, and only when grounded in the architecture doc.>
- **Source-of-truth touchpoints:** <for each shared state / store slice / derived state / persisted record / URL↔view-state this deliverable reads or writes — name it and list the OTHER repo paths that also read/write it (graph: writers/readers). If >1 writer OR >1 reader, declare the invariant and how validation exercises all paths. Otherwise: "n/a — single reader/writer.">
  - <source-of-truth name> — writers: `<paths>`; readers: `<paths>`
  - invariant: <e.g. "exactly one status representable"; "every create path yields its companion"; "URL and in-memory view-state agree"> — validation exercises all paths via: <how>

### D2 — <name>
...

## Parallel groups & order
<textual DAG — which groups run in parallel, which are sequential>

### Sequencing rationale
<the order the groups run, justified against authoring rule 13's rubric: unblocking fixes/refactors → audit+reuse shared → create shared / scaffold abstraction → per-domain (logical surface order) → e2e-validating deliverable last. One line per stage naming which D-ids land there and why. Stages are barriers, not anti-parallel — note which D-ids inside a stage run concurrently. For any stage-3 shared surface, say whether it is a standalone prior deliverable or a macro-deliverable seam (rule 12 placement); this must agree with the Workflow decision below. State explicitly which deliverable's validation proves the brief's success signal e2e.>

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

0. **Does this need to exist?** Before drafting any deliverable, abstraction, module, config surface, or dependency, walk this hierarchy and stop at the first hit:
   1. **Need it at all?** → if the brief's success signal and every acceptance step still hold without it, drop it (YAGNI).
   2. **Stdlib / language built-in does it?** → use that.
   3. **Native platform / framework feature does it?** → use that.
   4. **Already-installed dependency does it?** → use that (this is rule 6's reuse check).
   5. **One line?** → write the one line.
   6. **Only then** → the minimum that satisfies the acceptance steps.

   Never add scaffolding, plugin points, strategy patterns, or generalization for hypothetical future needs. The `plan-simplify` reviewer scores the plan against this same hierarchy and returns deletion candidates for anything that fails it.

1. **One deliverable = one user-observable outcome.** Do not create deliverables for "internal plumbing" unless the plumbing is itself a validation gate.
2. **No LOC budgets.** Size is not a gate. Fitness is a gate.
3. **Validation method honesty.** Choose the method whose evidence actually proves the deliverable's user-acceptance steps. If the steps require visual confirmation, `preview` or `post-hoc` — not `tdd`. If the steps name observable behavior under real I/O, `integration-test` — not `tdd` with a mocked seam. If the chosen method cannot reproduce the user's verification flow, it is wrong. **For a `Macro-deliverable: true` deliverable, the method must prove the INTEGRATED cross-domain outcome end-to-end — never a single domain in isolation.**
4. **Preview-unavailable fallback.** For `preview`-validated deliverables: in `supervised`/`auto`, pause for PM manual validation if the preview tool can't run; in `yolo`, auto-escalate to TDD and proceed.
5. **Verify paths.** Every file path must be confirmed via Glob before the draft is presented for review.
6. **Reuse before creating** (rule 0, rung 4). Grep for existing primitives before introducing a new one; cite every reused primitive in "Reused existing patterns."
7. **Validation honesty per integration-risk class.** Class `a`/`b`/`c` deliverables MUST declare validation as `integration-test`, `preview`, or `post-hoc`. They MUST NOT declare `tdd` if the proposed test would mock the very dependency the deliverable's correctness depends on. Class `d` may use any method. A green unit-test suite that mocks the integration point is not validation — it is orthogonal-to-correctness coverage. A `Macro-deliverable` is treated as integration-risk for this rule: its method must exercise the cross-domain seam, not per-domain mocks.

   | Rationalization | Rebuttal |
   |---|---|
   | "Unit tests are faster / simpler here." | If they mock the dependency the deliverable's correctness rests on, they're orthogonal-to-correctness coverage, not validation. Speed is irrelevant when the test can't fail for the real reason. |
   | "The integration point is stable, mocking is fine." | Stability is a claim, not evidence. Class a/b/c means the risk lives at that seam — exercise it (`integration-test`/`preview`/`post-hoc`), don't assume it away. |
8. **Consumer audit on shape change.** Any deliverable that changes a data shape (interface / type / schema / payload / return type / function signature) MUST grep its consumers and list every one with a status (`updated-in-this-deliverable`, `updated-in-D<n>`, `unaffected-because-<reason>`, `explicit-skip-because-<reason>`). Hand-wavy enumeration is rejected by review.

   | Rationalization | Rebuttal |
   |---|---|
   | "Probably nothing else uses this shape." | "Probably" is a grep you haven't run. Run it, then list every consumer with a status. |
   | "It's a small/internal change, consumers will adapt." | Silent shape changes break callers at runtime, not review time. Enumerate them now or review rejects the plan. |
9. **Macro-deliverable (narrow exception).** Default is normal decomposition — split work into the smallest independently-validateable deliverables. A deliverable may be marked `Macro-deliverable: true` ONLY when ALL hold: (a) the outcome spans ≥2 domains (commonly backend / API-contract / frontend); (b) the domains are NOT independently end-to-end-validateable — splitting them loses the ability to validate any sub-part e2e; (c) together they form ONE user-observable outcome; (d) it is large enough that concurrent build meaningfully beats sequential. PLUS an eligibility gate: the domains must own **disjoint file sets — authored AND generated/derived outputs** (no two domains write the same lockfile / index / generated artifact). Expected domain count is small (≤ ~4). If work *can* be split into independently-validateable pieces, it MUST be — a macro-deliverable is not a license to skip honest decomposition. A macro-deliverable IS one deliverable → one atomic `D<n>:` commit (executing-plans runs its domains in one Workflow). Record it in the template's `Macro-deliverable` / `Domains & file partition` fields and name it under "Workflow decision".

   **Shared surface inside a macro-deliverable (reconciles rule 12 with the seam).** If the cross-domain outcome needs a shared surface (a rule-12 `create-shared-primitive` / `scaffold-abstraction-layer`), that surface is the macro-deliverable's **seam/contract** — built first in the Workflow barrier, then the domains fan out against it (executing-plans Step 2-macro). It is NOT one of the concurrent domains: its consumers depend on it, so making it a parallel domain would break both the independent-buildability premise (b) and the disjoint-write gate. A shared surface consumed *beyond* this one outcome (≥2 separate deliverables, or a named future consumer) is instead a **standalone prior deliverable** (rule 13 stage 3) that this macro-deliverable lists under `Deps`.

10. **Convergence before re-implementation** (rule 0, rung 4, applied to capabilities — not just named symbols). Before a deliverable builds a behavioral UI element, a rendering/parsing pipeline, or a write to shared state, search the repo for an existing implementation of that *capability/purpose* (semantic search, not name-grep — the worst re-implementations are inline and have no symbol to grep). The plan-time and review-time question is the same: **"Does an implementation of this capability already exist, and does this deliverable route through it rather than re-implement the step?"** If one exists, the deliverable must `reuse` it, `extract-shared-primitive-and-converge` both call sites, or `second-path-routed-through` the canonical component — never re-implement the step inline. Record the search and the decision in the `Convergence audit` field. A second create / write / render path to an existing capability is a design smell, not a shortcut — the bug lives at the divergence seam.

    | Rationalization | Rebuttal |
    |---|---|
    | "Hand-rolling it here is simpler than wiring up the existing component." | The existing component carries behavior you'll silently drop (Esc/close, cascade enumeration, frontmatter strip). Convergence ≠ brevity — route through it or justify the re-implement. |
    | "It's a slightly different case, so a second path is cleaner." | A second path diverges the moment either side changes. Extract a shared primitive and converge both call sites, or route the variant through the canonical one. |

11. **Single chokepoint for writes to a source of truth.** Any deliverable that writes to shared state / a store / a persisted source of truth MUST route the write through the existing canonical mutation/lifecycle function, named in the `Convergence audit`. A write that mutates *around* it — an inline optimistic update, a second create path, an error path that sets state directly — is rejected: it bypasses whatever the canonical lifecycle does (optimistic state, error rollback, companion creation). When a source of truth has >1 writer or >1 reader, the `Source-of-truth touchpoints` field must declare the invariant and how validation exercises every path — **and prefer designing the multiplicity out** (one mutation fn, one derived enum so only one status is representable, one tight type so the bad value is unrepresentable) over testing all N paths. Collapsing N→1 is cheaper than proving N paths agree.

    | Rationalization | Rebuttal |
    |---|---|
    | "It's just one extra `setState` next to the store call." | Then it's one path the canonical lifecycle won't run — optimistic/error/companion logic silently skipped. Route it through the canonical fn. |

12. **Shared-component creation bar (the maintainer is the second user).** The brief's Maintainer view obligates reuse over parallel surfaces. When no existing implementation fits (convergence rung exhausted) and you must create something shared, the bar depends on scope:
    - **Leaf shared component / primitive** (a reusable widget, helper, hook, util) — justified ONLY by **≥2 current call sites** (list them) OR **a named near-term consumer** (a specific deliverable in this plan, or a referenced approved/in-flight brief). Speculative "we might reuse this later" with no named consumer is rejected — `plan-simplify` scores it against rule 0 (YAGNI) and returns it as a deletion candidate. Record as `create-shared-primitive` in the Convergence audit.
    - **Higher-scope abstraction layer** (an architectural boundary / seam others will build *on top of* — not a leaf reused *by* a few call sites) — MAY be scaffolded on **anticipated** reuse without a named current consumer, but ONLY when the anticipation is **grounded in the architecture document** (the arch doc or roadmap names the boundary, or the brief's scope plainly implies a broader surface). Cite the grounding. Ungrounded "future-proofing" abstraction layers are still rejected. Record as `scaffold-abstraction-layer (grounded-in: <ref>)` in the Convergence audit.
    - Document each created shared surface under `Docs to update/create` `to-create:` — a new shared surface is a new maintainer-facing surface and must be documented in the repo's style.
    - **Placement in the build (reconciles with the macro seam).** A created shared surface is build-first work (rule 13 stage 3) and lands one of two ways, never a third: (a) **standalone prior deliverable** — when consumed beyond one cross-domain outcome (≥2 separate deliverables or a named future consumer); sequenced before its consumers, its own atomic commit. (b) **macro-deliverable seam** — when it serves only the domains of ONE macro-deliverable; built first in that deliverable's Workflow barrier, folded into the one macro commit, no separate deliverable. A shared surface is **never** one of a macro-deliverable's concurrent domains — its consumers depend on it (rule 9).

    | Rationalization | Rebuttal |
    |---|---|
    | "Extract it now, we'll reuse it on the next feature." | Name the next feature's deliverable or brief. If you can't, that's speculation — build it inline at the one call site; extract when the second arrives. |
    | "This abstraction layer makes everything cleaner going forward." | Cleaner for whom, anticipated by what? A leaf abstraction needs 2 current call sites. An architectural layer needs the arch doc to name the boundary. Neither is satisfied by "going forward." |

13. **Sequence by unblock-then-domain, not by deliverable number.** The DAG (deps) constrains order; within what deps allow, order by this rubric so the build leaves the repo coherent at each step and ends on an e2e proof:
    1. **Unblocking fixes / refactors first** — anything that has to be true before clean work can begin (a broken seam, a refactor that other deliverables depend on, a dependency bump).
    2. **Audit + reuse shared components** — the convergence-audit `reuse` / `route-through` deliverables, so later work builds on the canonical surfaces rather than racing them.
    3. **Create shared components / scaffold abstraction layers** — the `create-shared-primitive` / `scaffold-abstraction-layer` deliverables (rule 12), so the surfaces they introduce exist before per-domain work consumes them.
    4. **Per-domain work in a logical surface order** — group by domain/surface (data → API contract → frontend is the common spine; follow the repo's actual layering), each group internally ordered so a reviewer can follow one surface at a time.
    5. **End on the deliverable(s) that validate the brief's success signal end-to-end** — the last group should be the one whose validation demonstrates the whole feature against the brief, not an internal sub-part.

    These stages are a **partial order (barriers), not a ban on concurrency.** Deliverables with no interdependency run in parallel *within* a stage, and a macro-deliverable runs its domains concurrently behind its own seam-first barrier — the macro's seam *is* stage 3 realized inside one deliverable (rule 9). The `Sequencing rationale` and the "Parallel groups & order" DAG must describe **one** order, not two: the rubric sets the stage barriers; the parallel groups are the deliverables a stage leaves free to run together. The only hard barrier the rubric adds beyond raw deps is **stage 3 before stage 4** — a created shared surface must land (as a prior deliverable or as a macro seam) before the per-domain work that consumes it.

    This is ordering, not new deliverables — it never adds scope. Record the resulting order and its rationale in the "Parallel groups & order" section's `Sequencing rationale`. `alignment` checks the plan honors this rubric.

---

## Step 4 — Invoke review

Still inside plan mode, invoke `strategic-implementation:review` with:
- The full plan text
- The brief path
- The document reference locations from the brief
- The filtered project-learnings block (if any)
- `specialists_recommended:` from `brief-meta.yaml` (may be empty list)
- Autonomy level

The `review` skill runs tiered: `alignment` + `plan-simplify` first, then specialists on flags. It returns a consolidated JSON patch list and status.

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

---

## Record routing — externalized artifact store

Per-feature **records** (brief / plan / validation-log / checkpoint / reports / mockup / brief-meta) route through the store adapter, not the feature folder directly: wherever a step says write/read `<feature-folder>/<file>`, use the store address `<repo-id>/<date-slug>/<file>` with in-repo fallback. Full read/write/fallback protocol: [`scripts/store/README.md`](../../scripts/store/README.md#record-routing-protocol-agent-facing). **Durable tier — `project-learnings.md`, `documentation-registry.md` — stays in-repo, never routed to the store.**
