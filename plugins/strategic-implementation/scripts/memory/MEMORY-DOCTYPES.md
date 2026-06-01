# Memory index — what counts as memory (and what doesn't)

The recall index is **typed and selective**, never a folder-glob. This is the
human-readable manifest of the include/exclude policy enforced in `ingest.py`.
Keeping noise and abandoned attempts out is what makes recall trustworthy —
it is the difference between "surface proven precedent" and "dump old files."

## Indexed (episodic memory — searchable, never auto-promoted to curated learnings)

| Source | Record type | Why |
|---|---|---|
| `validation-log.md` → `## APPROACH — D<n>` | `approach` | how we validated a similar deliverable before |
| `validation-log.md` → `## GOTCHA — D<n>` | `gotcha` | "we lost time on X; do Y first" — highest-signal for avoiding re-derivation |
| `validation-log.md` → `## DEV-NNN` | `deviation` | what deviated and how it was resolved |
| `validation-log.md` → `## SPIKE FINDING` | `spike` | exploratory findings |
| `validation-log.md` → `## D<n> — …` | `validation` | per-deliverable method + status note |
| `post-execution-report.md` (per `##` section) | `postmortem` | regressions, cross-contamination, status |
| `execution-plan.md` (status-gated: complete / complete-legacy / in-progress) | `plan` | Context + deliverable titles |
| `spec.md` | `spec` | design intent |
| `simplify-report-*.md` → `### F-NN` | `simplify` | reuse/cleanup findings |
| Gen-A `session-*-log.md` / `-plan.md` / `-postmortem.md`, `implementation-guide.md` | as above | legacy generation, mapped by the normalizer |

## Excluded (noise / transient / not episodic memory)

| Source | Why excluded |
|---|---|
| `checkpoint.md` | transient working state, not a durable lesson |
| `token-report.md` | metrics/telemetry, not a decision |
| `*.html` mockups (incl. duplicated `spec/mockups/` copies) | UI prototypes; duplicates also collapsed by content-hash dedupe |
| `product-brief_*.md` | PM-facing intent; design rationale lives in `spec`/`plan` records |
| `brief-meta.yaml` | internal review-routing metadata |
| `*.svg`, `*.css`, `*.json`, `*.txt` | assets / artifacts |
| `project-learnings.md` | the **human-curated** tier — never ingested, never auto-written |
| `documentation-registry.md` | an index, not episodic memory |

## Status semantics (generation-aware)

- `complete` — folder has a PASS `post-execution-report.md`.
- `complete-legacy` — Gen-A folder (session logs / implementation-guide) that predates the post-execution-report artifact. **Searchable, not demoted.**
- `superseded` — a later folder's frontmatter declares `supersedes: <this-slug>`.
- `aborted` — explicit abort marker (frontmatter `status: aborted`, or a "not approved" brainstorm), or a stub with no completion signal (≤2 files, last-resort heuristic).
- `in-progress` — has work, no completion signal yet.

`aborted` and `superseded` records are **never surfaced as proven precedent** by recall (they may appear clearly marked, never recommended).
