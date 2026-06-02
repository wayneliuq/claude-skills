# Execution Plan: Externalized Artifact Store — Specification
_Implements: product-brief_externalized-artifacts.md · Date: 2026-06-02_

## Context

The strategic-implementation skill writes ~5–9 markdown artifacts per feature into `docs/strategic-implementation/<date>-<slug>/` (73 files across 16 features today). They clutter the repo, are committed so every clone inherits them, and burn tokens for skill-less agents in other repos that try to parse them. This plan produces a **single backend-neutral specification document** (`spec.md`) that defines how those transient per-feature artifacts move to a server-authoritative external store, plus a proof the contract is implementable. The store is **one shared store serving every repo the skill runs in**, segregated by a `<repo-id>` namespace — so each consuming repo keeps only a tiny committed locator and zero artifact content, and skill-less agents in any of those repos parse nothing. **No adapter code, no skill rewiring, no migration this pass** — those are a later implementation pass the spec enables; migration of existing artifacts is forward-only/optional (existing files stay put; only new features externalize). Chosen execution target for the later pass: a single dedicated private GitHub repository. Durable tier (`project-learnings.md`, `documentation-registry.md`) stays in-repo, untouched.

The artifact is one document built incrementally; deliverables map to coherent, independently-checkable section-groups of it (consolidated from the brief's seven into four).

## Library lifecycle audit

These are the integration-risk dependencies from clarify. The spec's adapter contract must *accommodate* their semantics behind the abstraction without leaking specifics into the backend-neutral record shape. This pass writes only a document, so nothing executes against them here — the audit informs spec content.

### GitHub (chosen execution-target store: Contents-style file API + `gh` CLI)
- **State that persists:** each record is a file on a branch; every write is a commit, giving free version history. A write must present the record's current version handle (blob SHA); a stale handle is rejected (409) rather than silently overwritten — this is the optimistic-concurrency surface the spec's best-effort conflict clause maps onto.
- **Quirks / gotchas:** default content reads return base64-wrapped JSON (raw-markdown requires a specific Accept header); authenticated REST is rate-limited (~5k req/h, non-binding for solo doc volume); the official MCP repos-toolset loads ~10k tokens of schema, while the `gh` CLI is a zero-schema fallback. None of these may appear in the record shape; all live behind the adapter contract.
- **Doc consulted:** store-evaluation workflow findings (run `wf_b78710fd-d9e`, captured in this session); GitHub REST Contents docs (per workflow agent citations).

### Local filesystem (read-through scratch cache)
- **State that persists:** a per-session local materialization of the active feature's records. Must be disposable, gitignored, and never the source of truth — directly mirroring the existing `.memory/` derived-index discipline ([.gitignore:7-9], [MEMORY-DOCTYPES.md:29]).
- **Quirks / gotchas:** worktrees share no working state, so the cache must key off the stable artifact address, not a path inside one checkout; a deleted cache must be transparently re-hydratable from the store.
- **Doc consulted:** [.gitignore], [plugins/strategic-implementation/scripts/memory/MEMORY-DOCTYPES.md], [hooks/hooks.json:4-11] (SessionStart refresh precedent).

### `gh` CLI auth state
- **State that persists:** token availability across interactive vs non-interactive/cron agents. Relevant to the spec's confidentiality (D6) and reachability/locator (D7) sections — the locator names *how to reach the store*, and the spec must state the auth expectation without pinning a token mechanism.
- **Quirks / gotchas:** headless/cron contexts may lack interactive auth; spec states the requirement, defers the mechanism to implementation.
- **Doc consulted:** clarify integration-risk list; store-evaluation findings.

## Deliverables (DAG)

All deliverables write to one new file: `docs/strategic-implementation/2026-06-02-externalized-artifacts/spec.md`, following the established spec format ([2026-04-20-v2-redesign/spec.md] — numbered sections, `[HARD DECISION]` rows locked, revision log). Integration-risk class **d** for every deliverable (a document; nothing third-party executes). Validation method **post-hoc** throughout, because the deliverable is a document whose acceptance is "an independent read confirms the brief's per-deliverable verify-steps" — no preview/test can demonstrate a spec better than an adversarial read can. Consumer audit **n/a** (no code data-shape changes this pass). Visual contract **n/a** (no UI).

### DP1 — Core record model + backend-neutral adapter contract
- **Integration-risk class:** d
- **Implements brief:** D1 (record model + addressing + listing), D2 (adapter contract).
- **User-acceptance steps (from brief):**
  1. (D1) Find a section naming every per-feature artifact and assigning each a record address; confirm the address scheme `<repo-id>/<date-slug>/<artifact-name>` is stable across worktree/device/session and there's a defined way to list all records for a feature.
  2. (D2) Confirm each required operation (read-latest, write, list) has defined inputs/outputs/failure behavior; confirm the concurrency behavior is stated (surfaced where supported, else best-effort/last-write-wins — never silently assumed safe); confirm optional capabilities are separate capability flags.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** post-hoc — spawn an independent "spec-completeness" reviewer agent given ONLY this section; it must (a) restate the record address for three different artifacts unambiguously AND confirm the address scheme is stable across worktree/device/session (state why the same feature resolves identically from different checkouts); (b) list the three required operations (read-latest / write / list) with inputs, outputs, and failure behavior, and confirm `write` carries an optional opaque version-handle; (c) confirm the raw-markdown round-trip is stated as a contract obligation; (d) confirm optional-capability flags are listed separately from required ops. (Backend-leakage audit is NOT run here — it lives once, authoritatively, on the whole document in DP4, per simplify's de-dup.)
- **Files:** `docs/strategic-implementation/2026-06-02-externalized-artifacts/spec.md` (create), `docs/strategic-implementation/documentation-registry.md` (add one row for the new spec).
- **Steps:**
  1. Create `spec.md` with the standard header + §Context/§North-Star/§Users/§Locked-Decisions skeleton (carry the brief's HARD decisions verbatim).
  2. Write **§Record model**: enumerate the externalized artifact set (ground it in the lifecycle map — product-brief, execution-plan, validation-log, checkpoint, simplify-report-NN, token-report, post-execution-report, brief-meta.yaml, mockup.html, spec.md, research/spec extras); define one-record-per-artifact, the canonical address, address stability across checkout/device/session, and live per-feature listing. State the **store topology: ONE shared store holds the artifacts of every repo the skill runs in, segregated by the `<repo-id>` segment of the address** — the `repo-id` namespace is what makes the same shared store serve many repos without collision.
  3. Write **§Adapter contract**: read-latest / write / list as abstract operations with inputs, outputs, failure modes; raw-markdown round-trip requirement; the best-effort conflict clause expressed via an **optional opaque version-handle** returned by read-latest and accepted by write — backends that support optimistic concurrency reject a stale handle (GitHub maps it to blob-SHA → 409), last-write-wins backends ignore it; pair it with a `conflict-surfacing: yes|no` capability flag. The handle stays opaque so no backend token (blob-SHA etc.) leaks into the record shape. Optional-capability flags (incl. bulk-migration) declared separately from required ops.
  4. Add a `documentation-registry.md` row for `spec.md` (Covers / Last Updated 2026-06-02 / Update Trigger / Owning Area).
- **Deps:** none
- **Pre-flight env check:** brief + Explore lifecycle map available (both in-session). No runtime env.
- **may-invalidate:** none (skills unchanged this pass; this ADDS a registry row, invalidates no existing doc).

### DP2 — Lifecycle map + read-through cache + conversational-feedback revision contract
- **Integration-risk class:** d
- **Implements brief:** D3 (per-stage read/write map), D4 (read-through cache), D5 (conversational-feedback revision). Grouped because all three describe how the live skill flow interacts with the store/cache.
- **User-acceptance steps (from brief):**
  1. (D3) Walk the spec stage-by-stage in real skill order; every stage that produces/consumes an artifact has a row saying what it reads/writes; the two durable in-repo docs are marked "stays in repo"; the execution stage explains how a per-deliverable commit no longer carries the artifact.
  2. (D4) Cache section states when it's populated, that it has a single fixed local location, that it's excluded from version control, that it's deletable with no data loss, and that a new worktree/device gets current records with no manual sync.
  3. (D5) States the human never edits a record file as feedback; brief- and mockup-revision flows are restated to take feedback from chat and re-emit the record; no remaining lifecycle instruction depends on a human editing an artifact in place.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** post-hoc — spec-completeness reviewer must: (a) cross-check the lifecycle table against the Explore-derived ground-truth map (every R/W touch-point present); (b) confirm the two durable in-repo docs (project-learnings, documentation-registry) are explicitly marked stays-in-repo / not-moved; (c) confirm the deliverable-execution entry explains how the per-deliverable atomic commit stops carrying the artifact body; (d) confirm the cache discipline matches the `.memory/` precedent AND the read-resolution model + staleness bound are stated; (e) for the revision contract, confirm the brief-revision and mockup-revision flows are each POSITIVELY restated as chat-based / record-re-emitted (not merely that the old marker is absent), and grep for any surviving `<!-- pm: -->` dependency; (f) confirm the session-entry bootstrap is defined (first use in a repo creates the `<repo-id>` namespace + writes the locator; later sessions read it). Known current touch-points to neutralize: product-brief-drafter inline-comment loop ([product-brief-drafter/SKILL.md:9,75,193-206]), ui-mockup inline + `mockup-feedback.md` ([ui-mockup/SKILL.md:5,98,101,113-114]).
- **Files:** `spec.md` (append §Lifecycle, §Read-through cache, §Revision contract).
- **Steps:**
  1. Write **§Lifecycle map**: a table mirroring the Explore map — each stage (session-entry, clarify, product-brief-drafter draft/revise, ui-mockup, execution-plan, review, executing-plans, post-execution, simplify) → records read/written; explicitly mark durable tier (project-learnings, documentation-registry) as stays-in-repo / not-moved; describe how executing-plans' atomic per-deliverable commit stops carrying the artifact body (locator/registry only, body lives in the store). The **session-entry** row must define **bootstrap**: on first use in a repo (no locator present), the skill ensures this repo's `<repo-id>` namespace exists in the shared store and writes the locator; on subsequent sessions it reads the locator and hydrates the active feature's records into the cache.
  2. Write **§Read-through cache**: single fixed local location, populated at session start for the active feature, refreshed on write, gitignored, disposable, re-hydratable, deletable-with-no-data-loss — explicitly reusing the `.memory/` derived-cache discipline; note worktree-independence (keys off the address, not a checkout path). State the **read-resolution model** that makes "always-latest" true (read-through-on-access vs session-start snapshot, and the staleness window if any) and **bound hydration scope to the active feature only** (not the whole store), so per-session cost is bounded.
  3. Write **§Revision contract**: records are output-only; brief and mockup revision loops take feedback conversationally and re-emit the record; the `<!-- pm: -->` and `mockup-feedback.md` file-edit channels are retired for relocated artifacts. **Resolve `<!-- pm-disposition: -->` in simplify-report**: either include it in the retired file-edit channels or explicitly scope it out with a one-line reason (the post-hoc grep asserts the chosen disposition).
- **Deps:** DP1 (references the record model + addressing).
- **Pre-flight env check:** Explore lifecycle map available.
- **may-invalidate:** none this pass (documents intended future changes to those SKILL.md files; does not make them).

### DP3 — Confidentiality requirement + single in-repo locator
- **Integration-risk class:** d
- **Implements brief:** D6 (confidentiality requirement only), D7 (single in-repo locator).
- **User-acceptance steps (from brief):**
  1. (D6-confidentiality) Find a confidentiality requirement stated without depending on any one store's features.
  2. (D7) The locator has a single fixed, discoverable location and a defined schema; exactly one such file (not one per feature); the only load-bearing content is repo-id + how to reach the store; the feature catalog is resolved live from the store, not stored in the file; the locator is skill-maintained and a stale/missing locator is recoverable from a known store, never authoritative over content.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** post-hoc — spec-completeness reviewer confirms: (a) the confidentiality requirement is backend-neutral (holds for a private git repo AND a hosted notes service); (b) the credential is stated as supplied out-of-band, never stored in the repo or any record; (c) the locator schema contains *only* repo-id + reach-the-store coordinates (no catalog, no per-feature data, **no credential/secret**), with recovery semantics stated; (d) the locator explicitly forbids embedding a secret.
- **Files:** `spec.md` (append §Confidentiality, §Locator).
- **Steps:**
  1. Write **§Confidentiality**: backend-neutral requirement for handling anything sensitive that leaves the repo (private-by-default storage + an auth expectation), explicitly not tied to one store's mechanism. State the **credential is supplied out-of-band from the agent/host environment, never committed to the repo or stored in any record**. State secret-at-rest neutrally: artifact-content confidentiality is the store's responsibility (access-controlled, private-by-default); credential confidentiality is the host's — so neither lands in-repo.
  2. Write **§Locator**: one committed file per repo, fixed discoverable location, schema = this repo's `repo-id` (its namespace in the shared store) + how-to-reach-the-shared-store **coordinates** (for a git store: owner/repo + the branch/ref records live on — phrased neutrally as "store-target coordinates," concrete form filled by §Chosen execution target); live catalog from the store; skill-maintained, output-only (written at bootstrap); recoverable. **Invariant: the locator is committed, therefore it MUST NOT embed any credential/secret/token — a token in the locator is a defect.** Distinguish it from the in-repo `documentation-registry.md` (different purpose, stays separate).
- **Deps:** DP1 (locator references the addressing scheme).
- **Pre-flight env check:** none.
- **may-invalidate:** none.

### DP4 — Backend-neutrality proof + capability flags + chosen-target record
- **Integration-risk class:** d
- **Implements brief:** D6 (neutrality proof) + the brief's success signal (spec is implementable with no further decisions; zero backend-specifics in the record shape).
- **User-acceptance steps (from brief):**
  1. (D6) A comparison showing the candidate stores each satisfying the required operations with the record shape unchanged across all; migration appears only as an optional per-backend capability flag, never required.
  2. (Success signal) An implementer can take the spec and stand up the GitHub target with no further design decisions; an independent read of the record shape finds zero backend-specific detail baked in.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** post-hoc — spawn a fresh independent agent given ONLY the finished `spec.md` (genuine isolation: NOT the agent that authored it). It must (a) enumerate the concrete steps to implement the GitHub adapter and report ANY decision the spec leaves undefined (incl. which branch/ref, repo-id→owner/repo resolution, auth source); (b) audit §Record model + §Adapter contract for backend-specific leakage; (c) confirm all THREE named candidate stores map as full rows with the record shape unchanged; (d) confirm bulk-migration appears ONLY as a per-backend optional capability flag, never as a required step. PASS requires "no undefined decisions" + "no leakage." This is the authoritative whole-document leakage audit (DP1 no longer duplicates it) and directly tests the brief's success signal.
- **Files:** `spec.md` (append §Backend-neutrality proof, §Capability flags, §Chosen execution target, §Risks, §Revision log).
- **Steps:**
  1. Write **§Backend-neutrality proof**: name exactly **three candidate stores spanning structural diversity — GitHub (git file store), Cloudflare KV (key-value store), HackMD (hosted notes service)** — and give each a full row in a table mapping the adapter contract operations (read-latest / write+version-handle / list) onto it, with the record shape held constant across all three; note per-store capability flags (conflict-surfacing: GitHub yes / KV,HackMD no→best-effort; bulk-migration). The notes-service row (HackMD) plus the git-repo row (GitHub) jointly stress the backend-neutral confidentiality requirement (D6).
  2. Write **§Chosen execution target**: a SINGLE GitHub dedicated private repo (e.g. a `strategic-artifacts` repo) serving as the one shared store for all repos, each under its `<repo-id>/` path; with the flags it sets (conflict-surfacing: yes; bulk-migration: trivial, but migration is **forward-only / optional** per PM decision — existing artifacts are not migrated, only new features externalize). Record the **access-surface decision as a documented swappable capability** — official MCP repos-toolset (~10k-token schema, richer ops) vs. zero-schema `gh` CLI (cheaper) — state the default so the later pass inherits the dependency-cost decision rather than rediscovering it. Add one neutral line reconciling "always-latest read": the contract returns the latest committed record, and defeating any backend read-cache / propagation delay is the adapter's responsibility (does not re-harden D2 writes). **Reference** the auth/headless expectation from §Confidentiality rather than restating it (one source of truth). Keep all of this out of the backend-neutral record shape — it is execution-target detail.
  3. Write **§Risks** (incl. a named **offline-access** entry — server-authoritative ⇒ no records when offline; spec acknowledges rather than implying local availability — plus over-abstraction and leakage) and **§Revision log**; ensure the locked-decisions section reflects the final brief (best-effort D2).
- **Deps:** DP1 (contract), DP3 (locator/confidentiality feed the per-store comparison).
- **Pre-flight env check:** store-evaluation findings available (in-session).
- **may-invalidate:** none.

## Parallel groups & order

- **DP1** first (defines the record model + contract everything else references).
- **DP2** and **DP3** are order-independent (both depend only on DP1, touch disjoint sections). No real parallelism — all four edit one file, so authoring is sequential; the DAG only constrains dependency, not concurrency.
- **DP4** last (depends on DP1 + DP3; consumes the whole document — and runs the single authoritative backend-leakage audit, which DP1 no longer duplicates).
- Practical order: DP1 → DP2 → DP3 → DP4.

### Workflow decision
none — all deliverables are decomposable and authored sequentially into one document. No macro-deliverable (no cross-domain disjoint-file-set work; it's one markdown file).

## Reused existing patterns

- **`.memory/` derived-cache discipline** ([.gitignore:7-9], [scripts/memory/MEMORY-DOCTYPES.md:29], [hooks/hooks.json:4-11]) — the read-through cache (D4) reuses the same "derived, rebuildable, gitignored, never source of truth, refreshed at session start" model rather than inventing a new caching concept.
- **`spec.md` document format** ([docs/strategic-implementation/2026-04-20-v2-redesign/spec.md]) — numbered sections, `[HARD DECISION]` rows, revision log; the new spec follows it.
- **`documentation-registry.md` schema** ([docs/strategic-implementation/documentation-registry.md] header `Path | Covers | Last Updated | Update Trigger | Owning Area`) — DP1 registers the new spec using the existing row schema and update protocol.
- **`MEMORY-DOCTYPES.md` record classification** — informs which artifacts are "records" to externalize vs. excluded, so the spec's record set matches what the workflow already treats as durable-vs-derived.

## Risks & contingencies

- **Spec drifts from real skill behavior.** The lifecycle map (DP2) is only as correct as the Explore map; contingency — DP2's post-hoc check cross-references the map against the cited SKILL.md file:line touch-points, not memory.
- **Over-abstraction.** Forcing the contract to fit several stores risks a lowest-common-denominator shape; contingency — capability flags (DP1/DP4) absorb differences; the neutrality proof must hold the record shape constant, which is the guard.
- **Leakage of GitHub specifics into the neutral shape.** Contingency — DP4's independent-agent audit explicitly hunts for backend leakage in §Record model / §Adapter contract.
- **Self-reference.** The spec itself is written in-repo under the old scheme; that's expected and noted in the brief §6 — not a defect this pass.

## Out of scope for this plan

- Writing any adapter/client code, the locator file, or the cache mechanism.
- Rewiring any SKILL.md to read/write the external store, or retiring the `<!-- pm: -->` loops in code.
- Actually creating the GitHub repo or migrating the existing 73 artifacts.
- Any change to `project-learnings.md` or `documentation-registry.md` beyond adding one row for the new spec.

## Verification (end-to-end)

1. Open `spec.md`; walk each brief deliverable's "How a user verifies" steps (D1–D7) and confirm the corresponding section answers every step.
2. Run the DP4 independent-agent check: hand a fresh agent only `spec.md` and confirm it reports (a) no undefined decisions for a GitHub implementation and (b) no backend leakage in the record shape — this is the brief's success signal.
3. Confirm `documentation-registry.md` has exactly one new row for the spec and no existing row's content changed.
4. Confirm no source/skill file changed (git diff shows only the two docs).

## Review outcome (tiered review, 2026-06-02)

Ran: alignment, simplify, user-validation (generalists); boundaries, runtime-risk, technical-expert, tests (specialists). Status: **FLAG**, no BLOCK. Plan-gate kept all specialist patches (all in-scope spec-content completeness; none reopened a locked decision). Patches applied above:
- **High:** version-handle on the write contract (opaque/optional → best-effort conflict surfacing, no leakage) [DP1]; locator must forbid embedding any secret [DP3].
- **Med:** credential supplied out-of-band [DP3]; locator carries concrete store-target coordinates incl. branch/ref [DP3]; cache read-resolution model + staleness bound + active-feature-only hydration [DP2]; pin exactly three named candidate stores [DP4]; reviewer checks for address-stability [DP1] and durable-tier-stays-in-repo + exec-commit-drops-body [DP2].
- **Low:** raw-markdown round-trip in DP1 check; secret-at-rest neutral wording [DP3]; always-latest⇄backend-consistency line + access-surface token-cost capability + single-source auth ref [DP4]; offline-access risk entry [DP4]; resolve simplify-report `<!-- pm-disposition: -->` + positively-restate revision flows [DP2]; migration-only-as-flag reviewer check [DP4].
- **simplify ALTERNATIVE:** proposed collapsing four deliverables into two. Adopted simplify's de-dup (removed DP1's redundant leakage check; DP4 owns it on the whole document) but kept the 4-deliverable structure (per-section checks are now deliverable-specific and distinct; granular commits give cleaner history). PM approved as-is.

### Post-review PM clarifications (2026-06-02)
- **Store topology:** ONE shared store for all repos, segregated by `<repo-id>` namespace (not one store per repo). Folded into §Record model, §Locator, §Chosen execution target.
- **Bootstrap:** first use in a repo creates that repo's namespace + writes the locator; added to the §Lifecycle session-entry row and DP2 validation.
- **Migration:** forward-only / optional confirmed — existing artifacts are not migrated; only new features externalize. (No scope change; reaffirms brief stance.)
