# Post-reload verification protocol — memory-recall-layer

Skill-instruction edits (D1, D4) take effect only when the plugin is **reloaded**
in a fresh Claude Code session (L-005), so the live, in-session halves of the
brief's D2/D3 acceptance steps cannot be exercised in the building session. This
is their scheduled home. The static (grep) halves were validated at build time.

**Reviewer:** PM.
**Trigger:** the first `executing-plans` run, and the first `execution-plan` draft,
on any feature **after the plugin is reloaded** (new session) AND after the index
has been built at least once (`bash plugins/strategic-implementation/scripts/memory/recall.sh` returns or the build has run).

**Pre-step (once):** build the index for the active repo —
`python3 plugins/strategic-implementation/scripts/memory/build_index.py --root docs/strategic-implementation`.

## Checks

| # | Brief step | Observable PASS criterion |
|---|---|---|
| 1 | D2 — recall before build | In `executing-plans` Step 2a, for a class-`a|b|c`/macro deliverable in a previously-solved domain, a "Prior approaches that may apply" block appears **before** any build edit, carrying a `source_path :: anchor` pointer. |
| 2 | D2 — agent uses it, not re-derives | The deliverable's chosen approach cites the recalled snippet (by pointer or paraphrase) rather than re-deriving from scratch. Record a token-delta observation vs a recall-disabled run (feeds D5). |
| 3 | D3 — recall during plan drafting | In `execution-plan` Step 6, a relevant prior approach is surfaced for cross-domain/integration-risk work. With the vector leg enabled (Phase 1b), it surfaces even when the new plan's wording differs from the past write-up. |
| 4 | Advisory-never-blocks | With no index present (fresh repo), Step 2a / Step 6 recall produces no output and execution proceeds normally — no error, no block. |

## Notes
- Checks 1–3 are the live confirmation of the static grep checks already recorded in `validation-log.md` (D4 APPROACH block).
- Check 2's token-delta + adoption observation is the live, post-hoc half of the D5 precision gate's success signal.
- If any check fails, recall wiring can be made no-op by leaving the index unbuilt (the advisory step degrades to silence) while the issue is triaged — execution is never blocked.
