# first-principles

Three skills, kept small on purpose: capable models need goals and the few processes
they would not run unaided, not checklists.

| Skill | What it is |
|---|---|
| [`principles`](skills/principles/) | Seven goal-oriented principles for building, debugging, fixing and shipping. Loaded into **every session** by a `SessionStart` hook ([`hooks/hooks.json`](hooks/hooks.json)); not model-invoked. |
| [`pr-review`](skills/pr-review/) | Adversarial find-and-fix review of a PR, in that PR's branch. Never marks a draft ready. Carries the bug and bloat catalogs in [`references/`](skills/pr-review/references/). |
| [`adversarial-delegation`](skills/adversarial-delegation/) | Hand implementation to a Claude worker and review it rather than trust it; optional grok second look. |

## Worker definitions

[`agents/`](agents/) holds the four implementation workers that
`adversarial-delegation`'s triage dispatches to — Sonnet 5.5 and Opus 5.5, each at
medium and high effort. They exist because an Agent-tool call can pick a model but
not an effort level, and because the `sonnet`/`opus` aliases resolve differently per
provider, so the definitions pin full model ids. **The four share one system prompt
body; change all four together.**

## v2.0.0

v2 removed the seven gates (`scope-`, `build-`, `cut-`, `done-`, `bug-`, `ship-`,
`watch-gate`) and the `agent-roi.py` telemetry script. On current models they cost
more process than they returned; what still earned its keep was folded into
`principles`. They remain in git history at v1.4.1.

Codex installs the skills but not the `SessionStart` hook.
