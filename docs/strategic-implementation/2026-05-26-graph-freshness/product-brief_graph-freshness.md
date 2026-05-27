# Product Brief: Harden code-review-graph freshness

_Slug: graph-freshness · Date: 2026-05-26 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> The code-review-graph now stays fresh on its own. When you start a session, pull a batch of commits, switch branches, or edit files through any tool, the graph reparses the affected work automatically — so the strategic-implementation skills keep using the fast, structural graph path instead of silently falling back to slow, token-expensive whole-file reading. The freshness guarantee holds across every repo on the machine, not just the one you set it up in. You no longer have to remember to rebuild the graph by hand.

## 2. What the user does / sees

**Who is the user of this feature:** The single developer operating this dev machine (the repo owner), working through Claude Code. The interaction surface is Claude Code sessions and the local `code-review-graph` command line. There is no end-user audience — this is personal/local developer tooling.

### D1 — Starting a Claude Code session leaves the graph fully current, no matter how earlier changes arrived
**How a user verifies:**
1. In a repo, introduce a batch of changes that did not come from this machine's Claude edits — e.g. pull several commits, switch to a branch with different files, or rebase.
2. Start a fresh Claude Code session in that repo.
3. Check the graph's reported state and confirm it reflects the current files and the current commit — not an earlier snapshot.

### D2 — Edits made through every editing tool trigger a refresh, not just some of them
**How a user verifies:**
1. Have Claude change a tracked code file using each of the different ways it can edit files.
2. After each, check the graph's reported state.
3. Confirm the change is reflected regardless of which editing path produced it.

### D3 — The automatic-freshness behavior applies to every repo on the machine, including ones set up later
**How a user verifies:**
1. Pick a different repo than the one where this was set up (or create a new clone).
2. Pull a multi-commit batch of changes into it.
3. Confirm the graph for that repo refreshes automatically from the pull — without manually copying any setup into the repo first.

### D4 — The graph reflects the documentation content of a repo, not only its code files
**How a user verifies:**
1. In a documentation-heavy repo, ask the graph for its coverage (file count / languages).
2. Confirm prose/documentation files are represented, not only scripts and code.
3. (If the tool cannot represent documentation files at all, this deliverable is reported as not-feasible with the reason — see §6.)

## 3. Success signal

In any repo on the machine, immediately after a multi-commit pull or at the start of a session, the graph's self-reported "built at" commit matches the repo's current commit and its file/node counts reflect the current working tree — confirming the skills will take the fast graph path rather than degrading to whole-file reading.

## 4. Boundaries

**In scope:**
- Automatic graph refresh on session start, on edits through any Claude editing tool, and on incoming multi-commit changes (pull / rebase / branch switch).
- Machine-wide coverage so the behavior reaches all current and future repos.
- A feasibility-gated attempt to make the graph cover documentation files.
- Preserving any per-repo automation that already exists when machine-wide hooking is introduced.

**Out of scope:**
- Any remote/CI graph build — this is local-machine only.
- Redesigning or replacing the graph tool itself, or switching to an alternative tool.
- The brief-biased "repomap" renderer explored in the background brainstorm (separate, later effort).

**Anti-goals (philosophy-level — we deliberately will not):**
- Add a fix for a failure mode that diagnosis already ruled out (rebuild speed, concurrent-write contention) — no speculative robustness we have no evidence we need.
- Make freshness depend on the developer remembering to run anything by hand.
- Let machine-wide setup silently disable automation a repo already had.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Session-start refresh strength | Full reparse at session start (catches drift regardless of how it arrived), replacing the prior status-only check | `[HARD DECISION]` |
| Editing-tool coverage | Refresh must fire for every Claude editing tool, not a subset | `[HARD DECISION]` |
| Reach across repos | Machine-wide so all current/future repos are covered automatically | `[HARD DECISION]` |
| Documentation-file coverage | Attempt only if a clean configuration path exists; otherwise report not-feasible | `settled` |
| Scope of changes | Local developer machine only; no remote/CI | `settled` |

### HARD DECISION — Session-start refresh strength
| Option | Pro | Con |
|---|---|---|
| Full reparse at session start (chosen) | Catches all accumulated drift regardless of arrival path; deterministic clean baseline each session | Small one-time cost at session start |
| Keep status-only check | No cost | Does not fix staleness — the core problem |

### HARD DECISION — Editing-tool coverage
| Option | Pro | Con |
|---|---|---|
| All editing tools (chosen) | No silent gap depending on which tool was used | Slightly more refresh triggers |
| Current subset | Fewer triggers | Edits via uncovered tools silently leave graph stale — the observed bug |

### HARD DECISION — Reach across repos
| Option | Pro | Con |
|---|---|---|
| Machine-wide (chosen) | Freshness guarantee holds everywhere, including the repo where staleness was first noticed | Must preserve any pre-existing per-repo automation when introduced |
| Per-repo setup | Localized | Must be remembered for every repo; the failure that motivated this |

## 6. Risks & unknowns

- **Documentation-file coverage may not be feasible.** The graph tool may have no supported configuration to index prose files. If so, D4 is reported as not-feasible with the reason; it does not block D1–D3. Owner: execution-plan investigation.
- **Machine-wide hooking can override existing per-repo automation.** Introducing a machine-wide hook mechanism can supersede automation a repo already had locally (notably the post-merge refresh already placed in this repo). The plan must migrate/preserve existing hooks so nothing regresses. Owner: execution-plan.
- **Global hook scope is broad by nature.** A machine-wide refresh trigger fires in repos that have no graph; behavior there must be a harmless no-op, not an error or noise. Owner: execution-plan.
- **Settings file is shared infrastructure.** The session/edit refresh settings live in a file that also carries unrelated automation; edits must not disturb the rest.

## 7. References & revision log

**Document references:**
- Architecture: none (background brainstorm: `docs/strategic-implementation/2026-05-26-repo-mapping-brainstorm/brainstorm.md`)
- UX/PMF: n/a — developer tooling, no end-user surface
- Security policy: none
- Schema/ERD: n/a — no application data storage (graph is a local derived cache)

**Affected configuration/automation (internal plumbing — for execution-plan):**
- User-global Claude Code settings (`~/.claude/settings.json`): SessionStart and PostToolUse hooks.
- Git hook mechanism (per-repo `.git/hooks/` today; candidate global template directory).
- `code-review-graph` indexing configuration (for D4 feasibility).

**Revision log:**
- v0.1 · 2026-05-26 · initial draft
- v0.2 · 2026-05-26 · leakage-gate self-revision: generalized D2 wording away from specific editor-tool names
