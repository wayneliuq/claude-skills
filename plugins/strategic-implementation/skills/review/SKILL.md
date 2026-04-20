---
name: review
description: Tiered review orchestrator. Runs pre-filter + generalist + simplify in parallel on the execution plan, then invokes specialists only on dimensions flagged by the generalist or matched by the pre-filter. Returns a consolidated patch list, block status, and alternative-path candidate.
---

# review

You orchestrate the tiered review of an execution plan. The goal is ≥70% token reduction vs. v1's always-parallel 10-agent panel, while preserving coverage on the dimensions that actually need it.

You are invoked by `execution-plan` (and may be invoked directly by `post-execution` or other callers in the future).

You receive:
- The full execution plan text
- The brief path (for cross-reference by `alignment` and `tests`)
- Document reference locations (architecture, UX/PMF, security, schema) — pass through to specialists as applicable
- Filtered project-learnings block (optional)
- Autonomy level

---

## Step 1 — Pre-filter (domain triggers)

Scan the plan for trigger tokens. Determine which specialists are candidates:

| Specialist | Trigger tokens (case-insensitive, any match) |
|---|---|
| `boundaries` | auth, permission, role, endpoint, route, schema, migration, column, index, secret, credential, token, api, webhook, pii |
| `runtime-risk` | cache, queue, batch, retry, cron, worker, hot path, throughput, latency, stream, poll, install, dependency, package, license |
| `tests` | (always a candidate — validation method adequacy is reviewed every run) |
| `frontend-engineer` | component, page, route (if frontend framework present), modal, form, button, screen, view, css, style |

Record the candidate set. Specialists not in the candidate set will not run unless `alignment` adds them.

---

## Step 2 — Generalist tier (parallel)

Launch in parallel:
- `strategic-implementation:alignment`
- `strategic-implementation:simplify`

Pass each:
- The plan
- The brief path (alignment only)
- Filtered learnings block (if any, tagged for the respective agent)
- `max_tokens: 1500` hint in prompt ("Cap output at ~1500 tokens.")

Wait for both.

---

## Step 3 — Resolve specialists to launch

Union of:
- Pre-filter candidate set (from Step 1)
- `alignment`'s `specialists_needed` array

`tests` is always included.
`frontend-engineer` is included only if the pre-filter matched OR `alignment` flagged UI/UX.

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
4. **Block propagation.** Any specialist `BLOCK` propagates to the overall status. `alignment` BLOCK also propagates.
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

If the caller applies patches and asks for re-review: only re-run specialists whose dimension was patched. Generalist tier re-runs only if ≥2 specialists were re-run or a hard decision was touched.
