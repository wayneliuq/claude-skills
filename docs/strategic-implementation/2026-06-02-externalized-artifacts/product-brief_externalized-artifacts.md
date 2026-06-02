# Product Brief: Externalized Artifact Store — Specification

_Slug: externalized-artifacts · Date: 2026-06-02 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> The strategic-implementation skill now keeps its per-feature working documents — briefs, plans, validation logs, checkpoints, reports — in a server-authoritative external store instead of the repo. When you run the skill on any feature, its records land in that store and are surfaced to you locally, always-latest, without opening a web portal. A fresh clone of the main repo carries no per-feature artifact content — only a single small index file that points the skill at where the records live, so any strategic-implementation agent can find them while skill-less agents in other repos never parse the artifacts and never burn tokens on them. **This release delivers the specification only** — the record shape, the store-adapter contract, the in-repo discovery index, and the lifecycle mapping — proven implementable against three candidate stores, with no backend chosen and no skill rewired yet.

## 2. What the user does / sees

**Who is the user of this feature:** The maintainer of the strategic-implementation skill (you), operating the skill through Claude Code. The downstream beneficiary is any skill-less agent working in a *different* repo, who should never encounter these artifacts at all. The deliverable for this run is a **specification document**; the maintainer "uses" it by reading it and confirming it is complete and unambiguous enough to implement any one backend without further design decisions.

### D1 — A record model that says exactly what one artifact is, how it is named, and how a feature's records are listed
One artifact (a brief, a plan, a validation log, a checkpoint, a numbered simplify report, a token report, a post-execution report, a mockup) is one separately addressable record. The spec fixes the canonical address (`<repo-identifier>/<date-slug>/<artifact-name>`) and how all records under one feature are enumerated.
**How a user verifies:**
1. Open the spec and find a single section that names every per-feature artifact the skill produces today and assigns each a record address.
2. Confirm the address scheme is stable across worktree, device, and session (the same feature resolves to the same address from anywhere).
3. Confirm there is a defined way to list "all records for feature X" without knowing their names in advance.

### D2 — A store-adapter contract any backend can satisfy
The spec defines, independent of any backend, what a store must do: read returns the always-latest record; write persists a record; records are plain markdown for cheap round-trips. Conflict handling on concurrent writes is **best-effort** — surfaced when the backend supports it (a conflicting write reported, not silently lost), with a light skill-level guard acceptable where it doesn't, and plain last-write-wins tolerable for solo use. Optional behaviors a backend may or may not support (e.g. bulk import of existing artifacts) are declared as capability flags, so nothing optional becomes mandatory.
**How a user verifies:**
1. Find the contract section and confirm each required operation (read-latest, write, list) has defined inputs, outputs, and failure behavior.
2. Confirm the concurrency behavior is stated: conflicts are surfaced where the backend offers it, otherwise documented as best-effort / last-write-wins — never silently assumed safe.
3. Confirm optional capabilities are listed separately as flags, not mixed into the required operations.

### D3 — A lifecycle map showing which records are read and written at every stage of the skill
For each stage — session entry/start, clarify, brief draft, brief revise, mockup generate/revise, execution plan, deliverable execution, post-execution — the spec states which records that stage reads, which it writes, and when. It is explicit that the durable tier (project learnings, documentation registry) stays in the repo and is untouched.
**How a user verifies:**
1. Walk the spec stage-by-stage in the skill's real order and confirm every stage that produces or consumes an artifact today has a row saying what it reads/writes.
2. Confirm the two durable in-repo documents are explicitly marked "stays in repo, not moved."
3. Confirm the deliverable-execution stage explains how a per-deliverable commit no longer carries the artifact (the artifact lives outside the repo).

### D4 — A read-through cache contract for portal-free local browsing
The spec defines how the active feature's records are materialized locally so you can read them in your editor without a portal: hydrated at session start, always-latest, refreshed when the skill writes, disposable, and excluded from the repo. The local copy is never the source of truth.
**How a user verifies:**
1. Find the cache section and confirm it states when the cache is populated, that it has a single fixed local location, and that it is excluded from version control.
2. Confirm the spec is explicit that the cache can be deleted at any time with no data loss (the store is authoritative).
3. Confirm a new worktree or device gets the current records with no manual sync step.

### D5 — A conversational-feedback revision contract
Records are output-only: the skill writes them, you do not hand-edit them. Where the brief and mockup loops previously assumed you edited the file with inline comments, the spec replaces that with feedback given conversationally to the agent, which re-writes the record. The spec states this plainly for every loop that previously relied on file edits.
**How a user verifies:**
1. Find the revision contract and confirm it states the human never edits a record file as the feedback channel.
2. Confirm the brief-revision and mockup-revision flows are each restated to take feedback from chat and re-emit the record.
3. Confirm there is no remaining instruction anywhere in the lifecycle map that depends on a human editing an artifact in place.

### D6 — A confidentiality requirement and a proof the contract is backend-neutral
Because artifacts leave the repo for an external store, the spec states a backend-neutral requirement for handling anything sensitive they may contain. It then demonstrates the contract maps cleanly onto each of the three named candidate stores without changing the record shape — and records, per candidate, which optional capability flags it would set (including whether bulk migration of existing artifacts is trivial there).
**How a user verifies:**
1. Find the confidentiality requirement and confirm it is stated without depending on any one store's features.
2. Find a comparison showing each of the three candidate stores satisfying the required operations, with the record shape unchanged across all three.
3. Confirm migration of existing artifacts appears only as an optional per-backend capability flag — never as a required step.

### D7 — A single in-repo locator that points at where the records physically live
Exactly one file stays committed in the repo: a pure locator. It carries only what an agent needs to reach the store from a cold start — this repo's identifier and how to reach the store (the access surface the skill connects to, resolved when a backend is chosen). It does **not** hold the list of features; that catalog is fetched live from the store, so it is always current. It points; it never duplicates artifact content. The spec fixes the locator's schema and states the skill maintains it (output-only).
**How a user verifies:**
1. Open the spec and find that the locator has a single fixed, discoverable location and a defined schema, and confirm there is exactly one such file (not one per feature).
2. Confirm the only load-bearing content the spec requires is the repo identifier plus how to reach the store — and that the feature catalog is resolved live from the store, not stored in the file.
3. Confirm the spec says the locator is skill-maintained, so a stale or missing locator is recoverable from a known store and never authoritative over record content.

## 3. Success signal

The feature-level north star (PM-ratified) is: *a fresh clone of the main repo contains no per-feature artifact content — only the single discovery-index file — yet from any worktree/device the skill surfaces the active feature's records locally, always-latest.* This run delivers the specification that makes that outcome implementable, so its outside-observable signal is spec-level: **an implementer can take this spec and stand up any one of the three candidate stores with no further design decisions, and an independent read of the record shape finds zero backend-specific detail baked into it.** If either is not yet true, the spec is incomplete.

## 4. Boundaries

**In scope:**
- The specification: record model + addressing, store-adapter contract, the single in-repo discovery-index file's fixed location, schema, and maintenance rule, full lifecycle map, read-through cache contract, conversational-feedback revision contract, confidentiality requirement, and a three-backend neutrality proof.
- Defining optional capabilities (including bulk migration) as flags.

**Out of scope (this spec pass):**
- Writing any adapter code or rewiring any skill — the backend is now chosen (GitHub, a dedicated private repository), but implementing against it is the execution-plan's job, not this spec's.
- Actually migrating the existing per-feature artifacts.
- Changing the durable in-repo tier (project learnings, documentation registry).

**Anti-goals (philosophy-level — we deliberately will not):**
- Bake any single store's specifics into the record shape.
- Collapse a feature's artifacts into one composite document (one record per artifact is locked).
- Let a local copy ever become the source of truth.
- Require the maintainer to leave Claude Code or open a web portal for normal review.
- Treat human file-editing as a feedback channel.
- Let the in-repo index grow into a second copy of artifact content — it points, it does not duplicate.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Record granularity | One separately addressable record per artifact | `[HARD DECISION]` |
| Canonical address | `<repo-identifier>/<date-slug>/<artifact-name>`, stable across worktree/device/session | `[HARD DECISION]` |
| Durable tier | Project learnings + documentation registry stay in the repo, untouched | `[HARD DECISION]` |
| Source of truth | External store is authoritative; local copy is a disposable read-through cache | `[HARD DECISION]` |
| Human feedback channel | Conversational only; records are output-only, never hand-edited | `[HARD DECISION]` |
| Existing-artifact migration | Secondary, non-load-bearing; an optional per-backend capability, never a required step | `[HARD DECISION]` |
| Backend choice (execution target) | GitHub — a dedicated private repository — chosen as the implementation target for execution; the spec itself stays backend-neutral | `[HARD DECISION]` |
| Concurrent-write handling | Best-effort: surfaced where the backend supports it (the chosen store satisfies this), light skill-level guard otherwise; silent last-write-wins tolerable for solo use | `settled` (downgraded from hard) |
| Neutrality bar | Contract proven against the candidate stores with an unchanged record shape | `[HARD DECISION]` |
| In-repo footprint | Exactly one committed locator file holding only the repo identifier + how to reach the store; the feature catalog is fetched live from the store, not stored in-repo; skill-maintained, output-only | `[HARD DECISION]` |

## 6. Risks & unknowns

- **Concurrent writers.** D2 is now best-effort, not hard. The chosen execution target (a dedicated private GitHub repository) surfaces conflicting writes natively, so for the selected backend this is covered; the spec still documents the behavior rather than silently assuming safety. Owner: spec D2.
- **Over-abstraction.** Forcing one contract to fit three stores risks a lowest-common-denominator shape awkward for all. Owner: capability flags (D2/D6) absorb the differences.
- **Offline access.** A server-authoritative store means no records when offline; the spec should acknowledge this explicitly rather than imply local availability.
- **Confidentiality is genuinely hard to keep backend-neutral.** Stating a requirement that holds across very different stores (a private git repo vs a hosted notes service) is non-trivial. Owner: spec D6; may surface a residual open question.
- **Behavior change to existing loops.** Removing the inline-comment feedback path changes how brief/mockup revision works today; the downstream implementation phase must not regress those loops. Owner: deferred implementation, flagged here.
- **Locator drift across worktrees/branches.** Because the locator is committed in-repo, branches/worktrees can hold different versions. Largely defused by the locator-only design: it carries near-static config (repo identifier + how to reach the store), and the always-current feature catalog is fetched live from the store — so divergence is low-stakes and never authoritative over record content.
- **Self-reference.** This brief and its sibling artifacts are, for now, still written into the repo under the old scheme — the spec describes a future the skill does not yet follow. Owner: noted; not a defect this pass.

## 7. References & revision log

**Document references:**
- Architecture: `plugins/strategic-implementation/skills/*/SKILL.md` set + `docs/strategic-implementation/documentation-registry.md` (canonical; no standalone architecture doc)
- UX/PMF: n/a — captured in the clarify thread (no-portal, read-through cache)
- Security policy: none — confidentiality requirement stated inline in the spec (D6)
- Schema/ERD: n/a — the record shape is defined by this spec

**Revision log:**
- v0.1 · 2026-06-02 · initial draft
- v0.2 · 2026-06-02 · added D7 (single in-repo discovery-index file) per PM; added In-repo-footprint HARD decision; amended §1/§3/§4 to reflect the one remaining in-repo file; added index-drift risk
- v0.2.1 · 2026-06-02 · leakage self-revision: softened "location" wording in D4/D7/§4 to "a single fixed, discoverable location" (spec pins it; brief does not)
- v0.3 · 2026-06-02 · per PM, narrowed D7 to a pure locator (repo identifier + how to reach the store); feature catalog now fetched live from the store, not stored in-repo; updated §5 footprint decision and §6 drift risk accordingly
- v0.4 · 2026-06-02 · per PM, after a store-evaluation workflow: downgraded D2 conflict-safe-write from HARD to best-effort; recorded the chosen execution target (GitHub, a dedicated private repository — which satisfies the conflict-surfacing requirement); reversed the earlier "backend deferred" hard decision per explicit PM choice; spec remains backend-neutral
- v0.4.1 · 2026-06-02 · leakage self-revision: replaced "natively" with product-altitude wording in the §5 concurrent-write-handling row
