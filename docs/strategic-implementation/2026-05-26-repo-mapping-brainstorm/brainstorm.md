# Brainstorm: repo-mapping for strategic-implementation

_Date: 2026-05-26 · Status: brainstorm, not approved · Resume on next machine_

## Context

Three skills currently depend on `mcp__code-review-graph__`:

- [clarify/SKILL.md:50](../../plugins/strategic-implementation/skills/clarify/SKILL.md) — graph-first grounding
- [execution-plan/SKILL.md:31](../../plugins/strategic-implementation/skills/execution-plan/SKILL.md) — graph health pre-flight + `semantic_search_nodes` / `query_graph` / `get_architecture_overview` / `get_impact_radius`
- [simplify/SKILL.md:31](../../plugins/strategic-implementation/skills/simplify/SKILL.md) — `find_large_functions_tool`, `refactor_tool`, `query_graph callers_of`

All three have a stale-graph fallback (`FLAG: graph stale … file-read mode`), so the skills don't break when the graph is empty — they just lose the token-efficient path.

## Problem

The build itself is not broken. The issue is **we never trigger rebuilds**. The skills check freshness via `list_graph_stats_tool` but never call `build_or_update_graph_tool`. If edits land (from Claude or from outside), the next skill invocation silently downgrades to file-read mode.

Current user settings.json has only an RTK PreToolUse hook — no rebuild hook anywhere.

## Comparison: code-review-graph vs codegraph

| Axis | code-review-graph (tirth8205) | codegraph (colbymchenry) |
|---|---|---|
| Install | `pip install` (Python 3.10+) | npm / curl one-liner |
| Index | Tree-sitter + SQLite + optional embeddings | Tree-sitter + SQLite + FTS5 only |
| Auto-rebuild | manual | OS file-watcher, 2s debounce |
| Tools | 30 | 10 |
| Languages | ~35 | ~24 |
| Semantic search | yes (embeddings) | no (FTS5 keyword + structural) |
| Windows pain | documented (fastmcp, cmd /c, PYTHONUTF8) | low |
| Benchmark | 38–528× token reduction (own methodology) | 35% cheaper / 57% fewer tokens / 71% fewer tool calls across 7 named OSS repos |

**Trade decision:** stay on code-review-graph. `semantic_search_nodes` is actively used in simplify for reuse-miss detection ([simplify/SKILL.md:46](../../plugins/strategic-implementation/skills/simplify/SKILL.md)). codegraph would force a rewrite of three SKILL.md files and downgrade that capability to keyword search.

**Worth testing as a drop-in:** [n24q02m/better-code-review-graph](https://github.com/n24q02m/better-code-review-graph) — same MCP tool names, advertised bug fixes + configurable embeddings + CI/CD.

## Forking question — decided no

Not worth forking ourselves. Maintenance is MCP protocol churn, fastmcp version compat, embeddings backends, Windows quirks, dependency CVEs, regression testing across 35 languages. Claude can write patches; can't be the on-call. TS/Python already supported. better-code-review-graph already does the fork we'd write.

Rule: fork when two upstream PRs get ignored, not before.

## Fix 1 — Auto-rebuild hooks

Three places a rebuild can fire automatically:

| Trigger | Mechanism | Catches | Cost |
|---|---|---|---|
| Claude edits a file | Claude Code `PostToolUse` on `Edit\|Write\|MultiEdit` | only Claude's edits | ~2s per edit (or 0 if backgrounded) |
| Claude finishes a turn | Claude Code `Stop` hook | all of this turn's edits, batched | one ~2s rebuild per turn |
| External edits (manual, git pull) | git `post-merge` + `post-commit` | external changes | one rebuild per git op |

**Recommendation:** `Stop` hook + git `post-merge`. Stop hook fires once per assistant turn, rebuild runs in background while reading response → graph fresh by next skill invocation. Git hook covers `git pull` and manual edits.

Sketch (verify CLI invocation first — may be `build`, `index`, or `update`; check `code-review-graph --help`):

```json
"Stop": [
  {
    "hooks": [
      { "type": "command",
        "command": "code-review-graph build --incremental >NUL 2>&1" }
    ]
  }
]
```

And `.git/hooks/post-merge` + `post-commit` calling the same.

Verify before wiring:
1. Exact rebuild CLI subcommand.
2. **Scope:** put in per-project `.claude/settings.json`, not user-global — only repos with `.code-review-graph/` should rebuild. A no-op-when-no-graph is fine but noisy.

## Fix 2 — Brief-biased repomap (the real upgrade)

Aider-style repomap injection at phase start gives the model global structure in one shot instead of N grep calls. The brief is a free, high-signal seed set — bias the map toward identifiers/paths the brief names.

**Substrate: code-review-graph already covers ~80% of what's needed.**

| Repomap step | code-review-graph tool |
|---|---|
| Seed from brief keywords | `semantic_search_nodes` (embeddings hit on deliverable text) |
| Expand to neighborhood | `query_graph` callers_of / callees_of / imports |
| Signatures + path:line for rendering | node metadata from `query_graph` |
| Global importance ranking | `get_hub_nodes_tool` (centrality computed) |
| Module-level shape | `get_architecture_overview` |
| Blast-radius for changed files | `get_impact_radius` |

**Gap: personalized PageRank.** Aider reruns centrality weighted by the seed set so symbols near the brief get boosted. code-review-graph's hub scores are global. Two ways to close:

1. **Approximate** — global centrality × distance-from-seed decay. No graph export needed.
2. **Exact** — export subgraph via `query_graph`, run personalized PageRank locally with networkx (~30 lines). Only if (1) produces bad maps.

**Renderer shape:**

```
plugins/strategic-implementation/scripts/repomap.py
  - input: brief path + token budget
  - calls code-review-graph MCP tools (or SQLite directly for speed)
  - extracts identifiers/paths from brief
  - semantic_search_nodes → seed nodes
  - query_graph 1–2 hops out → subgraph
  - rerank by hub score × seed-distance decay
  - render top-N signatures within token budget
  - emit markdown block; SKILL injects into clarify/execution-plan prompts
```

**Layered budgets per phase:**
- clarify — structure-only (~1K tokens)
- execution-plan — structure + 1-hop around predicted-changed files (~3K)
- review — deliverable-scoped subgraph cached from execution-plan (no recompute)

Cached per-brief slice as JSON sidecar next to the brief = review and executing-plans read the sidecar, no re-querying the live graph.

## Sequencing

1. **First**: fix the rebuild trigger (Stop hook + git post-merge). Stale graph poisons every map; no point building the renderer on top of stale data.
2. **Then**: prototype `repomap.py` with approach-1 ranking (global centrality × seed decay). Inject into execution-plan only, measure token delta on one real brief.
3. **If signal looks good**: add to clarify and review, build the per-brief sidecar cache.
4. **If approach-1 ranking is bad**: upgrade to personalized PageRank (networkx, ~30 lines).

## Open questions to resolve on next machine

- Exact `code-review-graph` rebuild CLI invocation (`build`, `index`, `update`, `--incremental`?).
- Whether better-code-review-graph is worth swapping to (test as drop-in — same MCP tool names).
- Confirm `semantic_search_nodes` quality on brief-extracted keywords vs hand-picked seeds before committing to the embeddings-dependent path.

## References

- [tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph)
- [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)
- [n24q02m/better-code-review-graph](https://github.com/n24q02m/better-code-review-graph)
- [Aider repomap docs](https://aider.chat/docs/repomap.html)
- [Aider repomap source (PageRank impl)](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)
- [SCIP / Sourcegraph code-graph protocol](https://github.com/sourcegraph/scip)
