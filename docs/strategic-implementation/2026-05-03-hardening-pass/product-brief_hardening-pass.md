# Product Brief: Hardening Pass — Five Rules
_Slug: hardening-pass · Date: 2026-05-03 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> TBD — open question

_Working hypothesis (drafter, not PM): SI runs now catch a class of failure they previously missed — plugin config security issues, vague-spec triage spirals, mid-deliverable file thrashing, error-loop flailing, and horizontal-slice tests — without measurable token overhead. The five rules are imported with attribution from three vetted external skill repos. Confirm or replace this paragraph before plan approval._

## 2. What the user does / sees

| # | Deliverable (user-observable) | Validation |
|---|---|---|
| D1 | When a feature touches `.claude/` files, post-execution runs an inlined static config scan (secrets, dangerous permissions, hook injection patterns, MCP risk profile, agent config issues). Critical findings BLOCK the regression-check; High findings FLAG; Medium/Info logged. | `cli` — run regression-check on a feature that intentionally introduces a hardcoded API key in a hook file; confirm BLOCK output names the offending file and rule. |
| D2 | When a PM invokes triage, the skill builds a deterministic reproduction of the issue *before* proposing fixes, then surfaces 3–5 ranked falsifiable hypotheses, and tags any debug logs it adds with a unique prefix so they can be removed cleanly. | `cli` — run triage against a synthetic bug; observe that no fix is proposed until a repro exists, hypotheses are listed, and debug-log prefix is declared. |
| D3 | During execution, the agent self-tracks per-deliverable rework: more than 3 edits to the same file inside one deliverable triggers a forced re-read of the brief before further edits; 3 consecutive tool failures escalate to triage rather than a 4th retry. | `cli` — fabricate a deliverable that requires re-edits; confirm the trip-wire fires and the agent re-anchors on the brief. Fabricate a tool-call loop; confirm escalation, not retry. |
| D4 | Test work follows a one-test-one-implementation tracer-bullet rule (no horizontal slicing — write one failing test, make it pass, repeat). The `tests` reviewer agent flags any test that mocks an internal collaborator (mocks are allowed only at system boundaries). | `cli` — execute a deliverable that adds tests; confirm tests are added incrementally rather than in batch. Run the `tests` reviewer on a plan that mocks an internal helper; confirm it flags. |
| D5 | When a triage session detects the PM has rephrased the same instruction within the last 5 turns (≥60% similarity, agent-eyeballed), it routes the issue back to brief revision instead of attempting another code fix. | `cli` — feed triage a transcript with two paraphrased PM messages within 5 turns; confirm it returns "specification ambiguity — revise brief" rather than diving into code. |
| D6 | The plugin README credits the three source repos (mattpocock/skills, affaan-m/everything-claude-code AgentShield, millionco/claude-doctor) for the techniques imported. The version bumps to v3.1.0. | `post-hoc` — README diff shows attribution section; `plugin.json` (or equivalent) shows v3.1.0. |

## 3. Success signal

> TBD — open question

_Drafter note: the natural outcome-level signal is "next 3 SI runs that surface bugs use the new triage flow at least once, and at least one regression-check blocks on a config issue that would previously have shipped silently." Replace if PM has a different framing._

## 4. Boundaries

**In scope:**
- Edits to `plugins/strategic-implementation/skills/post-execution/`, `plugins/strategic-implementation/skills/executing-plans/`, `plugins/strategic-implementation/agents/tests.md`, plugin `README.md`, and version metadata.
- Inlined rule patterns equivalent to AgentShield's static checks (secrets, permissions, hook injection, MCP profile, agent config).
- Attribution section in README naming source repos and the technique borrowed from each.

**Out of scope:**
- The full `npx ecc-agentshield` external dependency. We inline the rule patterns instead.
- AgentShield's optional `--opus` red-team/blue-team multi-agent deep scan.
- claude-doctor's cross-session signals (restart-cluster, sentiment, abandonment, negative-drift) — not feature-scoped.
- mattpocock's `CONTEXT.md` + ADR persistent domain language convention (deferred — separate brief).
- Confidence scoring + auto-promotion on `learnings-synthesis` from continuous-learning-v2 (deferred — separate brief).
- Any background hook or daemon (no `PreToolUse`/`PostToolUse` instrumentation).
- Migration tooling for users on v3.0.0 (changes are additive; no migration needed).

**Anti-goals (we'd reject even if free):**
- Adding an external runtime dependency to the SI plugin (`npx ecc-agentshield` or otherwise). Plugin must remain self-contained prose + agents.
- Reinventing the deviation/validation log as a confidence-weighted instinct system (heavier reinvention of what we have).
- Auto-generating CLAUDE.md rules from session transcripts (claude-doctor's `--rules`) — would conflict with the skill's careful prompt structure.
- Hard scripts or literal Jaccard math for similarity detection — the agent eyeballs in prose. Hardening the plugin must not turn it into a code project that needs its own CI.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Source for AgentShield rule patterns | Inline (with attribution) — not external `npx` | `[HARD DECISION]` |
| Similarity check mechanism for repeated-instructions | Agent-eyeballed prose rule, not literal Jaccard math | `[HARD DECISION]` |
| Ship as single feature vs. five separate briefs | Single feature, one brief, one execution plan | settled |
| Version bump | v3.1.0 (additive minor) | settled |
| Attribution location | Plugin README — new "Acknowledgments" section | settled |
| Edit-thrashing trip threshold | >3 edits to same file within one deliverable | settled |
| Error-loop trip threshold | 3 consecutive tool failures without strategy change | settled |
| Repeated-instructions window | Last 5 PM turns, ≥60% similarity | settled |
| AgentShield severity gating in regression-check | Critical → BLOCK · High → FLAG · Medium/Info → log only | settled |
| AgentShield trigger condition | Only when feature's modified-file set includes `.claude/` paths | settled |
| Treatment of debug logs added during triage | Tag with unique prefix declared up front so they can be grep-removed cleanly | settled |

### Tradeoff: Source for AgentShield rule patterns _(HARD DECISION)_

| Option | Pro | Con |
|---|---|---|
| Inline rules with attribution **(chosen)** | No runtime dep; no supply-chain risk; works offline; full control over rule wording | Rules can drift from upstream; we own maintenance |
| `npx ecc-agentshield` | Always upstream-current; richer rule set (102 rules); auto-fix mode | New runtime dep; install/network requirement; output-shape coupling; supply-chain surface |

PM directive: plugin must remain self-contained.

### Tradeoff: Similarity check mechanism _(HARD DECISION)_

| Option | Pro | Con |
|---|---|---|
| Agent-eyeballed prose rule **(chosen)** | Zero runtime cost; consistent with rest of SI; no script to maintain | Subjective threshold; agent may miss edge cases |
| Literal Jaccard math (script) | Deterministic | Adds code path; turns SI into a project with its own tests; against anti-goal |

## 6. Risks & unknowns

- **Rule drift.** Inlined AgentShield patterns will go stale relative to upstream over time. **Owner:** maintainer; mitigation = README note pinning the upstream commit/version we mirrored, plus a learnings-synthesis-style refresh cadence (out of scope this round).
- **False positives in regression-check config scan.** Inlined patterns may flag legitimate config (e.g. a documented test-only token in a fixture). Mitigation = severity gating (only Critical blocks; High flags); first real run will calibrate.
- **Triage rewrite size.** Adding diagnose Phase-1 (#2) and repeated-instructions detection (#5) grows `post-execution:triage` substantially. Risk: skill-prose surface area exceeds what the agent reliably internalizes. Mitigation = compress where possible during execution; tests reviewer flags if any single skill body crosses a readability threshold.
- **Working-backwards / success-signal both `TBD`.** PM did not state outcome in one sentence. The drafter has logged hypotheses (sections 1 and 3) but they are not approved. Reviewers should flag if the brief is approved without these being filled in.
- **Edit-thrashing false trips on legitimately churny files.** Some deliverables genuinely require >3 edits to the same file (e.g. iterative refactors). Mitigation = the rule re-anchors on the brief but doesn't block; the agent decides whether to continue.
- **Version-pinning of imported techniques.** Once shipped, "we borrowed X from mattpocock/skills" is a frozen claim. If those repos change semantics, our attribution still points to the version we copied. Mitigation = README attribution names the commit hash mirrored.
- **Validation-method choices.** D1–D5 all declare `cli`; D6 declares `post-hoc`. Reviewers should verify these are honest — particularly D2 (triage repro behavior) and D5 (similarity detection) which are hardest to validate via a single CLI invocation; may need scripted scenarios.

## 7. References & revision log

**Document references:**
- Architecture: none (skill bodies + agent definitions are architecture-of-record)
- UX/PMF: n/a — backend devtool plugin
- Security policy: none
- Schema/ERD: n/a — no data storage

**Source repos (techniques imported):**
- `mattpocock/skills` — `diagnose` Phase-1 feedback-loop discipline (D2); TDD vertical-slice + mock-at-boundaries (D4)
- `affaan-m/everything-claude-code` — AgentShield static config scan rule patterns (D1)
- `millionco/claude-doctor` — edit-thrashing + error-loop signals (D3); repeated-instructions detection (D5)

**Revision log:**
- v0.1 · 2026-05-03 · initial draft
