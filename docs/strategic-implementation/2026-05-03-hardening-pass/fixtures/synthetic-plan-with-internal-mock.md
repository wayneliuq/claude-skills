<!--
TEST FIXTURE — not a real plan.
Purpose: D2 cli validation. Feeding this into the `tests` reviewer agent must
produce a JSON output whose `flags` array contains an entry with
`dimension: "mock-placement"` and `severity: "high"`.

If the agent flags any other dimension instead, OR fails to flag at all, D2's
mock-placement rule is structurally broken and D2 must be reworked.
-->

# Execution Plan: Synthetic — internal-mock test
_Implements: (fixture, no real brief) · Date: 2026-05-03_

## Context

A one-deliverable synthetic plan that deliberately mocks an internal collaborator. Used as input to the tests reviewer to confirm the mock-placement rule fires.

## Deliverables (DAG)

### D1 — Add a price calculation helper
- **Integration-risk class:** `d`
- **Validation:** `tdd` — write a test that mocks the internal `applyDiscount` helper inside the same module and asserts the wrapper function returns the expected total. The test does not exercise `applyDiscount`; it stubs it.
- **Files:**
  - `src/billing/calculate-total.ts` — new wrapper function `calculateTotal(items, code)`
  - `src/billing/apply-discount.ts` — internal helper (already exists in module)
  - `src/billing/calculate-total.test.ts` — new test file that mocks `applyDiscount`
- **Steps:**
  1. Write `calculate-total.test.ts` that imports `calculateTotal` and mocks the internal `applyDiscount` collaborator using the test framework's mock facility. Stub `applyDiscount` to return a fixed number; assert `calculateTotal` returns the stubbed result plus tax.
  2. Implement `calculateTotal` in `calculate-total.ts` calling `applyDiscount` and adding tax.
  3. Run the test; it passes because `applyDiscount` is stubbed.
- **Deps:** none.
- **Pre-flight env check:** test runner available.
- **may-invalidate:** none.
- **Visual contract:** n/a.
- **Consumer audit:** n/a — internal module addition; no external consumers of `calculateTotal` yet.

## Parallel groups & order

D1 only.

## Reused existing patterns

None — synthetic fixture.

## Risks & contingencies

None — synthetic fixture.

## Out of scope for this plan

Everything except the single deliverable above.
