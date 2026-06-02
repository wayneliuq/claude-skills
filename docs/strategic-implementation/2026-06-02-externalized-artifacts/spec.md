# Spec: Externalized Artifact Store

_Slug: externalized-artifacts · Date: 2026-06-02 · Status: draft_
_Implements: product-brief_externalized-artifacts.md · execution-plan.md_

## 1. Context & motivation

The strategic-implementation skill writes ~5–9 markdown artifacts per feature into `docs/strategic-implementation/<date>-<slug>/`. They are committed, so every clone of every repo the skill runs in inherits them, and any skill-less agent scanning such a repo spends tokens parsing them. Yet the maintainer wants these artifacts to persist across worktrees, sessions, and devices — which the in-repo location cannot give (worktrees share no working state; a clone on another device is a different checkout).

This spec defines how the **transient per-feature artifacts** move out of the repo into a **server-authoritative external store**, leaving each repo with only a tiny pointer. It is **backend-neutral**: anything true of only one store lives behind the adapter contract (§3), never in the record shape (§2). A separate later implementation pass builds the adapter, the locator, and the cache against a chosen store; this document is the contract that pass implements.

## 2. North star

> Run the skill on any feature in any repo; its per-artifact records land in one shared server-authoritative store under that repo's namespace, are surfaced locally without a web portal, and the repo carries no artifact content — only a one-line pointer to the store.

## 3. Users

- **Primary:** the maintainer of the strategic-implementation skill, operating it through Claude Code. "Uses" this spec by reading it and confirming it is complete and unambiguous enough to implement any one backend with no further design decisions.
- **Secondary:** any skill-less agent working in a different repo, who must never encounter these artifacts at all.

## 4. Locked decisions (HARD — carried from the approved brief §5)

| # | Decision |
|---|---|
| 1 | One separately addressable record per artifact (not a composite document). |
| 2 | Canonical address `<repo-id>/<date-slug>/<artifact-name>`, stable across worktree / device / session. |
| 3 | Durable tier (`project-learnings.md`, `documentation-registry.md`) stays in the repo, untouched. |
| 4 | The external store is authoritative; any local copy is a disposable read-through cache, never the source of truth. |
| 5 | Human feedback is conversational only; records are output-only, never hand-edited. |
| 6 | Existing-artifact migration is forward-only / optional — a per-backend capability, never a required step. |
| 7 | Concurrent-write handling is **best-effort** (surfaced where the backend supports it; last-write-wins tolerable for solo use) — NOT a hard guarantee. |
| 8 | Backend-neutral record shape, proven against candidate stores with the shape held constant. |
| 9 | Chosen execution target for the later pass: a single dedicated private GitHub repository, shared across all repos. |
| 10 | In-repo footprint is exactly one committed locator file per repo (pointer only, no artifact content). |

## 5. Record model

### 5.1 What a record is

One artifact = one record. The full set the skill externalizes (the *records*):

| Record | Pattern |
|---|---|
| Product brief | `product-brief_<slug>.md` |
| Execution plan | `execution-plan.md` |
| Validation log | `validation-log.md` |
| Checkpoint | `checkpoint.md` |
| Simplify report | `simplify-report-NN.md` |
| Token report | `token-report.md` |
| Post-execution report | `post-execution-report.md` |
| Brief sidecar | `brief-meta.yaml` |
| UI mockup | `mockup.html` |
| Spec | `spec.md` |
| Research / spec extras | `research-findings.md`, `spec.md`, feature-specific notes |

Excluded from externalization (stay in-repo, per locked decision 3 and the existing `MEMORY-DOCTYPES.md` durable/derived split): `project-learnings.md`, `documentation-registry.md`, and the derived `.memory/` index.

Each record is **raw markdown** (or the artifact's native text, e.g. YAML for the sidecar, HTML for the mockup) — no wrapper format is part of the record.

### 5.2 Address

The canonical address of a record is:

```
<repo-id>/<date-slug>/<artifact-name>
```

- `<repo-id>` — a stable identifier for the repo the skill is running in (assigned once at bootstrap, recorded in that repo's locator). It is the **namespace** segment.
- `<date-slug>` — the feature folder name, `<YYYY-MM-DD>-<slug>` (the existing convention).
- `<artifact-name>` — the record filename from §5.1.

**Stability:** the address is a pure function of (repo-id, feature, artifact-name). None of those depend on which checkout, worktree, machine, or session resolves it — so the same feature's records resolve to the same addresses from anywhere. The `repo-id` lives in the committed locator (§ Locator), so every worktree/clone of a repo carries the same `repo-id` and therefore the same addresses.

### 5.3 Store topology

There is **ONE shared store** for every repo the skill runs in. Records from different repos never collide because the `<repo-id>` segment namespaces them: repo A's records live under `A/...`, repo B's under `B/...`, in the same store. A new repo is onboarded by assigning it a `repo-id` namespace at bootstrap (§ Lifecycle, session-entry) — no new store is provisioned per repo.

### 5.4 Listing

The store MUST support enumerating all records under one feature — i.e. listing everything addressed by the prefix `<repo-id>/<date-slug>/` — without the caller knowing the artifact names in advance. The catalog is always resolved **live from the store** (never cached as the source of truth, never duplicated in-repo).

## 6. Adapter contract

A store is usable iff an adapter can provide the three required operations below over markdown records addressed per §5.2. Operations are defined abstractly; the mapping to a concrete store is the adapter's job (§ Backend-neutrality proof).

### 6.1 Required operations

| Operation | Input | Output | Failure behavior |
|---|---|---|---|
| **read-latest** | a record address | the current record body (raw markdown) **and an opaque `version-handle`** for that record | not-found if the address has no record; transport/auth error surfaced to the caller |
| **write** | a record address, the body, **an optional `version-handle`** | success + the new `version-handle` | if a `version-handle` is supplied and the store supports conflict detection and the stored record has advanced past it → **conflict surfaced** (not applied, not silently overwritten); transport/auth error surfaced |
| **list** | a feature prefix `<repo-id>/<date-slug>/` | the set of record addresses under it (live) | empty set if none; transport/auth error surfaced |

### 6.2 Read semantics — always-latest

`read-latest` returns the latest committed record. There is no local source of truth: a read resolves against the store (see § Read-through cache for how the local cache stays consistent with this guarantee). Defeating any backend-side read cache or propagation delay so the returned body is genuinely current is the adapter's responsibility.

### 6.3 Concurrency — best-effort, via an opaque version-handle

The `version-handle` returned by `read-latest` is an **opaque token** — the contract says nothing about its internal form, so no backend-specific value (a git blob SHA, an ETag, a row version) leaks into the record shape. Behavior:

- A backend that supports optimistic concurrency rejects a `write` whose supplied handle is stale, and the adapter **surfaces** the conflict to the caller.
- A backend that does not support it ignores the handle; the `write` is last-write-wins. This is acceptable for solo use (locked decision 7).

A store advertises which behavior it provides via the capability flag `conflict-surfacing: yes | no` (§ Capability flags). Conflict handling is best-effort — the contract never promises that concurrent writes are always safe.

### 6.4 Record format — raw-markdown round-trip

A record written as markdown must read back as the identical markdown body — the contract requires a **raw-markdown round-trip** with no lossy wrapper/transcoding as part of the record. If a backend's wire format wraps content (base64, block JSON, a result envelope), unwrapping it to the original markdown is the adapter's responsibility and MUST be lossless; the wrapper is never part of the record.

### 6.5 Optional capabilities (flags, not requirements)

Capabilities a backend MAY or MAY NOT provide are declared as flags, kept strictly separate from the three required operations so nothing optional becomes mandatory:

- `conflict-surfacing: yes | no` (see §6.3)
- `bulk-migration: <trivial | scriptable | unsupported>` — the ease of importing pre-existing artifacts in one shot. **Optional and forward-only:** migration is never a required operation and is not performed unless explicitly chosen (locked decision 6).

## 7. Lifecycle map

Which records each skill stage reads (R) / writes (W). Bodies live in the store; the cache (§8) is a read-through projection. The durable tier and the locator stay in-repo.

| Stage | Reads | Writes |
|---|---|---|
| **session-entry** (orchestrator) | locator (this repo's `repo-id` + reach-the-store coords) | **bootstrap only:** locator (first use in repo); hydrates the active feature's records into the cache |
| clarify | `documentation-registry.md` (in-repo) | `documentation-registry.md` (in-repo) |
| product-brief-drafter (draft) | — | `product-brief_<slug>.md`, `brief-meta.yaml` |
| product-brief-drafter (revise) | `product-brief_<slug>.md` | `product-brief_<slug>.md`, `brief-meta.yaml` |
| ui-mockup (generate / revise) | `product-brief_<slug>.md`, `mockup.html` | `mockup.html` |
| execution-plan | `product-brief_<slug>.md`, `brief-meta.yaml`, `mockup.html`, prior-feature records (live), `project-learnings.md` (in-repo), `documentation-registry.md` (in-repo) | `execution-plan.md`, `documentation-registry.md` (in-repo) |
| review | `execution-plan.md`, `product-brief_<slug>.md`, `brief-meta.yaml`, `project-learnings.md` (in-repo) | — |
| executing-plans | `execution-plan.md`, `checkpoint.md` | `validation-log.md`, `checkpoint.md`, `simplify-report-NN.md`; per deliverable also `documentation-registry.md` (in-repo) |
| post-execution | `execution-plan.md`, `validation-log.md`, `checkpoint.md`, `documentation-registry.md` (in-repo) | `post-execution-report.md`, `token-report.md`, `simplify-report-NN.md`; appends `project-learnings.md` (in-repo) |
| simplify | changed source files | `simplify-report-NN.md` |

**Durable tier — stays in repo, NOT moved:** `project-learnings.md` and `documentation-registry.md` remain in-repo and are read/written in place (marked "(in-repo)" above). Only the per-feature records (§5.1) move to the store.

**Commit no longer carries the artifact body.** executing-plans' per-deliverable atomic commit currently stages the feature folder's record files. Under this spec it stages only **in-repo** items — the locator (when bootstrap wrote it), the `documentation-registry.md` row, and any in-repo source — never the record bodies, which are written to the store out-of-band. The commit thus carries a pointer + index advance, not the artifact content; a clone of the repo gets no record bodies.

## 8. Read-through cache

A per-session local materialization of records, so the maintainer reads them in an editor without a web portal. It is a **derived projection, never the source of truth** — reusing the established `.memory/` discipline (derived, rebuildable, git-ignored, refreshed at session start; see `MEMORY-DOCTYPES.md`).

- **Single fixed location**, outside any worktree's tracked tree (e.g. a per-repo path under the user/cache area keyed by `repo-id`), and **git-ignored** — it is never committed, in any worktree.
- **Populated at session start** for the **active feature only** (bounded hydration — the cache holds one feature's records, not the whole store, so per-session cost is bounded), and **refreshed when the skill writes** a record.
- **Disposable / deletable with no data loss:** the store is authoritative; deleting the cache loses nothing and it transparently re-hydrates on next access from the store.
- **Worktree-independent:** the cache keys off the record **address** (§5.2), not a path inside a checkout, so a new worktree or a new device gets the current records with no manual sync step.
- **Read-resolution model (makes "always-latest" true):** a record read **resolves through to the store on access** (read-through), not from a stale session-start snapshot. The cache may hold a copy for editor browsing, but a read used by the skill returns the store's latest; the staleness window for a skill-consumed read is therefore zero. (A human eyeballing a cached file may see a copy as fresh as the last hydrate/refresh — acceptable, since humans don't feed the cache back as truth.)

## 9. Revision contract

**Records are output-only.** The skill writes records; the human never edits a record file as a feedback channel (locked decision 5). This replaces the prior file-embedded feedback loops:

- **Brief revision** — previously: PM added `<!-- pm: ... -->` comments inside `product-brief_<slug>.md` and the drafter addressed/removed them. **Now:** the PM gives feedback **conversationally to the agent in chat**; the drafter re-writes the brief record and re-emits it. No inline-comment editing of the record.
- **Mockup revision** — previously: PM edited `mockup.html` with `<!-- pm: ... -->` comments or wrote a sibling `mockup-feedback.md`. **Now:** feedback is **conversational**; ui-mockup re-writes and re-emits `mockup.html`. The `mockup-feedback.md` sibling channel is retired.
- **simplify-report disposition** — the `<!-- pm-disposition: apply|defer|dismiss -->` marker, where the PM edits `simplify-report-NN.md` in place, is the same class of file-edit feedback. **Resolution: retired** — disposition is given conversationally (the report record stays output-only); executing-plans records the chosen disposition rather than reading a hand-edited marker.

No lifecycle stage depends on a human editing a record in place; every feedback path is conversational, and every record is written solely by the skill.

## 10. Confidentiality

Artifacts leave the repo into an external store, so the spec mandates the following — stated **backend-neutrally**, so it holds equally for a private git repository and for a hosted notes service:

- **Private by default.** The store holds records under access control such that only an authenticated principal can read or write them. There is no public/unauthenticated read path. (Stores whose only "private" mode is an unguessable URL do not satisfy this.)
- **Credential supplied out-of-band.** The access credential is resolved at runtime from the agent/host environment (ambient auth). It is **never committed to the repo and never stored in any record** — not in the locator, not in a record body, not in the in-repo durable tier.
- **Secret-at-rest split.** Confidentiality of artifact **content** is the store's responsibility (private-by-default, access-controlled, encrypted in transit). Confidentiality of the **credential** is the host's responsibility (ambient/secret-managed). The repo holds neither the content nor the credential — only the non-secret locator (§11).

This makes the §11 no-secret rule enforceable rather than aspirational: there is a defined place the credential comes from (the host), and it is explicitly not the repo.

## 11. Locator

Exactly **one committed file per repo** — the only in-repo footprint of the externalized store. It is a pure pointer, not a catalog and not content.

- **Single fixed, discoverable location**, with a defined schema, exactly one such file per repo (not one per feature).
- **Schema — load-bearing content only:**
  - `repo-id` — this repo's namespace segment in the shared store (§5.2).
  - `store-target coordinates` — how to reach the shared store: the abstract address of the store and where within it this repo's records live. (Concrete form is filled by §13 Chosen execution target — e.g. for a git store: the store repo's `owner/repo` plus the branch/ref the records live on.)
- **No catalog.** The set of features/records is **resolved live from the store** (§5.4), never enumerated in the locator — so the locator does not drift as features are added.
- **No secret — invariant.** The locator is committed, therefore it **MUST NOT embed any credential / secret / token**. A token in the locator is a defect. It carries only the non-secret coordinates above; the credential is supplied out-of-band (§10).
- **Skill-maintained, output-only.** Written by the skill at bootstrap (§7 session-entry); never hand-edited.
- **Recoverable.** A stale or missing locator is reconstructable from a known store (the `repo-id`/coordinates are stable facts), so the locator is never authoritative over record content — the store is.

**Distinct from `documentation-registry.md`.** The registry is an in-repo human-facing index of *documentation* (locked decision 3, stays in repo); the locator is the machine pointer to the *external store*. Different purpose, different file — they stay separate.

## 12. Backend-neutrality proof

The same record shape (§5: address `<repo-id>/<date-slug>/<artifact-name>`, raw-markdown body) maps onto three structurally diverse stores with **no change to the shape** — only the adapter mapping differs. A git file store, a key-value store, and a hosted notes service are chosen deliberately: the git repo and the notes service jointly stress the backend-neutral confidentiality requirement (§10).

| Contract op / property | GitHub (git file store) | Cloudflare KV (key-value store) | HackMD (hosted notes service) |
|---|---|---|---|
| **read-latest** | GET file contents (raw markdown via content negotiation); body returned | GET value by key → raw bytes | GET note (raw markdown via content negotiation) |
| **version-handle** (opaque) | the file's blob SHA | none → handle ignored | none → handle ignored |
| **write** | PUT contents with current SHA; stale SHA → conflict surfaced | PUT value (last-write-wins) | PATCH note (last-write-wins) |
| **list** (prefix `<repo-id>/<date-slug>/`) | list dir / tree by path prefix (native) | list keys by prefix (native) | list notes + filter by title/tag convention (adapter-maintained, no native prefix) |
| **address mapping** | path = `<repo-id>/<date-slug>/<artifact-name>` (native, 1:1) | key = the address string (native, 1:1) | note title/tag encodes the address; adapter keeps the address↔note-id map (impedance absorbed by adapter, **shape unchanged**) |
| **raw-markdown** | adapter unwraps base64/raw → identical markdown | raw bytes → identical markdown | raw markdown body → identical |
| **private (D6)** | private repo, token-gated | account/token-gated, encrypted at rest | note permission = owner-only, token-gated |
| `conflict-surfacing` | **yes** | no → best-effort | no → best-effort |
| `bulk-migration` | trivial (single push) | scriptable (per-key PUT) | scriptable (per-note create) |

The record shape is identical in all three columns; every store-specific detail (blob SHA, key string, note-id mapping, base64 unwrapping) is confined to the adapter and to the opaque `version-handle` — **none of it appears in the record**. Where a store lacks a contract feature (KV/HackMD optimistic concurrency; HackMD native hierarchy), the gap is absorbed by a capability flag (§6.5) or by adapter-side encoding, never by mutating the shape.

## 13. Chosen execution target

The implementation pass targets a **single dedicated private GitHub repository** (e.g. `strategic-artifacts`) as the one shared store for every repo the skill runs in — each repo's records under its `<repo-id>/` path. This is decision-complete for an implementer:

- **Store-target coordinates (in each repo's locator):** the artifacts repo `owner/repo`, plus the **branch the records live on** — a single fixed branch (the artifacts repo's default branch). The record path within it is `<repo-id>/<date-slug>/<artifact-name>`.
- **`repo-id` → concrete resolution:** the consuming repo's locator carries its `repo-id` (its path segment in the artifacts repo). No global registry is needed — the locator is the resolution.
- **Auth:** as defined in §10 — an out-of-band token from the agent/host environment; never in the locator or any record. (Referenced, not restated, to keep one source of truth.)
- **Access surface — documented swappable capability:** two ways to reach the store — the official GitHub MCP repos-toolset (~10k-token schema, richer ops) or the zero-schema `gh` CLI (cheaper, sufficient for read/write/list). **Default: `gh` CLI** (lowest token cost; the success-signal "zero token cost to skill-less agents" holds because nothing is loaded unless the skill opts in); the MCP is an optional swap when richer ops are wanted. This is an execution-target capability, not part of the record shape.
- **Always-latest:** a `read-latest` returns the latest committed record; the adapter requests raw content and bypasses any CDN/propagation-cached read so the body is current.
- **Conflict-surfacing:** `yes` (blob-SHA optimistic concurrency). **Bulk-migration:** `trivial`, but **forward-only / optional** per locked decision 6 — existing artifacts are not migrated; only new features externalize. The capability exists if the maintainer later chooses to run it.

## 14. Risks & unknowns

- **Offline access.** The store is server-authoritative, so **records are unavailable offline** (no network ⇒ no read/write). The spec acknowledges this explicitly rather than implying local availability; the read-through cache (§8) may still show the last-hydrated copy to a human, but the skill's authoritative reads require connectivity.
- **Over-abstraction.** Fitting one contract to diverse stores risks a lowest-common-denominator shape. Mitigated: capability flags (§6.5) absorb differences and the neutrality proof (§12) holds the record shape constant as the guard.
- **Backend leakage.** Risk that a store-specific detail creeps into the record shape. Guard: the independent whole-document audit (this deliverable's validation) hunts §5/§6 for leakage.
- **Locator drift across worktrees/branches.** The locator is committed, so branches can diverge — but it carries near-static config (`repo-id` + coordinates) and the live catalog comes from the store, so divergence is low-stakes and never authoritative over content.
- **Self-reference.** This spec and its sibling records are, for now, written in-repo under the pre-externalization scheme; the spec describes a future the skill does not yet follow. Expected, not a defect this pass.

## 15. Revision log

- v0.1 · 2026-06-02 · initial spec — §5 record model + §6 adapter contract (DP1); §7 lifecycle + §8 read-through cache + §9 revision contract (DP2); §10 confidentiality + §11 locator (DP3); §12 backend-neutrality proof + §13 chosen target + §14 risks (DP4). Implements product-brief_externalized-artifacts.md (D1–D7); D2 conflict handling is best-effort per brief v0.4.
