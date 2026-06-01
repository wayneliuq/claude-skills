# Product Brief: Repo Memory & Recall Layer

_Slug: memory-recall-layer · Date: 2026-06-01 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> The strategic-implementation skill now remembers how past work was actually done. When the agent is about to build a deliverable, it is shown the relevant prior approaches — drawn from earlier validation logs and post-mortems — before it starts, so it reuses what worked instead of re-deriving it (and stops repeating known mistakes, like rediscovering that an end-to-end test should run in a container first). Plan drafting surfaces the same memory, and now matches on meaning rather than exact wording, so a relevant past solution is found even when it was described differently. The memory is searchable across every past implementation in the repo, yet abandoned attempts and routine bookkeeping never resurface as if they were proven precedent. Everything stays on the machine and in the repo's own files — nothing is sent anywhere and nothing replaces the documents the PM already reviews.

## 2. What the user does / sees

**Who is the user of this feature:** The internal strategic-implementation team — the PM and the planning/execution agent — operating through the strategic-implementation skill inside Claude Code. Every acceptance step below is performable from within that skill's normal run, or by reading the repo's strategic-implementation documents.

### D1 — Going-forward, each validation log and post-mortem carries structured status and domain tags, so memory can be filtered precisely.
**How a user verifies:**
1. Run an implementation through the skill to completion.
2. Open the resulting validation log and post-mortem; observe a short structured header recording the work's status (completed / abandoned / superseded), the domains it touched, and its outcome.
3. Ask the skill to recall prior work in one of those domains; observe results narrow to that domain and exclude other domains.

### D2 — Before building each deliverable, the skill surfaces the most relevant prior approaches for that deliverable.
**How a user verifies:**
1. Start executing a plan whose next deliverable is in a domain the team has solved before (e.g. a containerized end-to-end test).
2. Observe that, before any build work begins, the skill shows a short ranked list of relevant prior approaches with a pointer to where each came from.
3. Confirm the surfaced approach captures the prior lesson (e.g. "run the end-to-end test in a container first") and that the agent proceeds with it rather than re-deriving the approach from scratch.

### D3 — Plan drafting recalls relevant prior approaches by meaning, not just exact keywords.
**How a user verifies:**
1. Draft an execution plan for work in a domain the team has handled before, but describe it with different wording than the past write-up used.
2. Observe the relevant prior approach is still surfaced during planning.
3. Compare against the old behavior: a wording-only difference that previously surfaced nothing now returns the relevant precedent.

### D4 — Recall only ever returns trustworthy precedent: routine bookkeeping is excluded, and abandoned or superseded attempts are never presented as proven.
**How a user verifies:**
1. Query memory in a domain that includes a past abandoned attempt.
2. Confirm the abandoned attempt does not appear as a recommended approach (or appears clearly marked as abandoned, never as precedent).
3. Confirm transient state notes, cost/telemetry reports, and visual mockups never appear in recall results.

### D5 — Every past implementation in the repo becomes searchable memory, without any of it silently becoming curated team guidance.
**How a user verifies:**
1. Search memory for a topic addressed only in older implementations; confirm relevant historical hits are returned.
2. Open the curated learnings list and confirm it is unchanged — no entries were added automatically from the historical backfill.
3. Confirm that promoting any historical finding into curated guidance still requires an explicit human confirmation, exactly as today.

## 3. Success signal

On a pinned, known-repeat scenario (the containerized end-to-end test case), the agent adopts the prior approach at the moment it starts the deliverable — without rediscovering it — and the point-of-use token count for reaching that approach is equal to or lower than a baseline run with recall disabled. In aggregate across new implementations, surfaced recall is referenced in the chosen approach more often than it is ignored, with no net increase in point-of-use tokens.

## 4. Boundaries

**In scope:**
- Searchable memory over past episodic work: validation logs, post-mortems, execution plans (status-gated), specs, and simplify findings.
- Structured status/domain/outcome tags on go-forward validation logs and post-mortems.
- Recall at point-of-need (before each deliverable during execution) and at plan-drafting time, replacing today's narrower lookup that only finds prior work when the wording matches.
- Selective, status-aware capture: bookkeeping and visual artifacts excluded; abandoned/superseded work tagged so it is never shown as precedent.
- One-time searchable backfill of all existing implementations in the repo.
- A one-time cleanup that removes duplicated mockup copies and records which document types count as memory.
- Memory that lives entirely on the machine and can be fully rebuilt from the repo's own files at any time.

**Out of scope:**
- Tracking how a fact changes over time / automatically retiring superseded facts as a first-class capability (deferred to a later phase).
- Memory shared across multiple repositories (deferred to a later phase).
- Any change to the structural code map the team already uses.
- Automatically writing or editing curated team guidance.

**Anti-goals (philosophy-level — we deliberately will not):**
- Make the derived memory the source of truth — the repo's reviewed documents always are.
- Let the agent auto-edit curated guidance; promotion stays a human decision.
- Maximize recall coverage at the expense of precision — surfacing nothing is preferable to surfacing noise.
- Send any repository content off the machine.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Source of truth | The repo's reviewed documents stay canonical; the memory is derived from them and fully rebuildable | `[HARD DECISION]` |
| Data residency & cost | Memory stays entirely on the machine — nothing is sent anywhere, no per-use cost | `[HARD DECISION]` |
| Historical work vs curated guidance | Past implementations are searchable, but none is ever auto-promoted into curated team guidance | `[HARD DECISION]` |
| When recall fires | At point-of-need before each deliverable, and at plan-drafting time | `settled` |
| What gets captured | Selective by document type and status — never whole-folder | `settled` |
| Precision over coverage | A relevance bar applies; below it, recall returns nothing rather than noise | `settled` |
| Time-aware supersession & cross-repo memory | Deferred to a later phase | `settled` |

**Source of truth — tradeoff:**

| Option | Pro | Con | Verdict |
|---|---|---|---|
| Memory derived from files (chosen) | Reviewed docs stay authoritative; memory can be deleted and rebuilt; survives format changes | Memory can briefly be behind the latest files | **Chosen** — preserves PM approval + version history |
| Memory becomes the store of record (files no longer canonical) | Single place to look | Loses human-readable, version-controlled, reviewable artifacts | Rejected |

**Data residency & cost — tradeoff:**

| Option | Pro | Con | Verdict |
|---|---|---|---|
| Fully local (chosen) | $0, offline, no content leaves the machine | Adds a local capability to the toolchain | **Chosen** — free and safe for a proprietary repo |
| Hosted/cloud memory service | Less to maintain | Recurring cost, content egress, network dependency | Rejected |

**Historical work vs curated guidance — tradeoff:**

| Option | Pro | Con | Verdict |
|---|---|---|---|
| Backfill is searchable only (chosen) | Full recall reach without polluting trusted guidance | Historical hits are unvetted; must be marked as such | **Chosen** — protects curated guidance from unreviewed history |
| Auto-promote historical findings into guidance | More guidance immediately | Imports unreviewed, possibly-wrong precedent as if trusted | Rejected |

## 6. Risks & unknowns

- **Precision is the make-or-break risk.** If recall surfaces irrelevant hits, it adds tokens instead of saving them — inverting the goal. Execution-plan owns defining the relevance bar and a concrete, measurable precision check on the pinned repeat case before this is considered working.
- **"Used instead of re-derived" is partly qualitative.** Needs a concrete observable — e.g. the surfaced precedent is cited in the chosen approach, plus a point-of-use token comparison against a recall-disabled baseline on a pinned scenario. Owner: execution-plan / tests.
- **Historical corpus is unreviewed and uneven** — 46 implementations, several stubs or abandoned runs across three different historical document formats. Mitigated by status-tagging and searchable-only backfill; older-format records map on a best-effort basis and may be less precise.
- **Index staleness** — the derived index can lag the files between refreshes; it must refresh on change and rebuild cheaply. Local rebuild is inexpensive at current corpus size (~150 high-signal documents).
- **Local embedding capability is a new dependency** in the toolchain (a model file + a local runtime); it must be version-pinned so stored vectors stay comparable over time. Flagged for runtime-risk and technical-expert review.
- **Corpus is small today** (~150 high-signal documents); the meaning-based search and local index earn most of their value as the corpus grows (~150 implementations/year). The cheapest parts (tags + selective capture + keyword search + point-of-need triggering) carry most of the near-term value.

## 7. References & revision log

**Document references:**
- Architecture: `docs/strategic-implementation/2026-04-20-v2-redesign/spec.md`; `plugins/strategic-implementation/README.md`
- UX/PMF: n/a — no external user-facing surface (user is the internal strategic-implementation team)
- Security policy: none — local-only index, local embeddings, no data egress
- Schema/ERD: none prior — this feature defines the capture-tag schema and the derived-index schema

**Affected skill files (internal plumbing — for execution-plan):**
- `plugins/strategic-implementation/skills/executing-plans/SKILL.md` — per-deliverable pre-flight recall; status/domain tags on validation logs
- `plugins/strategic-implementation/skills/execution-plan/SKILL.md` — replace the N-most-recent keyword grep (Step 6 validation-approach recall) with the hybrid index query
- `plugins/strategic-implementation/skills/post-execution/SKILL.md` — status/domain/outcome tags on post-mortems; curation gate unchanged
- New index build/refresh + recall scripts under `plugins/strategic-implementation/scripts/`
- Index artifact under each consuming repo's `docs/strategic-implementation/` (git-ignored, rebuildable)

**Revision log:**
- v0.1 · 2026-06-01 · initial draft
- v0.2 · 2026-06-01 · leakage self-revision — replaced implementation nouns ("search index", "database", "keyword-only lookup") in §4/§5 with user-observable behavior phrasing
- v0.3 · 2026-06-01 · leakage cleanup — remaining "search index" → "derived memory" in §4 anti-goals; softened "lag the files until refreshed"; kept "structural code map" and "simplify findings" as named skill-system artifacts (caveat-allowed)
