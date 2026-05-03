# strategic-implementation

**Outcome-first development. Ship features without becoming an engineering bottleneck.**

`strategic-implementation` is a Claude Code plugin that turns a plain-English description of what the user should be able to do into shipped, validated code. The whole workflow is **outcome-first** — every feature starts from the user-observable change and works backwards to implementation. Designed for **product managers, founders, and creators** who think in user outcomes, not implementation details.

You write what the user should be able to do. The plugin handles everything between that sentence and merged code: clarification, planning, adversarial review, deliverable-by-deliverable execution, and a regression check at the end. You approve **one document** (the product brief). Everything else happens behind the right gates, with the right level of autonomy you choose at the start.

**Version:** 3.1.0
**Built for:** Claude Code on Opus 4.7
**Audience:** non-technical PMs, solo founders, anyone who can describe what good looks like

---

## Why this plugin exists

Agentic coding tools have two failure modes:

1. **Too thin** — a single chat that runs off-script, makes silent scope changes, and ships something that "passes tests" but doesn't do what you asked.
2. **Too thick** — a 30-agent SDLC framework with hundreds of slash commands, file-based state machines, and a learning curve that defeats the point of having an agent.

`strategic-implementation` is the **lean middle**. The full plugin is ~1,500 lines of prompts and 8 small skills. There is exactly one document the PM signs off on. There is exactly one approval gate inside Claude Code's native plan mode. And there is a deliberate, measured **token-efficiency target — ≥70% review-phase reduction over our v1** — without giving up adversarial review or honest validation.

In short: **the best balance between performance and token cost.** A reviewer that is sharp where it matters, silent where it doesn't, and never asks you to read three documents when one will do.

---

## Who it's for

- **Product managers** who want their ideas built the way they described them.
- **Founders** moving fast across a small codebase who need a senior-engineer-shaped reviewer at every step without hiring one.
- **Creators** — anyone who has a clear vision of what a feature should do for a user, and wants the agent to handle the rest with discipline.

You do not need to know what TDD is. You do not need to read the execution plan unless you want to. You **do** need to write a clear product brief — and the `clarify` skill will pull the right context out of you in a single pass before that brief is drafted.

---

## How it works (the whole arc, in plain English)

The arc is **outcome-first**: clarify pulls the one-sentence user-observable outcome out of you up front, and every later phase works backwards from that to implementation.

```
You describe what you want.
        │
        ▼
[clarify]  →  one short conversation: assumptions, ≤3 questions, doc references, autonomy level.
        │      Catches solution-disguised-as-problem framing before it becomes a brief.
        ▼
[product-brief]  →  drafts the ONE document you'll approve. Working-backwards paragraph,
        │            user-observable deliverables (each with its own validation method),
        │            success signal, anti-goals, hard decisions locked.
        │
        ▼  ← you read it, comment inline with `<!-- pm: ... -->`, approve when ready
        │
[execution-plan]  →  enters Claude Code plan mode. Drafts a deliverable DAG. Each deliverable
        │            declares HOW it will be validated (preview / CLI / TDD / post-hoc).
        │            Then a panel of reviewers inspects the plan…
        │
        ├─ [alignment] + [simplify]  ← always run, in parallel (the generalist tier)
        ├─ [boundaries] / [runtime-risk] / [tests] / [frontend] / [technical-expert]
        │   ← run only when the plan touches their dimension (the specialist tier)
        │
        │   The plan gets patched, then presented in plan mode. You approve in the UI.
        ▼
[executing-plans]  →  one deliverable at a time. Pre-flight check, build, validate, atomic commit.
        │              If validation fails: a structured Failure Protocol kicks in (state the
        │              assumption, fix once, re-validate, escalate before guessing further).
        │              Every deviation is logged. Nothing gets quietly skipped.
        ▼
[post-execution]  →  regression check, cross-file impact scan, acceptance tests for any
                      criterion that didn't get a TDD test, and (v2.2) a goal-backward
                      verification that the code actually substantiates the plan's claims —
                      not just that the test suite is green.
```

That's it. There are three more skills (`triage` for bugs after-the-fact, `learnings-synthesis` for accumulating project-specific rules, `prune-tests` for GA prep), but the path above is what runs on every feature.

---

## What makes this different

### 1. One PM-facing artifact, not five

Most planning frameworks ask you to read a design doc, a plan, and four review reports. We ship **one** document for your approval — the product brief. The execution plan is reviewed by the agents and approved inside plan mode's native UI. You stay focused on what the feature should do.

### 2. Tiered review, not always-on panels

A 10-agent panel that runs on every plan is a luxury car that idles in the driveway. Our review is **tiered**:

- A **pre-filter** scans the plan for trigger tokens (auth, schema, hot-path, UI).
- The **generalist tier** (`alignment` + `simplify`) always runs in parallel.
- **Specialists** run only when their dimension is actually present.

Result: review costs scale with what the plan does, not with how many reviewer types we shipped. Token reduction vs. our v1 always-on panel: ≥70%.

### 3. Validation declared up-front, honestly

Each deliverable declares **how it will be proven correct** before any code is written:

| Method | When to use |
|---|---|
| `preview` | Visually observable in Claude Code's preview tool |
| `cli` | A command whose output proves the behavior |
| `tdd` | Acceptance test written first, then code |
| `integration-test` | Real third-party runtime / network exercised — no mocks at the seam |
| `post-hoc` | Manual PM inspection (rare) |

The `tests` reviewer flags dishonest method choices — e.g. `tdd` against a database whose lifecycle the deliverable changes is a HIGH flag, because mocking the database doesn't prove the database behaves correctly. **A green test suite is not a proxy for correctness.** The plugin is built around that principle.

### 4. Adversarial reviewers, not cooperative ones

As of v2.2, the generalist reviewers (`alignment`, `tests`) carry an explicit **adversarial stance** with named failure modes for their own reasoning ("anchoring on passing dimensions", "trusting well-written prose", "calling missing details non-blocking"). The reviewer is told **how reviewers go soft**, so it can resist its own bias toward agreement.

### 5. Goal-backward verification post-execution

Tests passing is necessary, not sufficient. After execution completes, the `post-execution` skill (v2.2) re-reads the code against the plan's claims for any deliverable whose validation was `post-hoc` or carried a mocked-seam flag. Did the named function actually appear? Is the route registered? It catches the silent gap between "code committed" and "feature shipped." Token-bounded — runs on at most 3 suspect deliverables, single-grep yes/no checks. **Skipped entirely when every deliverable had real automated proof.**

### 6. Anti-framing at the entry gate

`clarify` (v2.2) catches the most common PM failure mode: smuggling implementation into a request ("add tabs to the login page"). It surfaces one alternative framing — *what is the user actually trying to do?* — so the brief is built around the user need, not the proposed solution. One paragraph, no nagging.

### 7. You pick the autonomy level

| Level | Behavior |
|---|---|
| `supervised` | Pause at every gate. Maximum control. |
| `auto` (default) | Pause only on flagged items, blocks, and PM-approval gates. |
| `yolo` | Pause only on hard blocks. Preview-unavailable auto-escalates to TDD. |

Set once at clarify time. Carried through the whole workflow.

---

## Skills (9) and agents (7)

**Skills:**

| Skill | Role |
|---|---|
| `strategic-implementation` | Orchestrator. Routes clarify → brief → execution-plan. |
| `clarify` | One-pass entry gate. Anti-framing check, doc refs, autonomy. |
| `product-brief-drafter` | Single PM-approvable artifact. Draft & revise modes. |
| `ui-mockup` | (v3.0) Optional static-HTML mockup between brief and plan. `generate` / `revise` / `conflict-back-to-brief`. |
| `execution-plan` | Plan-mode native. Drafts deliverable DAG, runs review, exits on approval. Loads doc registry; tags `may-invalidate` (v3.0). |
| `review` | Pre-filter + generalist + specialist tiering. |
| `executing-plans` | Deliverable-gated execution with declared validation per deliverable. Bundles registry-tracked doc updates into the atomic commit (v3.0). |
| `post-execution` | `regression-check`, `triage`, `learnings-synthesis`. Goal-backward verification (v2.2). Registry-update verification + visual-contract diff (v3.0). |
| `prune-tests` | GA-state-gated. Removes pre-GA line-level unit tests. |

**Agents:**

- **Generalist (always run):** `alignment`, `simplify`
- **Specialists (run on flag):** `boundaries` (security + data + API), `runtime-risk` (performance + dependencies), `tests` (validation honesty), `frontend-engineer` (UI/UX/a11y), `technical-expert` (stack pitfalls + step ordering)

All agents return JSON, cap at ~1500 tokens, and stay under ~120 lines of prompt.

---

## Artifacts produced

Per feature, under `docs/strategic-implementation/<YYYY-MM-DD>-<slug>/`:

- `product-brief_<slug>.md` — the one document you approve
- `execution-plan.md` — agent-reviewed, approved in plan mode
- `validation-log.md` — append-only deviation log
- `post-execution-report.md` — regression + goal-backward verification

Plus a shared `docs/strategic-implementation/project-learnings.md` that accumulates rules synthesized from each feature's deviations.

---

## Token efficiency, by design

v2 vs. v1 → ≥70% review-phase reduction via:

- Single PM artifact replacing v1's spec + sessionized-guide + per-session-plans
- Plan-mode native approval instead of hand-authored drafter prompts
- Tiered review (generalist → specialists on flag) instead of always-parallel 10-agent panel
- Panel consolidation: 10 always-on → 4 always-eligible + contextual
- JSON output contracts with `max_tokens: 1500` hints instead of freeform prose
- Merged post-execution skills replacing v1's bug-fix + post-mortem + end-of-implementation
- Dropped sessionization, LOC gates, revision logs, per-step commits, double agent panels

v2.2 adds (~24 lines added across 4 files; total still ~1,525 lines):

- Adversarial stance prompts on `alignment` and `tests`
- Anti-framing posture in `clarify`
- Scoped goal-backward verification in `post-execution` regression-check (zero added cost on TDD-heavy features; ~3–12K tokens worst case)

v3.0 adds (outcome-first restructure + new optional phase + persistent doc index):

- Brief restructured along the working-backwards spine: a release-note paragraph leads every brief; `Acceptance criteria` section dropped (each deliverable's validation method is its acceptance test); new `Success signal` section names the outside-observable outcome; `Anti-goals` separated from out-of-scope as philosophy-level statements.
- `clarify` primes the new sections with three small additions: a working-backwards prompt (one-sentence outcome), a success-signal prompt, and an outcome playback in Step 4 ("to confirm — when X happens for user Y…"). Inability to answer captured as `TBD — open question` and propagated verbatim — never blocks.
- New `ui-mockup` skill + Step 3.5 in the orchestrator: optional static-HTML mockup between brief approval and execution-plan drafting, gated by an explicit pre-flight scope estimate. Reuses repo design tokens (CSS vars → Tailwind config → theme file → neutral fallback). Mockup-vs-brief conflicts route back to brief revision, never silently override.
- Per-repo documentation registry at `docs/strategic-implementation/documentation-registry.md`. Populated at clarify time when a doc is first named (with `Covers` and `Update Trigger` captured then), read by execution-plan to tag deliverables with `may-invalidate`, bundled into the deliverable's atomic commit by executing-plans, verified by post-execution.
- Defense-in-depth plan-mode exit checks across all file-writing sub-skills + orchestrator constraint.

The principle: **add the agent-side defenses that catch the most common silent-failure modes; spend tokens only where automated proof is weakest.**

---

## Acknowledgments — inspirations for v2.2

The v2.2 changes (adversarial stance, goal-backward verification, anti-framing in clarify) are inspired by close study of two excellent open-source agentic-coding plugins:

- **[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)** — a maximalist spec-driven SDLC framework with deeply considered adversarial-stance prompting for its `gsd-plan-checker` and `gsd-verifier` agents. The "named failure modes for the reviewer's own reasoning" pattern in our `alignment` agent, and the "do not trust the executor's narrative; re-read the code" methodology behind our `post-execution` goal-backward verification, both originate there.
- **[garrytan/gstack](https://github.com/garrytan/gstack)** — a virtual-engineering-team-in-a-box with a strong anti-sycophancy doctrine in its `office-hours` skill. The anti-framing posture in our `clarify` skill — surfacing solution-disguised-as-problem requests before a brief is drafted — is a direct adaptation.

Both plugins are broader in scope than `strategic-implementation`. Our deliberate choice has been to keep this plugin **lean** — eight small skills, one PM artifact, native plan-mode integration — and to borrow only the specific high-leverage ideas that close real gaps in our own workflow without bloating it. We thank both projects for their public, well-documented work.

---

## Acknowledgments — inspirations for v3.1 (Hardening Pass)

The v3.1 hardening pass adds five rules across `post-execution`, `executing-plans`, and `agents/tests.md` that close a security gate, sharpen triage, prevent rework loops, and tighten the tests reviewer. All five are imported from public, well-documented sources:

- **[mattpocock/skills](https://github.com/mattpocock/skills) @ b843cb5** — the `diagnose` Phase-1 feedback-loop discipline (build a deterministic repro before hypothesizing; produce 3–5 ranked falsifiable hypotheses; tag debug logs with a unique prefix) is imported into `post-execution:triage` (D3). The `tdd` vertical-slice tracer-bullet rule and the `mocking.md` "mock at system boundaries only" rule are imported into `executing-plans` Step 2b and `agents/tests.md` Scope item 3 (D2).
- **[affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) @ 841beea** — the AgentShield static-config-scan rule patterns are inlined into `post-execution:regression-check` Step 2a (D1). Patterns are inlined as prose (no `npx` runtime dependency); upstream maintains 102 rules with auto-fix mode, our subset covers secrets, permissions, hook injection, MCP risk profile, and agent config review with severity gating (Critical → BLOCK, High → FLAG, Medium → log).
- **[millionco/claude-doctor](https://github.com/millionco/claude-doctor) @ f5efb2a** — the edit-thrashing and error-loop signals (>3 edits to one file → re-read brief; 3 consecutive tool failures → escalate to triage instead of retrying) are imported into `executing-plans` Step 2b's Rework guardrails block (D2). The repeated-instructions detection (≥60% phrase-overlap across 5 PM turns → route to brief revision rather than code fix) is imported into `post-execution:triage` Step 1.5 (D3).

**De-facto policy note.** The inlined AgentShield rule patterns in D1 are the plugin's de-facto plugin-config security policy as of v3.1 — the brief declared no security policy doc upstream of this work, and the rule wording shipped here is authoritative-by-default. Future PMs editing security-sensitive plugin config should treat these patterns as the contract until a project-level security policy supersedes them.

The v3.1 choice mirrors v2.2: import the high-leverage idea, leave the heavyweight stack behind. AgentShield's `npx` runtime, claude-doctor's cross-session signals, and mattpocock's persistent domain-language convention are all explicitly out of scope. We thank all three projects for their public, well-documented work.

---

## Feature folder layout

```
docs/strategic-implementation/2026-04-28-auth-redesign/
├── product-brief_auth-redesign.md
├── execution-plan.md
├── validation-log.md
└── post-execution-report.md
```

Plus `docs/strategic-implementation/project-learnings.md` at the root.

---

## Get started

Install the plugin via your Claude Code marketplace, then in any project run:

```
/strategic-implementation
```

Describe what you want built. The rest of the workflow takes over from there.
