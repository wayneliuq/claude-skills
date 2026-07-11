# strategic-implementation — efficiency & quality action plan

_Durable record of the F1–F13 optimization program derived from the wayneliuq-axiph
artifact corpus (64 features) + session-transcript telemetry. Kept in-repo so it
survives context loss. Last updated: 2026-07-10._

## How this was measured

Two data sources:
1. **Artifact corpus** — `wayneliuq/strategic-artifacts/wayneliuq-axiph` (briefs,
   plans, validation-logs, simplify-reports, token-reports across 64 features).
2. **Session transcripts** — `~/.claude/projects/*axiph*/*.jsonl`. Every assistant
   message carries real `usage` (input/output/cache tokens) + model id; every
   `Task`/`Agent` tool_result embeds `<usage>subagent_tokens … duration_ms …</usage>`.
   This is exact cost data, not the byte-proxy the old `token-report.sh` inferred.

The reviewer-ROI figures below come from `scripts/reviewer-roi.py` (deterministic
cost + a haiku value-classification pass) over 89 reviewer invocations in 18 review
rounds.

## Reviewer ROI — real cost vs. real output

Tokens/novel = real tokens spent per unique (non-overlapping) finding. Value column
is haiku-judged high/moderate/low-or-noop.

| Reviewer | Inv | Avg tok | Novel | Overlap% | No-op% | Tok/novel | Value H/M/L |
|---|--:|--:|--:|--:|--:|--:|:--|
| user-validation | 14 | 64.2k | 18 | 18% | 14% | **49.9k (worst)** | 1/7/6 |
| plan-simplify | 11 | 62.2k | 20 | 26% | 9% | 34.2k | 3/3/5 |
| alignment | 15 | 74.5k | 39 | 13% | 0% | 28.7k | 11/2/2 |
| frontend-engineer | 15 | 85.9k | 56 | 15% | 0% | 23.0k | 13/1/1 |
| technical-expert | 6 | 77.7k | 21 | 28% | 0% | 22.2k | 5/1/0 |
| boundaries | 4 | 67.6k | 14 | 7% | 0% | 19.3k | 3/1/0 |
| runtime-risk | 8 | 64.9k | 28 | 10% | 0% | 18.5k | 6/2/0 |
| tests | 14 | 48.7k | 45 | 22% | 0% | **15.2k (best)** | 7/7/0 |
| plan-gate | 2 | 24.8k | 0 | — | — | n/a (gate) | 0/2/0 |

**Data-backed conclusions**
- `user-validation` is the clear underperformer (worst tok/novel, highest no-op) →
  validated F2 (conditional skip, shipped 4.7.0).
- `plan-simplify` is second-worst + highest generalist overlap (26%) → extend F2 to
  gate it on small plans (4.8.0).
- `technical-expert` has the highest overlap (28%) → F9 (tighten gating to its real
  domain) (4.8.0).
- `frontend-engineer` is the most expensive but **highest value** (13/15 high) — do
  NOT cut. Cost is input-dominated (files/mockups it reads), not waste. This refutes
  the earlier byte-proxy inference.
- `tests` is the efficiency champion on both axes — keep always-on.

_Caveats: small n for plan-gate/boundaries/technical-expert (directional only);
value judged by a single haiku pass (no adversarial verify); tok/novel penalizes
role-agents that aren't finding-generators; cost is input-dominated so F1 cuts all
rows roughly proportionally._

## Fix ledger (F1–F13)

| # | Fix | Status | Shipped |
|---|---|---|---|
| F1 | Reviewers → Sonnet 5 / `effort: low` (effort is the real lever) | ✅ done | 4.7.0 |
| F2 | Conditional generalists — skip `user-validation` on no user-observable surface | ✅ done | 4.7.0 |
| F2+ | Extend F2 — skip `plan-simplify` on trivial/single-deliverable plans | ✅ done | 4.8.0 |
| F3 | Inline `plan-gate` | ⏭️ declined — superseded by F1 (spawn now cheap; inlining moves cost into the Opus orchestrator) |
| F4 | Graph-first exploration enforced in plan/execute skills + checkpoint record | 🟡 partial — clarify graph-refresh shipped 4.7.0; enforcement half open |
| F5 | Fix preview/rAF validation surface (hit 23 features) | ❌ open — needs design pass |
| F6 | Per-deliverable preview-unavailability escalation (no silent full-suite defer) | ❌ open |
| F7 | Graph-based mandatory consumer audit in `alignment` | ❌ open |
| F8 | Brief-mechanism conformance check (prevents full re-plans) | ❌ open |
| F9 | Tighten `boundaries`/`technical-expert` triggers to real domain | ✅ done | 4.8.0 |
| F10 | Simplify-disposition counter | 🟡 partial — grep fixed 4.7.0; marker-emission half open |
| F11 | Per-phase token/time accounting | 🟢 tooling built — `scripts/reviewer-roi.py` (transcript-based); phase bucketing via `Skill` delimiters |
| F12 | Reliable token-report capture (transcript-dir/jq robustness) | ❌ open |
| F13 | Pre-flight environment probe (~45 retry/blocker stalls) | ❌ open |

## Suggested sequencing for the remainder

1. **F10 marker-emission + F12** — finish telemetry reliability (cheap).
2. **F4 enforcement + F7** — graph-first consumer audit (the biggest escaped-defect class).
3. **F8** — brief-mechanism conformance (prevents the most expensive failure: full re-plan).
4. **F5 / F6** — preview/rAF harness (largest wall-clock sink; needs a design pass).
5. **F13** — pre-flight probe.

## Reproducing the telemetry

```
python3 plugins/strategic-implementation/scripts/reviewer-roi.py extract   # deterministic cost + round slices
# then run the haiku value pass (see script header), writing verdicts/*.json
python3 plugins/strategic-implementation/scripts/reviewer-roi.py roi        # join → ROI table
```
