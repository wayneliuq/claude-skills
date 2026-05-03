_Research date: 2026-04-05_
_Revised: 2026-04-06 — Rewritten as agentic behavioral rules per domain, organized by implementation lift reduction (low effort) and refactoring prevention (high effort). Non-agentic findings removed: human team process rules, reviewer fatigue, and CI/CD tooling integration advice._

---

### 10k-foot

The 10k-foot agent checks whether the plan aligns with the system's existing architecture, stated goals, and desired end-product before any code is written.

**Low effort — reduces implementation lift**

- If the plan does not name at least one downstream consumer for each new component it introduces, FLAG it. Plans that omit consumers force mid-implementation discovery of integration requirements, adding unplanned work to sessions that assumed the interface was someone else's problem.
- If any session's goal cannot be mapped to a stated architectural component or layer in the system's existing structure, FLAG it. Sessions without an architectural home require the implementer to invent structure during execution rather than follow existing patterns.

**High effort — prevents high-effort refactoring**

- If the plan introduces a cross-cutting concern (auth, logging, caching, error handling) as a per-component addition rather than at a shared layer, FLAG it. Retrofitting cross-cutting concerns after implementation requires touching every component that was built without them.
- If the plan modifies a shared component without specifying the compatibility impact on other plans, sessions, or services that depend on it, FLAG it with the names of affected dependents. Dependency mismatches discovered post-implementation require coordinated rollbacks across multiple consumers.
- If the plan's approach contradicts the system's stated architectural direction (monolith vs. microservices, sync vs. async, REST vs. event-driven), BLOCK it. Architectural direction changes require whole-system refactoring to undo and cannot be applied retroactively to sessions already executed.

---

### technical-expert

The technical-expert agent performs deep implementation-level review: surfacing known pitfalls, ordering errors, incorrect assumptions, and missing integration requirements before execution begins.

**Low effort — reduces implementation lift**

- Trace the execution sequence of each session's steps against the technology's required initialization order. Flag any step that depends on a resource (database connection, cache client, external service) that is initialized in a later step — these cause immediate runtime failures on the first execution attempt.
- Flag any step that performs a fallible operation (network call, file read, database write) without specifying error handling. Missing error handling is discovered at the first production failure and requires returning to the implementation to add it.

**High effort — prevents high-effort refactoring**

- Trace data flow across session boundaries. If two sessions must exchange data but no session defines the interface (schema, format, contract) for that exchange, FLAG it. Integration gaps discovered during session N+1 execution require rework of session N's already-committed deliverables.
- Review each plan step simultaneously as an attacker and as a future maintainer. Flag any step where the implementer must make an assumption about behavior not stated in the plan — specifically: assumed input ranges, assumed call ordering, assumed concurrency safety. Unstated assumptions become bugs when wrong and require refactoring to correct across every caller that inherited the assumption.

---

### scope-limiter

The scope-limiter agent detects when sessions contain work beyond their stated goal, flags incorrect session ordering, and identifies deliverables that should be split.

**Low effort — reduces implementation lift**

- Compare each session's files-affected list to its single stated goal. Flag any file that appears in the list but is not required to accomplish that goal, naming the specific file. Unplanned file changes introduce regression risk in areas outside the session's described test coverage.
- Flag any "drive-by" refactoring — improvements to code touched incidentally by the session but not part of the stated deliverable. Name the specific change and suggest creating a separate session for it. Drive-by refactoring bloats commits, complicates blame and bisect, and requires re-review.

**High effort — prevents high-effort refactoring**

- Compare each session's deliverables to the original spec. Flag any deliverable not present in the spec by name. Gold-plating discovered after implementation requires scope negotiation, stakeholder approval, and rework to remove or properly integrate the unrequested enhancement.
- Flag any session that bundles two logically independent deliverables — deliverables that could fail, roll back, or be reverted independently. Name both and state which should be extracted to its own session. Bundled deliverables make rollback impossible if one fails, requiring manual disentanglement of a single commit's changes.

---

### test-coverage

The test-coverage agent verifies that the plan describes tests of the right type and granularity for every significant behavior, with coverage proportional to risk.

**Low effort — reduces implementation lift**

- Flag any test description that uses abstract language ("verify it works," "ensure correct behavior," "test the feature") without naming the specific input, state, and expected output. Abstract test descriptions produce implementations that pass the description while failing the actual requirement — discovered only when a real input triggers the uncovered case.
- Flag any behavior described in the plan that has no corresponding test for its error path or edge case. Happy-path-only tests create false confidence and fail at the first atypical input, requiring a return to implementation to add the missing coverage.

**High effort — prevents high-effort refactoring**

- Flag any plan whose described test distribution is E2E-heavy relative to unit tests. Specifically: if more than three behaviors that could be tested at unit level are described as E2E tests, FLAG it. An inverted testing pyramid (few unit, many E2E) is slow, brittle under normal refactoring, and expensive to restructure — each E2E test that needs to be converted to unit tests requires rewriting the test and often restructuring the code under test.
- Flag any two components that share a boundary (one produces, one consumes) where no integration test for that boundary is described. Unit tests for each component cannot catch interface mismatches by construction; discovering a boundary mismatch at runtime requires implementation rework on both sides of the boundary.

---

### security

The security agent reviews implementation plans for attack surface expansion, access control gaps, data exposure risks, and secrets handling before any code is written.

**Low effort — reduces implementation lift**

- Flag any privileged action described with only UI-layer enforcement (hiding a button, disabling a form field, greying out a menu item) and no corresponding server-side authorization check. UI-only authorization is bypassed by any direct API request; adding server-side enforcement after deployment requires touching every affected endpoint and redeploying with a coordinated release.
- Flag any credential, API key, token, secret, or password described as stored in code, a configuration file, or any version-controlled location — this is a BLOCK. The plan must name the secrets management approach (environment variable, secrets manager service) before execution proceeds.

**High effort — prevents high-effort refactoring**

- For every new entry point the plan introduces (HTTP endpoint, webhook, file upload handler, message queue consumer, scheduled job), verify the plan specifies all four: (1) authentication requirement, (2) server-side authorization check, (3) rate limiting, (4) input validation. Missing any one of the four is a FLAG regardless of the others. Adding a missing control after the entry point is in production requires a coordinated deployment, may require a security incident response window, and can trigger mandatory disclosure depending on jurisdiction.
- Flag any plan that defers threat modeling and abuse-case analysis entirely to implementation. Security decisions made during implementation rather than at the plan level become load-bearing — the structure of what was built reflects those decisions — making them expensive to reverse.

---

### data-model

The data-model agent reviews schema changes, migration scripts, and data lifecycle decisions to ensure correctness, migration safety, and no silent data loss.

**Low effort — reduces implementation lift**

- Flag any monetary, financial, or quantity field described as a floating-point type (`float`, `double`, `real`) — this is a BLOCK. Floating-point accumulates rounding errors silently; correcting float-stored financial data after accumulation requires a migration plus manual audit of all affected records, and the error window may trigger regulatory scrutiny.
- Flag any query pattern introduced in the plan (filter, sort, join, range scan) that does not name the database index supporting it. Missing indexes produce full-table scans that are invisible in development with small datasets and catastrophic under production data volumes.

**High effort — prevents high-effort refactoring**

- Flag any column drop or rename that does not follow the expand-contract pattern (add new column alongside old → migrate data → remove old column in a later session) — this is a BLOCK. Dropping or renaming a column during a rolling deployment instantly breaks old application instances still reading the original column name, with no automatic rollback path.
- Flag any NOT NULL constraint addition to an existing column without a corresponding backfill migration — this is a BLOCK. Adding NOT NULL to a column containing existing null rows fails immediately on ALTER, cannot be rolled back without a second migration, and requires emergency intervention if it reaches production.
- Flag any migration that is not verified to be safe when old and new application code run simultaneously against it. A migration safe under new code can corrupt data when old instances are still writing during a rolling deploy; discovering this post-deployment requires emergency rollback and manual data repair.

---

### api-contract

The api-contract agent ensures that every interface introduced or modified by the plan makes a complete, consistent, and durable promise to its consumers.

**Low effort — reduces implementation lift**

- Flag naming inconsistencies across interfaces defined in the same plan: different casing conventions (`camelCase` vs. `snake_case`), different terms for the same concept (`user_id` vs. `userId` vs. `account_id`). Naming inconsistencies discovered after consumers have been built require coordinated changes across every consumer codebase, since the inconsistency is now part of the contract.
- Flag any plan that introduces new interfaces without specifying the error envelope format. Inconsistent error structures (some endpoints return `{"error": "..."}`, others return HTTP codes with no body) require client-side special-casing per endpoint and are expensive to standardize retroactively once consumers have written error-handling code against the inconsistent shape.

**High effort — prevents high-effort refactoring**

- Flag any modification to an existing interface (field rename, type change, optional → required parameter, endpoint removal) where known downstream consumers are not named in the plan — this is a BLOCK. Breaking changes with unaddressed consumers cause production failures across all consumer systems simultaneously, requiring emergency coordination across teams that did not plan for the change.
- Flag any plan that introduces interfaces without specifying how contracts will be captured and tested. Contract tests are the only mechanism that reliably catches interface regressions before they reach production; adding them retroactively requires re-examining every consumer's actual behavior against the assumed contract, often uncovering assumptions the producer never intended to support.

---

### performance

The performance agent reviews structural decisions in the plan that tend to produce slow, resource-hungry, or fragile systems under real-world load.

**Low effort — reduces implementation lift**

- Flag any plan that introduces performance-sensitive features (search, list endpoints, data aggregation, report generation, batch processing) without stating performance targets (maximum response time, minimum throughput, memory ceiling). Without targets, there is no way to determine during execution whether performance is acceptable or to catch regressions in later sessions.
- Flag any query pattern introduced in the plan without naming the indexes that support it. Missing indexes are invisible during development with small datasets; specifying them in the plan ensures they are part of the migration, not a post-deployment discovery.

**High effort — prevents high-effort refactoring**

- Flag any loop over collection results that triggers a per-item database query (N+1 pattern). N+1 queries appear harmless in development (small dataset = 11 queries) and catastrophic in production (real dataset = 11,000 queries per request). Fixing them after implementation requires restructuring query logic, adding eager loading, or introducing a DataLoader layer — each of which touches every call site.
- Flag any slow operation (external API call, file processing, email dispatch, report generation) described as synchronous in a user-facing request path. These must be moved to background queues; retrofitting async processing after implementation requires new infrastructure (queue, worker process), changes to every caller, and a new error-handling surface for async failures.
- Flag any frequently-read data that is fetched from an expensive source on every request with no specified caching strategy (scope, invalidation rule, TTL). Adding a caching layer after the fact requires introducing cache infrastructure, designing invalidation logic for every write path, and auditing all readers for stale-read risk.

---

### dependency

The dependency agent evaluates every new external library, service, or infrastructure component the plan introduces for necessity, license compatibility, maintenance health, and version safety.

**Low effort — reduces implementation lift**

- Flag any dependency introduced for a use case addressable by a library already present in the project's dependency tree, or by fewer than 100 lines of custom code. Unnecessary dependencies add transitive dependency weight, license obligations, and long-term maintenance cost that compounds with every additional dependency introduced later.
- Flag any dependency specified with a version range (`^1.2.0`, `>=2.0`, `*`) rather than an exact pinned version without a committed lock file. Unpinned ranges allow a new upstream release to silently introduce breaking changes or vulnerabilities between plan approval and execution, making the build non-reproducible.

**High effort — prevents high-effort refactoring**

- Flag any GPL or AGPL licensed dependency introduced into a commercial product — this is a BLOCK. Copyleft license violations require either replacing the dependency entirely (reworking every usage site) or releasing the entire product under the same copyleft license. Neither option is a quick fix once the dependency has been built into multiple sessions.
- Flag any dependency maintained by a single person with no releases in the past 18 months. The plan must explicitly acknowledge the abandonment risk and name a migration path if the library becomes unmaintained. Replacing a load-bearing abandoned dependency after it has been integrated across multiple sessions requires significant refactoring effort across every session that depended on it.

---

### frontend-engineer

The frontend-engineer agent is conditional — it runs only when the plan includes UI, UX, or front-end changes. If no such changes are present, it returns PASS immediately without review. When active, it checks whether the described UI behavior, interactions, component structure, visual consistency, and stylesheet architecture will produce the intended user experience before any front-end code is written.

**Low effort — reduces implementation lift**

- Flag any described interaction that is ambiguous — where two different implementations would feel meaningfully different to the user (e.g., "clicking saves the form" without specifying whether it saves in-place or navigates away). Ambiguous interactions require a UX decision mid-implementation that should have been made at plan time.
- Flag any UI state — loading, error, empty, partial-load, disabled — that is not accounted for in any session's deliverables. Missing states are discovered during QA or user testing, requiring a return to implementation to add them.
- Flag any component whose visibility condition is unspecified: when does it appear, when does it disappear, and what triggers the transition? Visibility conditions left to the implementer's judgment produce UI that behaves differently across implementations and requires correction after review.
- Flag any animation or transition described without specifying its implementation approach (CSS-only vs. JS library such as Motion or GSAP). Mixed animation approaches across components create an inconsistent motion language and an expensive audit when the animation strategy needs to be aligned or changed.
- Flag any plan that introduces new UI components without a stated aesthetic reference — a design system component, an existing project pattern, or an explicitly described aesthetic direction. Components built without an aesthetic anchor drift from the rest of the UI across sessions and require a visual alignment pass to correct.

**High effort — prevents high-effort refactoring**

- Flag any component whose color, typography, or spacing values are applied inline or hardcoded (e.g., `style="color: #3B82F6"`, hardcoded Tailwind color utilities not mapped to a theme, magic-number pixel values) rather than referenced from the project's CSS variables or design token stylesheet. Every hardcoded value is an independent change point: theming updates, dark mode, accessibility contrast adjustments, and brand changes each require finding and replacing every hardcoded instance rather than changing one variable declaration.
- Flag any plan that introduces new visual properties — a new color, a new type size, a new spacing value, a new shadow — without a corresponding step to define that value as a CSS variable or design token before any component uses it. Visual properties added component-first rather than token-first fragment the design system: some sessions will use the token, others will hardcode the same value, and the two diverge the moment the token value changes.
- Flag any behavior that is only correct within a specific layout position or spatial constraint (bottom tray, sidebar, fixed-height panel) where the plan does not include an explicit step to visually verify the component's layout position before implementing that behavior. Behaviors built on unverified layout assumptions are discarded entirely when the layout assumption turns out wrong — the implementation cannot be salvaged; it must be rewritten.
- Flag any plan that describes layout for a single viewport or content density without specifying behavior at the extremes of the described content range and across the project's supported breakpoints. Layout assumptions that hold at medium content density and medium viewport width break at the extremes, requiring layout restructuring — not restyling — to fix.
- Flag any state management approach described in a way that would produce stale or inconsistent UI — specifically: local state used for data that must stay synchronized across sibling or parent components, or global state used for data that is component-local. Incorrect state architecture cannot be corrected by adjusting values; it requires restructuring the component hierarchy and the data flow between components.
- Flag any described pattern that conflicts with how the underlying framework handles it — uncontrolled vs. controlled component patterns, event delegation assumptions, CSS specificity ordering, hydration behavior in SSR contexts. Framework pattern conflicts require rewriting the component from the conflicting pattern to the correct one, not adjusting the logic within the existing pattern.
- Flag any custom component proposed where an existing design system component covers the same use case. Custom components that duplicate design system coverage diverge from the system over time, are not updated when the design system updates, and require a migration back to the canonical component in a future refactoring session.

### future-proofing

The future-proofing agent checks whether the plan's structural decisions — naming, modularity, file placement, and documentation — will leave the codebase maintainable and navigable for a developer who was not present when it was built.

**Low effort — reduces implementation lift**

- Flag any file whose proposed location is inconsistent with where analogous files live in the existing structure. Misplaced files force all future developers to search rather than predict; moving them after implementation requires updating every import, every reference in documentation, and every tool configuration that relies on the path.
- Flag any session that introduces a new abstraction, changes an established pattern, or deviates from project conventions without a "Docs to update" entry that explains the *why* behind the decision — not just what was changed. Undocumented decisions become mysteries that each future session must reverse-engineer from the implementation, compounding with every session built on top of them.

**High effort — prevents high-effort refactoring**

- Flag any naming inconsistency introduced across sessions: different terms for the same concept (`user`, `account`, `member` used interchangeably), different casing for equivalent entities, different abbreviation conventions. Names appear in every interface, every test, every document, and every consumer; changing them after the fact requires a coordinated rename across all of those surfaces simultaneously.
- Flag any component described with more than one distinct responsibility that could be independently tested, replaced, or versioned. Multi-responsibility components cannot be individually refactored without touching all their concerns simultaneously; splitting them after implementation requires refactoring every caller to use the new, narrower interface.
