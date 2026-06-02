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

_Additional sections (lifecycle, read-through cache, revision contract, confidentiality, locator, backend-neutrality proof, chosen target, risks, revision log) are appended by subsequent deliverables._
