# Execution Plan: Repo Memory & Recall Layer (Phase 1)
_Implements: product-brief_memory-recall-layer.md · Date: 2026-06-01_

## Context
Give the strategic-implementation skill a derived, rebuildable memory over its own markdown artifacts so the agent recalls how past work was done — at the moment it starts a deliverable and while drafting a plan — instead of re-deriving it. Markdown stays canonical; a local SQLite index (full-text now, local-embedding vectors in a gated Phase 1b) is derived and git-ignored. Ingest is typed/selective/status-aware so noise and abandoned attempts never surface as precedent. Historical work backfills as searchable-only and never auto-promotes into curated learnings. The make-or-break gate is precision: recalled context must *replace* re-derivation (net point-of-use tokens neutral-or-lower), proven on a pinned repeat case **before** the vector leg's complexity/runtime risk is taken on.

## Review-driven resequencing (why this differs from the first draft)
A verified machine fact reshaped the plan: the resident interpreter (`python3`, python.org 3.13 — the same one `code-review-graph` runs on) has `enable_load_extension` **compiled out**, so `sqlite-vec` (the vector leg) cannot load here without a Homebrew python or `apsw`. FTS5 + BM25 are verified working on the stock interpreter. Since the brief's §3 success signal is an **exact-domain repeat** (the containerized-e2e case) that BM25 satisfies, the vector leg (brief D3's *wording-mismatch* acceptance step) is deferred to **Phase 1b**, gated behind the BM25 path proving the success signal. This isolates all new-dependency + extension-load risk behind a green gate. Phase 1a (D1–D5) runs entirely on the verified FTS5/BM25 stack with zero extension risk.

## Library lifecycle audit

### Python runtime (new to the plugin; present on the machine)
- **State that persists:** plugin gains a `scripts/memory/` Python package + pinned `requirements.txt`. No daemon; scripts invoked per-call (build / recall) like `token-report.sh`, with a thin `*.sh` entrypoint.
- **Quirks / gotchas:** first Python in a bash-only plugin. `code-review-graph` (Python) is already installed, so an interpreter exists; scripts must resolve an interpreter without assuming a venv. Pre-flight verifies interpreter + deps; any miss → one-line message, **exit 0** (recall degrades to "no memory available", never blocks). `recall.sh` traps any `recall.py` non-zero/stderr and converts it to silent exit 0 — a malformed index or query-time crash degrades to silence, never a stack trace into the agent's context.
- **Doc consulted:** in-repo `plugins/strategic-implementation/scripts/token-report.sh` (house style: `set -uo pipefail`, graceful degrade, exit 0).

### SQLite + FTS5 (BM25 leg) — Python stdlib `sqlite3` — VERIFIED AVAILABLE
- **State that persists:** one index file per consuming repo at `docs/strategic-implementation/.memory/index.db` (git-ignored, rebuildable). FTS5 virtual table of distilled records + a metadata table (record type, status, domains, source path, anchor, content hash, schema-generation).
- **Quirks / gotchas:** FTS5 + `bm25()` ranking confirmed present on the resident interpreter (probed on `:memory:`). Pre-flight probe still runs; absence fails the *build* (not execution). `schema.sql` is **FTS5 + metadata only** — no `vec0` DDL (that is created lazily in Phase 1b, guarded, so the BM25 leg never inherits extension-load risk).
- **Doc consulted:** SQLite FTS5 docs (BM25 built in).

### git
- **State that persists:** markdown canonical + committed; `.memory/` git-ignored.
- **Quirks / gotchas:** index is never the source of truth; add `docs/strategic-implementation/.memory/` to `.gitignore`.
- **Doc consulted:** repo `.gitignore` (minimal; new derived-artifact entry required).

### code-review-graph MCP — consumed, not modified. Out of scope.

### [Phase 1b only] sqlite-vec + fastembed (ONNX local embeddings)
- **State that persists:** `vec0` virtual table in the same db file; ~100MB ONNX model (`BAAI/bge-small-en-v1.5`, 384-dim) cached locally after a one-time inbound fetch; `model_id` + `dim` written to index metadata.
- **Quirks / gotchas:** (1) `enable_load_extension` is **compiled out** on the resident python.org build — VERIFIED; Phase 1b requires a Homebrew python or the `apsw` carrier, documented as a setup prerequisite, not a silent degrade. (2) The probe must catch **AttributeError** (attr absent), not only `OperationalError`. (3) `vec0` tables are fixed-dimension — a model change requires **DROP + recreate** the `vec0` table, not just re-embedding. (4) `requirements.txt` pins exact `==` versions for `fastembed`, `sqlite-vec`, `onnxruntime`, `tokenizers` + the model id; verify darwin-arm64 wheels exist (no source build). (5) One-time model fetch is an inbound download (model weights from a CDN) — it does **not** violate the no-egress HARD DECISION (no repo content leaves); flag as a one-time network prerequisite + document an air-gapped pre-seed path.
- **Doc consulted:** sqlite-vec README (extension load + `vec0`); fastembed README (offline after first download); Apache-2.0 / MIT licenses (no copyleft).

---

## Deliverables (DAG)

> **Phase 1a = D1 → D2 → D3 → D4 → D5** (BM25 only, verified stack, zero extension risk; proves the success signal). **Phase 1b = D6** (vector leg), gated behind D5 passing.

### D1 — Go-forward capture schema: status/domain tags + GOTCHA block
- **Integration-risk class:** d
- **User-acceptance steps (from brief D1):**
  1. Run an implementation through the skill to completion.
  2. Open the resulting validation log and post-mortem; observe a short structured header recording status (completed / abandoned / superseded), domains touched, and outcome.
  3. Ask the skill to recall prior work in one of those domains; results narrow to that domain and exclude others. _(Domain-narrowing is exercised by D2's cross-domain integration assertion, since D1 is schema-only.)_
- **Validation method (chosen here):** cli — grep `executing-plans/SKILL.md` + `post-execution/SKILL.md` for the new frontmatter-emit instructions and the `## GOTCHA — D<n>` block spec; author one sample `validation-log.md` with the frontmatter and confirm the D2 parser reads `status`/`domains`. (L-005: skill instructions load on plugin reload, not mid-session — static grep + sample is the honest check, not a live run.)
- **Files:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md`, `plugins/strategic-implementation/skills/post-execution/SKILL.md`
- **Steps:**
  1. executing-plans: extend the validation-log header with optional frontmatter (`status`, `domains`, `outcome`, `supersedes`); add a `## GOTCHA — D<n>` block ("we lost time on X; do Y first") alongside the existing additive `## APPROACH` block.
  2. post-execution: same frontmatter on the post-execution-report header (`status` derived from the PASS/FLAG/BLOCK verdict).
  3. Keep all fields optional so older logs stay valid (additive, like APPROACH).
- **Deps:** none
- **Pre-flight env check:** repo only.
- **may-invalidate:** [`plugins/strategic-implementation/skills/executing-plans/SKILL.md`, `plugins/strategic-implementation/skills/post-execution/SKILL.md`]
- **Consumer audit:** changes the validation-log/post-mortem header shape. Consumers: D2 parser (`updated-in-D2` — reads new optional fields); existing review/post-execution readers (`unaffected-because` fields are additive + optional).

### D2 — Index builder: typed/selective/status-aware ingest + normalizer + backfill (BM25/FTS5)
- **Integration-risk class:** a
- **User-acceptance steps (from brief D4 + D5):**
  1. Query memory in a domain including a past abandoned attempt; the abandoned attempt is not returned as recommended (or clearly marked abandoned).
  2. Transient state notes, telemetry reports, and mockups never appear.
  3. Search a topic only in older implementations; relevant historical hits returned; curated learnings list unchanged.
- **Validation method (chosen here):** integration-test — run the builder against the real plugin corpus AND a fixture mirroring the 3 schema generations; assert: (a) only typed records ingested (APPROACH/GOTCHA/DEVIATION/SPIKE blocks, post-mortem findings, spec, simplify findings); (b) noise excluded by filename (`checkpoint.md`, `token-report.md`, `*.html`, assets) — zero such records; (c) status inference correct (see step 4) incl. a Gen-A folder tagged `complete-legacy`, not `aborted`; (d) duplicate content (same hash) collapses to one record; (e) backfill writes only episodic records — `project-learnings.md` untouched; **(f) cross-domain exclusion** — two records tagged domain-A vs domain-B, a domain-A-filtered query returns zero domain-B records (covers brief D1 step 3). Real SQLite, no mocked seam.
- **Files:** `scripts/memory/build_index.py`, `scripts/memory/ingest.py` (typed extractors + normalizer), `scripts/memory/schema.sql`, `scripts/memory/requirements.txt`, `scripts/memory/MEMORY-DOCTYPES.md` (the readable include/exclude manifest), `.gitignore`
- **Steps:**
  1. Define the uniform record (id, type, status, domains[], source_path, anchor, distilled_text, content_hash, schema_generation) + SQLite schema (FTS5 table + metadata table; **FTS5/metadata only, no vec0**).
  2. Normalizer mapping 3 generations: Gen-A `session-*-log.md`/`implementation-guide.md` → DEVIATION/approach-equivalent; Gen-B/C `validation-log.md` blocks + `post-execution-report.md` findings + `spec.md` + `simplify-report-*.md` findings.
  3. Selective ingest: include only typed records; exclude `checkpoint.md`, `token-report.md`, `*.html`, `*.svg/.css/.json/.txt` by path. Record the include/exclude rule set in `MEMORY-DOCTYPES.md` (the readable artifact satisfying brief §4's "records which document types count as memory").
  4. **Generation-aware status inference:** `complete` if a PASS `post-execution-report.md` exists; `complete-legacy` for Gen-A folders with an implementation-guide/session log and no abort marker (predate post-exec reports — searchable, NOT demoted); `superseded` if a `supersedes` frontmatter points at it; `aborted` only on an explicit abort marker OR a stub with no completion signal at all (≤2 files used only as a last-resort tiebreaker). Aborted/superseded demoted/excluded as precedent by recall.
  5. Dedupe by `content_hash` (handles the consuming repo's duplicated mockup-spec copies without deleting files).
  6. Backfill all historical folders (episodic-only); never write `project-learnings.md`. Git-ignore `docs/strategic-implementation/.memory/`.
- **Deps:** D1 (parser reads D1 optional frontmatter, tolerates absence)
- **Pre-flight env check:** interpreter resolvable; FTS5 probe passes; `requirements.txt` installed (BM25-leg deps only — no fastembed/sqlite-vec in Phase 1a).
- **may-invalidate:** [`docs/strategic-implementation/documentation-registry.md`, `plugins/strategic-implementation/README.md`] (register new scripts + index artifact; README note that the plugin now has a Python surface under `scripts/memory/`)
- **Consumer audit:** defines the db schema. Consumers: D3 recall (`updated-in-D3`); D6 vector leg attaches `vec0` lazily (`updated-in-D6`, no migration — schema accommodates a later attach). No external consumer.

### D3 — BM25 recall command: ranked distilled snippets + pointers, or nothing
- **Integration-risk class:** a
- **User-acceptance steps (foundation for brief D2):**
  1. Query the built index for a known repeat case (a containerized e2e test); the prior APPROACH returns with a source pointer.
  2. A query with no good match returns nothing (not a low-relevance dump).
  3. Abandoned-status records are not returned as precedent.
- **Validation method (chosen here):** integration-test — against the D2-built index: assert the Docker-case query returns the expected APPROACH + pointer above threshold; a deliberately-unrelated query returns zero rows (threshold honored); aborted records excluded. Real db.
- **Files:** `scripts/memory/recall.py`, `scripts/memory/recall.sh` (thin bash entrypoint, token-report.sh style — swallows any recall.py non-zero/stderr into silent exit 0)
- **Steps:**
  1. Query interface: inputs = free text + optional facet filters (domains, type, integration-risk class); output = top-k (≤3) distilled snippets each with `source_path` + anchor, or empty.
  2. BM25 ranking via FTS5 `bm25()`; relevance threshold so below-bar queries return nothing; status filter excludes/demotes aborted/superseded.
  3. Compact, ranked, pointer-carrying output (not whole files), suitable for inline injection. `recall.sh` reads the index only; **never** triggers build/embed.
- **Deps:** D2
- **Pre-flight env check:** index db exists (else "no memory yet", exit 0); interpreter + BM25 deps.
- **may-invalidate:** [`docs/strategic-implementation/documentation-registry.md`]
- **Consumer audit:** n/a — reads D2 schema.

### D4 — Wire recall at point-of-need (delivers brief D2; BM25 half of brief D3)
- **Integration-risk class:** c
- **User-acceptance steps (from brief D2 + D3):**
  1. Start executing a plan whose next deliverable is in a previously-solved domain; before any build work, the skill shows a short ranked list of relevant prior approaches with pointers.
  2. The surfaced approach captures the prior lesson (e.g. "run the e2e test in a container first") and the agent proceeds with it.
  3. During plan drafting, a relevant prior approach is surfaced (exact-domain match in 1a; wording-mismatch match arrives with D6).
- **Validation method (chosen here):** post-hoc — cli grep confirms (a) the per-deliverable pre-flight recall instruction in executing-plans Step 2a and (b) the replacement of the Step 6 N-most-recent grep in execution-plan with a recall-command call; the live mid-session demo is a deferred post-hoc trial (L-005). Class c — cannot be honestly exercised live this session; declared post-hoc, not tdd. **Post-hoc protocol** (written to the feature folder): reviewer = PM; trigger = first executing-plans run after plugin reload; pass criterion = recall fires before build and surfaces a pointer-carrying snippet.
- **Files:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md` (Step 2a), `plugins/strategic-implementation/skills/execution-plan/SKILL.md` (Step 6), `docs/strategic-implementation/2026-06-01-memory-recall-layer/post-reload-verification.md`
- **Steps:**
  1. executing-plans Step 2a: before the env check, for `Macro-deliverable` or integration-risk `a|b|c` deliverables, call recall (**BM25-only on this hot path** — no model load) with the deliverable's domain/type; inject returned snippets as advisory pre-flight context (informs, never dictates). No hit → proceed silently. Read index only; never rebuild inline.
  2. execution-plan Step 6: replace the verbatim `grep over N-most-recent validation-log.md for ## APPROACH` with a recall-command call (BM25 in 1a; vector fusion added in D6, which fires once per plan, not per deliverable). Preserve "advisory only; absent → proceed silently".
  3. Write the post-reload verification protocol doc (the concrete home for the L-005-deferred brief D2/D3 live checks).
- **Deps:** D3
- **Pre-flight env check:** recall command runnable; index present (else advisory step no-ops).
- **may-invalidate:** [`plugins/strategic-implementation/skills/executing-plans/SKILL.md`, `plugins/strategic-implementation/skills/execution-plan/SKILL.md`]
- **Consumer audit:** n/a — skill-instruction edits, no data shape change.

### D5 — Precision A/B gate (make-or-break; runs on the BM25 path)
- **Integration-risk class:** a
- **User-acceptance steps (from brief §3 success signal):**
  1. On the pinned containerized-e2e-test case, run recall-on vs recall-off; observe whether the prior approach is adopted at deliverable start without rediscovery.
  2. Point-of-use token count recall-on ≤ recall-off (net neutral-or-lower).
  3. The relevance threshold + precision check are recorded and reproducible.
- **Validation method (chosen here):** integration-test + post-hoc — the precision script loads a **committed fixture** `memory-fixtures/labeled-set.json` (each query string; expected record id(s); a relevant=true/false label per (query,record); and the numeric BM25/threshold + top-k values) — thresholds are pinned in the fixture BEFORE the script runs, not chosen inline. Script asserts precision@k ≥ target and token delta ≤ 0 over the labeled set. The live agent-adoption half is post-hoc with a scheduled home: reviewer = PM; trigger = first executing-plans run after reload; pass criterion = the agent's chosen approach cites the recalled snippet (pointer or paraphrase), with a token-delta observation vs a recall-disabled run. If precision/token targets miss, this gate FLAGs for PM decision before the feature is considered shipped.
- **Files:** `scripts/memory/precision_ab.py`, `plugins/strategic-implementation/skills/.../memory-fixtures/labeled-set.json` (committed), findings doc in the feature folder.
- **Steps:**
  1. Author + commit the labeled set + threshold fixture first.
  2. Run recall-on/off over the fixture; compute precision@k + token delta; assert against the committed thresholds.
  3. Write results to the feature folder; FLAG on miss.
- **Deps:** D4
- **Pre-flight env check:** built index; committed fixture present.
- **may-invalidate:** none
- **Consumer audit:** n/a.

### D6 — [Phase 1b] Vector leg: local ONNX embeddings + sqlite-vec; plan-time hybrid fusion
- **Integration-risk class:** a
- **Gating:** built only after D5 passes on the BM25 path. **Requires an extension-capable interpreter** (Homebrew python or `apsw`); on a python.org build the extension cannot load — documented prerequisite.
- **User-acceptance steps (from brief D3):**
  1. Draft/query for work in a known domain with different wording than the past write-up; the relevant prior approach is still surfaced.
  2. A wording-only difference that BM25 alone missed is now returned.
  3. No network egress after the one-time model download; the embedding `model_id` + `dim` are recorded.
- **Validation method (chosen here):** integration-test — on an extension-capable interpreter: build embeddings; assert a differently-worded query returns the semantically-correct prior record that D3 BM25 misses; assert RRF fusion ordering; assert `model_id`+`dim` persisted and a second run is offline (run with egress blocked at the OS level and assert exit 0 + no new outbound connections — not merely a warm-cache pass). **If no extension-capable interpreter is resolvable, this integration-test is SKIPPED-WITH-REASON, not asserted green**, and recall stays BM25-only.
  - Re-run D5's A/B after D6 to confirm the vector leg does not regress point-of-use tokens.
- **Files:** `scripts/memory/embed.py`, updates to `build_index.py` (lazy `vec0` create, guarded by an AttributeError-and-OperationalError-catching probe), `recall.py` (BM25+vector RRF fusion at plan-time Step 6 only), `requirements.txt` (`fastembed`, `sqlite-vec`, `onnxruntime`, `tokenizers` — exact pins)
- **Steps:**
  1. Probe chain: `enable_load_extension` exists (catch AttributeError) → True succeeds → `sqlite_vec.load` → `vec0` CREATE works; any failure → log once, recall stays BM25-only.
  2. Lazily create the `vec0` table (fixed dim); embed each distilled record; persist `model_id`+`dim`. On model-id OR dim mismatch, DROP + recreate `vec0` before re-embedding.
  3. Extend recall to fuse BM25 + vector via RRF + threshold + status filter, **at plan-drafting Step 6 only** (the per-deliverable hot path stays BM25-only).
- **Deps:** D5 (pass)
- **Pre-flight env check:** extension-capable interpreter; `sqlite-vec` loadable (probe); model fetchable once then cached.
- **may-invalidate:** [`docs/strategic-implementation/documentation-registry.md`]
- **Consumer audit:** adds `vec0` + metadata columns. Consumer: `recall.py` (`updated-in-this-deliverable`).

## Parallel groups & order
- **Phase 1a spine (build before wire):** D1 → D2 → D3 → D4 → D5. D1 (skill-text schema) may proceed alongside D2 scaffolding but D2's parser must land D1's field names — treat D1 as a soft predecessor.
- **Phase 1b:** D6, only after D5 passes. Strictly gated.
- The entire success-signal path (D1–D5) is BM25-only on the verified FTS5 stack — zero extension-load risk on the critical path.

## Reused existing patterns
- `scripts/token-report.sh` — deterministic-script house style (`set -uo pipefail`, graceful degrade, exit 0, thin bash entrypoint over logic).
- `scripts/hook-helpers.sh` — state/path patterns if a refresh hook is added later (not in Phase 1).
- Existing additive `## APPROACH — D<n>` block — extended, not replaced; recall already tolerates its absence in old logs.
- `documentation-registry.md` — register new scripts + index artifact + the Python surface.
- execution-plan Step 6 advisory-recall contract ("advisory only; absent → proceed silently") — preserved verbatim when swapping the mechanism.

## Risks & contingencies
- **Precision is make-or-break (brief §6).** If D5 shows recall adds tokens or low-relevance hits: raise threshold / lower k; if still failing, the gate FLAGs and D4 wiring ships disabled-by-default pending tuning. Recall is always advisory and degrades to silence — never blocks or harms execution.
- **`enable_load_extension` compiled out on the resident interpreter (VERIFIED).** The vector leg (D6) is non-functional on python.org 3.13; it requires Homebrew python/`apsw`. Phase 1a is unaffected (BM25 only). D6 acceptance is skip-with-reason if no extension-capable interpreter; recall defaults to BM25-only on this machine.
- **New Python runtime in a bash-only plugin.** Isolated to `scripts/memory/`, pinned `requirements.txt`, pre-flight dependency check, `recall.sh` swallows crashes into silent exit 0.
- **Status mislabeling across generations.** Generation-aware inference + `complete-legacy` for Gen-A; `aborted` only on explicit signal; dedupe-at-ingest. Old Gen-A logs map best-effort (acceptable; never promoted).
- **vec0 dimension drift (Phase 1b).** Re-embed triggers on model-id OR dim mismatch and DROPs+recreates the vec0 table.
- **Small corpus today.** BM25 + tags + triggers carry near-term value; vector value scales with corpus growth (documented trajectory). D5 is the decision point for whether D6's complexity is worth it now.

## Out of scope for this plan
- Temporal/bi-temporal supersession graph and cross-repo memory (Phase 2).
- Rebuilding the structural code graph (consumed as-is).
- Auto-promotion of any record into `project-learnings.md` (human curation gate unchanged).
- **Physical deletion of the consuming repo's duplicated mockup files** — handled as dedupe-at-ingest instead (deleting canonical files is an anti-goal; the dup copies live in a *different* repo). Surfaced for PM: if you want the on-disk copies physically removed in the consuming repo, that's a separate one-time cleanup, not a plugin deliverable.
- An always-on index-refresh hook (Phase 1 rebuilds on demand; a FileChanged refresh hook is a later optimization).
