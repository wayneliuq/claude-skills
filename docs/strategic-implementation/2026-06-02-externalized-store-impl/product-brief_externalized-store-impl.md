# Product Brief: Externalized Artifact Store — Implementation

_Slug: externalized-store-impl · Date: 2026-06-02 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> The strategic-implementation skill now writes each feature's working documents to a shared private GitHub store under the current repo's namespace, instead of committing them into the repo. When you run the skill on a feature, the working repo gains no artifact-content files — only a single one-line pointer — and the records are mirrored into a local scratch area so you can read them in your editor without opening a web page. The store is always-latest and shared across every repo you use the skill in, so a record written from one machine or worktree is readable from another. The first time the skill runs in a repo it sets itself up automatically. Existing artifacts are left exactly where they are; only new work flows to the store.

## 2. What the user does / sees

**Who is the user of this feature:** The maintainer of the strategic-implementation skill (you), operating it through Claude Code and a terminal. Records are written and read on your behalf by the skill; you confirm behavior using the GitHub store and your shell.

### D1 — First run in a repo sets up the store automatically and leaves only a pointer
The first time the skill runs in a repo, it ensures the shared private store and this repo's namespace exist and writes one committed pointer file. The pointer holds only where-to-find-the-store coordinates and this repo's namespace — never a password or token.
**How a user verifies:**
1. In a repo that has never used the externalized store, run the skill on any feature.
2. Confirm the shared private store exists on GitHub and now contains this repo's namespace.
3. Confirm the repo has exactly one new committed pointer file and that opening it shows no secret/token — only coordinates + namespace.
4. Run the skill again in the same repo; confirm it reuses the existing pointer (no duplicate setup).

### D2 — A feature's records are written to, read back from, and listed in the store
The skill stores each artifact as its own record under `this-repo/feature/artifact`. A record written and read back is byte-identical markdown; all records for a feature can be listed.
**How a user verifies:**
1. After the skill produces a feature's records, list that feature's records directly against the GitHub store and see every expected artifact.
2. Open one record from the store and confirm it is the same markdown the skill produced (no wrapping, no corruption).
3. Confirm two records written close together by different actors do not silently clobber each other — a conflicting write is reported, not lost (where the store supports it).

### D3 — The active feature's records appear locally, always-latest, and are disposable
While you work, the active feature's records are mirrored into a local scratch area you can open in your editor, with no web portal. The mirror is never committed, can be deleted with no data loss, and reflects the latest stored content.
**How a user verifies:**
1. During a session, find the active feature's records in a local scratch location and open them in your editor.
2. Confirm that location is excluded from version control (it never shows up in `git status`).
3. Delete the local mirror, continue working, and confirm the records are still intact (re-fetched from the store) — nothing was lost.
4. From a second worktree or a fresh session, confirm the same feature's current records are available locally with no manual copy step.

### D4 — Running the skill keeps the working repo clean — records go to the store, not the repo
Once the stages are routed through the store, running the skill on a feature writes that feature's records to the store; the working repo gains only the pointer. During the transition a half-routed run never loses an artifact (it falls back to the old in-repo location rather than dropping data).
**How a user verifies:**
1. Run the skill on a feature (or the validation feature used to prove this out).
2. Confirm the feature's records now exist in the GitHub store under this repo's namespace.
3. Run `git status` in the working repo and confirm no new per-feature artifact files appear — only the pointer.
4. Confirm that the durable shared documents (project learnings, documentation registry) are untouched and still in the repo.

### D5 — Feedback is conversational; you never hand-edit an artifact to steer the skill
Revising a brief or a mockup, and dispositioning review findings, are done by telling the skill in chat — not by editing an artifact file. The skill re-emits the record from your spoken feedback.
**How a user verifies:**
1. Ask the skill to revise a brief by describing the change in chat; confirm it re-emits the updated record without you editing any file.
2. Do the same for a mockup revision and for accepting/deferring a review finding.
3. Confirm no step in the flow asks you to edit a record file to give feedback.

## 3. Success signal

After running a feature, its records are listable in the shared GitHub store under this repo's namespace, `git status` in the working repo shows no new per-feature artifact files (only the pointer), and a fresh session or worktree surfaces the active feature's records locally from the store — always-latest.

## 4. Boundaries

**In scope:**
- Standing up the shared private store + this repo's namespace + the committed pointer, created on first run.
- Store read / write / list of per-feature records with byte-identical markdown and best-effort conflict reporting.
- The local always-latest mirror (disposable, never committed).
- Routing the skill's per-feature record reads/writes through the store, validated end-to-end against the live store.
- Replacing artifact-file-editing feedback with conversational feedback.
- An in-repo fallback during the transition so no artifact is ever dropped.

**Out of scope:**
- Migrating the existing per-feature artifacts (forward-only; existing files stay put).
- Non-interactive / scheduled (headless / cron) operation — interactive Claude Code only this round.
- Moving the durable shared documents (project learnings, documentation registry) out of the repo.
- Choosing or supporting a non-GitHub store (the design proves neutrality; this build targets GitHub only).

**Anti-goals (philosophy-level — we deliberately will not):**
- Put any credential/token into the repo, the pointer, or any record.
- Let the local mirror become the source of truth.
- Make a half-finished rewiring lose or strand an artifact.
- Require a web portal for normal review.
- Commit artifact content into the working repo.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Store location | A single shared **private GitHub repository**, `wayneliuq/strategic-artifacts`, namespaced per source repo | `[HARD DECISION]` |
| Sequencing | Phased — store + pointer + mirror + first-run setup land and are validated against the live store first; stage rewiring follows | `[HARD DECISION]` |
| Transition safety | An in-repo fallback is kept during rewiring so a half-routed run never drops an artifact | `[HARD DECISION]` |
| Validation liveness | This pass performs **real** reads/writes against the live store (dogfooded), not a sandbox | `[HARD DECISION]` |
| Credential handling | Access is via your existing ambient GitHub login; no secret is ever written to the repo, pointer, or any record | `[HARD DECISION]` |
| This feature's own artifacts | Stay in the repo under the current scheme (the store isn't trusted until built) | `settled` |
| Migration | Forward-only / optional — existing artifacts are not moved | `[HARD DECISION]` |
| Design contract | Implements the approved spec at `docs/strategic-implementation/2026-06-02-externalized-artifacts/spec.md`; its locked decisions are not reopened | `[HARD DECISION]` |

## 6. Risks & unknowns

- **Live external dependency.** This pass does real GitHub I/O; network/auth/rate-limit conditions can fail a run. Owner: execution-plan library-lifecycle audit + validation must exercise the real store and handle auth-absent / offline gracefully.
- **Invasive rewiring.** Multiple live skill stages change behavior; a regression could disrupt the maintainer's own workflow. Owner: phased sequencing + in-repo fallback bound the blast radius; the rewiring stage is validated end-to-end before the fallback is removed (fallback removal is itself out of scope this pass if risk remains).
- **Secret leakage.** A credential could accidentally land in the committed pointer or a record. Owner: the no-secret-in-repo anti-goal is a review focus (boundaries); the pointer carries coordinates only.
- **Always-latest vs. store read caching.** The store may serve a slightly stale read after a write; the mirror must reflect the latest. Owner: execution-plan validation confirms a write is immediately readable as latest.
- **Bootstrap idempotency.** First-run setup must be safe to run more than once (not create duplicate namespaces/pointers). Owner: D1 acceptance step 4.

## 7. References & revision log

**Document references:**
- Architecture: `docs/strategic-implementation/2026-06-02-externalized-artifacts/spec.md` (locked design — record model §5, adapter contract §6, lifecycle §7, cache §8, revision §9, confidentiality §10, locator §11, neutrality §12, chosen target §13); plus the `plugins/strategic-implementation/skills/*/SKILL.md` set being rewired and `docs/strategic-implementation/documentation-registry.md`
- UX/PMF: n/a — user is the maintainer via Claude Code
- Security policy: inline — spec §10 confidentiality (out-of-band credential via ambient GitHub login; never in repo/pointer/record)
- Schema/ERD: n/a (external) — record shape defined by spec §5; storage is the GitHub repo

**Revision log:**
- v0.1 · 2026-06-02 · initial draft
