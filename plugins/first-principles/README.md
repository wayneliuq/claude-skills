# first-principles

Three skills, kept small on purpose: capable models need goals and the few processes
they would not run unaided, not checklists.

| Skill | What it is |
|---|---|
| [`principles`](skills/principles/) | Seven goal-oriented principles for building, debugging, fixing and shipping. Loaded into **every session** by a `SessionStart` hook ([`hooks/hooks.json`](hooks/hooks.json)); not model-invoked. |
| [`pr-review`](skills/pr-review/) | Adversarial find-and-fix review of a PR, in that PR's branch. Never marks a draft ready. Carries the bug and bloat catalogs in [`references/`](skills/pr-review/references/). |
| [`adversarial-delegation`](skills/adversarial-delegation/) | Keep Opus-level work in-session; hand scouting and narrow checkable edits to Haiku and bounded implementation to Sonnet, review rather than trust; grok second look on every consequential change. |

## Worker definitions

[`agents/`](agents/) holds the three workers that `adversarial-delegation`'s triage
dispatches to — Haiku 5.5 at medium, and Sonnet 5.5 at medium and high effort. There are
no Opus workers: Opus-level work stays in the orchestrating session. The definitions exist
because an Agent-tool call can pick a model but not an effort level, and because the
`sonnet`/`haiku` aliases resolve differently per provider, so they pin full model ids.
**The three share one system prompt body; change all three together.**

## v3.0.0

v3 removed `worker-opus` and `worker-opus-high`. Opus-priced subagents bought context
isolation at the orchestrator's own price; Haiku 5.5 buys the same for a fortieth of it.

## v2.0.0

v2 removed the seven gates (`scope-`, `build-`, `cut-`, `done-`, `bug-`, `ship-`,
`watch-gate`) and the `agent-roi.py` telemetry script. On current models they cost
more process than they returned; what still earned its keep was folded into
`principles`. They remain in git history at v1.4.1.

Codex installs the skills but not the `SessionStart` hook.
