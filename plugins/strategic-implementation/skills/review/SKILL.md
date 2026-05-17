---
name: review
description: Tiered review orchestrator. Runs pre-filter + generalist + simplify in parallel on the execution plan, then invokes specialists only on dimensions flagged by the generalist or matched by the pre-filter. Returns a consolidated patch list, block status, and alternative-path candidate.
---

# review

You orchestrate the tiered review of an execution plan. The goal is ≥70% token reduction vs. v1's always-parallel 10-agent panel, while preserving coverage on the dimensions that actually need it.

You are invoked by `execution-plan` (and may be invoked directly by `post-execution` or other callers in the future).

You receive:
- The full execution plan text
- The brief path (for cross-reference by `alignment`, `user-validation`, and `tests`)
- Document reference locations (architecture, UX/PMF, security, schema) — pass through to specialists as applicable
- Filtered project-learnings block (optional)
- Autonomy level

---

## Generalist tier composition

Three generalist reviewers run in parallel on every plan. Their scopes are deliberately non-overlapping; anti-overlap rules live in each agent's prompt and are enforced by the orchestrator's dedup-with-corroboration logic in Step 5.

| Agent | Owns | Does NOT review |
|---|---|---|
| [`alignment`](../../agents/alignment.md) | Brief alignment (every deliverable in brief → in plan), consumer audit on shape change, architecture-doc conformance, future-proofing/naming/repo-coherence, specialist routing. | PMF, user walkthroughs, user-reachability — ceded to `user-validation`. Simplicity → `simplify`. Test correctness → `tests`. Specialist domains → specialists. |
| [`simplify`](../simplify/SKILL.md) | Whether a shorter path exists from the brief's success signal to the plan; returns PASS or ALTERNATIVE. | Per-file code style. Reviewer dimensions owned by other agents. |
| [`user-validation`](../../agents/user-validation.md) | Named target user, declared interaction surface, per-acceptance-step walkthrough, end-to-end reachability of the user path (including the "client-built, pipeline-missing" loophole), PMF / deliverable-recognizability. | Missing deliverables (alignment owns; flag the unreachable step as the consequence instead). Architecture, consumer audits → alignment. Validation-method honesty → `tests`. Simplicity → `simplify`. |

When two agents corroborate the same root cause (e.g. `alignment` flags "D5 absent" while `user-validation` flags "step 3 of D5 unreachable because D5 missing"), Step 5's dedup logic merges them into one entry and raises severity rather than duplicating the flag.

---

## Step 1 — Pre-filter (domain triggers)

Scan the plan for trigger tokens. Determine which specialists are candidates:

| Specialist | Trigger tokens (case-insensitive, any match) |
|---|---|
| `boundaries` | auth, permission, role, endpoint, route, schema, migration, column, index, secret, credential, token, api, webhook, pii |
| `runtime-risk` | cache, queue, batch, retry, cron, worker, hot path, throughput, latency, stream, poll, install, dependency, package, license, **any non-empty `Library lifecycle audit` section, or any deliverable with `Integration-risk class: a`** |
| `tests` | (always a candidate — validation method adequacy is reviewed every run) |
| `frontend-engineer` | component, page, route (if frontend framework present), modal, form, button, screen, view, css, style |

Additional triggers (any specialist that matches gets added to the candidate set):
- **Missing `Library lifecycle audit` when integration-risk deps were declared in clarify** → `runtime-risk`.
- **Any deliverable whose `Consumer audit` is missing, present-but-empty, or hand-wavy on a shape-changing deliverable** → `alignment`.
- **Any deliverable with `Integration-risk class: a|b|c` and `Validation: tdd`** → `tests` (honesty check is mandatory).

Record the candidate set. Specialists not in the candidate set will not run unless `alignment` adds them.

---

## Step 2 — Generalist tier (parallel)

Launch in parallel:
- `strategic-implementation:alignment`
- `strategic-implementation:simplify`
- `strategic-implementation:user-validation`

Pass each:
- The plan
- The brief path (alignment AND user-validation — user-validation needs the brief for the named user, declared interaction surface, and acceptance steps)
- Filtered learnings block (if any, tagged for the respective agent)
- `max_tokens: 1500` hint in prompt ("Cap output at ~1500 tokens.")

Wait for all three.

---

## Step 3 — Resolve specialists to launch

Union of:
- Pre-filter candidate set (from Step 1)
- `alignment`'s `specialists_needed` array
- `user-validation`'s `specialists_needed` array (e.g., user surface broken → `frontend-engineer`)

`tests` is always included.
`frontend-engineer` is included only if the pre-filter matched OR `alignment` flagged UI/UX OR `user-validation` named it.

If a specialist is in the union but there is clearly no relevant surface (e.g. `frontend-engineer` with zero UI deliverables), skip it and log the skip in the synthesis output.

---

## Step 4 — Specialist tier (parallel)

Launch the resolved specialist set in parallel. Pass each:
- The plan
- Document references relevant to the specialist (security policy → `boundaries`; schema/ERD → `boundaries`; etc.)
- Filtered learnings block tagged for that specialist
- `max_tokens: 1500` hint

Wait for all.

---

## Step 5 — Synthesize

Merge all agent outputs. Apply:

1. **Collect** every flag and recommendation.
2. **Deduplicate.** Two agents flagging the same underlying issue → keep one, note the corroboration.
3. **Reconcile conflicts.** Prefer the more conservative position. Note the conflict inline.
4. **Block propagation.** Any specialist `BLOCK` propagates to the overall status. `alignment` BLOCK propagates. `user-validation` BLOCK propagates — typically caused by an unreachable user-acceptance step (the "client-built, pipeline-missing" loophole). When `alignment` flags "D<n> absent" AND `user-validation` flags "step k of D<n> unreachable because D<n> missing", these are the same root cause — dedup into one entry with corroboration noted; severity is the max of the two.
5. **Alternative path (simplify).** If `simplify` returned `ALTERNATIVE`, carry it through as a top-level field — it requires a PM decision, not a patch.
6. **Prioritize.** Sort recommendations: high-severity first, then by deliverable id.

---

## Step 6 — Return

Return to the caller:

```json
{
  "status": "PASS | FLAG | BLOCK",
  "block_reason": "string or null",
  "alternative_path": "string or null (from simplify)",
  "patches": [
    { "severity": "low|med|high", "target": "deliverable id", "change": "...", "source_agents": ["..."] }
  ],
  "skipped_specialists": ["list with one-line reason each"],
  "ran": ["agent names that executed"]
}
```

Keep total synthesis output terse — the caller uses it, not the PM directly.

---

## Re-review

If the caller applies patches and asks for re-review: only re-run specialists whose dimension was patched. Generalist tier re-runs only if ≥2 specialists were re-run, a hard decision was touched, OR `user-validation` returned BLOCK on the previous pass (a reachability BLOCK demands a re-walk after patches).
