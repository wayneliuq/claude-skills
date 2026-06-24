---
name: ui-mockup
description: Generates a static HTML mockup as the visual contract for non-trivial UI work. Sits between brief approval and execution-plan drafting. One file, inline CSS, no JS framework, no build. Reuses repo design tokens. PM iterates via conversational feedback in chat. Mockup-vs-brief conflicts route back to brief revision.
---

# ui-mockup

You produce a single static `mockup.html` that serves as the visual contract for a feature. The mockup is the cheapest possible failure point for visual misalignment — drafted in seconds, iterated on in minutes, locked before the execution plan references it. Throwaway artifact; lives in the feature folder, never the source tree.

**Modes:** `generate` (new mockup), `revise` (PM feedback), `conflict-back-to-brief` (mockup change contradicts brief).

**Output location:** `<feature-folder>/mockup.html`.

---

## Discipline rules (all modes)

1. **One file.** Single `mockup.html` with inline `<style>`. No `<script>` tags. No external assets. No build step.
2. **Reuse repo styles where they exist.** Discovery order is fixed; the mockup names what it found and what it fell back to.
3. **No fabrication.** If the brief is silent on a UI element, leave a TODO marker rather than inventing.
4. **Throwaway, not polished.** The mockup proves layout and IA — not pixel fidelity.
5. **PM feedback is conversational.** The PM describes changes in chat; the skill re-emits `mockup.html` (output-only). No inline-comment or sibling-feedback-file editing.
6. **Conflict-back-to-brief.** A PM comment that contradicts a brief deliverable is not silently applied — the conflict is surfaced and the workflow loops back to brief revision.
7. **Anti-slop (SLIM tier).** Apply the SLIM tier of `agents/frontend-quality.md` — zero em-dashes, eyebrow restraint, no repeated section layouts, hero fits the first viewport, no fake-precise numbers, no scroll cues/version tells, real content not lorem, off-black/off-white. These are legibility/IA rules, not pixel polish; they do not violate rule 4 (throwaway, not polished). Do NOT pull in the RICH tier (motion, fonts, design systems) — that belongs to shipped UI, not the mockup.
8. **Show the edit in place, not in isolation.** The mockup is a contextual diff, not a floating component. Render the surrounding *existing* surface the edit lands in — the nav, the page chrome, the adjacent sections that will NOT change — using a muted "unchanged" treatment (reduced opacity or a neutral wash), and mark the new/changed regions clearly (a labeled outline or a `NEW` / `CHANGED` tag). The PM should see exactly where the work touches the product and what it leaves alone. If the surrounding surface is unknown, survey it (Task B) before mocking — don't invent the context.
9. **Survey conventions, not just tokens.** Run Task B (convention survey) before writing the mockup. The mockup must match the de-facto conventions of similar existing surfaces; conflicts between the brief and existing conventions are surfaced to the PM, never silently resolved in the mockup.
10. **Codify resolved conventions.** When PM iteration resolves a convention that should bind future work (a layout/interaction/naming decision not previously documented), codify it — see the `codify` step. This is the mockup phase's contribution to the brief's maintainer goal.
11. **Plan-mode entry-check.** If plan mode is active, call `ExitPlanMode` before writing files (`execution-plan` is the only skill exempt).

---

## Mode: generate

You receive:
- Brief path
- Feature folder path
- Trigger reason from orchestrator (`new screen` / `≥2-step flow` / `IA change`)

### Task A — discover repo styles (tokens)

Token discovery order (stop at first hit, but record what was found):

1. **CSS variables.** Glob `**/*.css` for `:root { --` blocks. Extract color, spacing, typography variables.
2. **Tailwind config.** Glob `tailwind.config.{ts,js,cjs,mjs}`. Extract `theme.extend` palette, fontSizes, spacing.
3. **Theme file.** Glob `theme.{ts,js}`, `styles/theme*`, `src/theme*`. Extract token exports.
4. **Neutral fallback.** No styles found → use the documented neutral palette below.

Documented neutral fallback:
- Background `#ffffff`, surface `#f5f5f7`, border `#e5e5ea`
- Text primary `#1d1d1f`, secondary `#6e6e73`
- Accent `#0066cc`
- Font stack `system-ui, -apple-system, "Segoe UI", sans-serif`
- Spacing scale 4 / 8 / 12 / 16 / 24 / 32 / 48 px

### Task B — survey conventions (beyond tokens)

Tokens are not conventions. Tokens tell you *what colors exist*; conventions tell you *how this kind of surface is built here* — where the primary action sits, how empty/error/loading states look, how forms validate, what a list row looks like. Survey all that apply; record each source and what it yielded. This pass also serves the maintainer (the brief's second user): the mockup should look like it belongs in this repo, not like a foreign surface someone has to reconcile later.

1. **Convention docs.** Read `docs/strategic-implementation/documentation-registry.md`; pull any entry tagged as UI conventions / design system. Read the `ui_conventions` doc reference from the brief's §7 (clarify collects it). Read whatever those point to.
2. **Figma.** If the brief names a Figma file or the registry points to one and the Figma MCP is connected (`mcp__plugin_design_figma`), survey the referenced frames for the surface being built. If not connected, note that and continue — do not block.
3. **Similar-surface survey (always, even when docs exist — especially when they don't).** Use `mcp__code-review-graph__semantic_search_nodes` to find ≥1 existing surface that does something *similar* to this feature (a sibling page, an analogous form, a comparable list/detail view). Read it. Extract the de-facto conventions it embodies (layout skeleton, control placement, state handling, naming) and note any **conflict** between what the brief asks for and what the repo already does. A conflict is a flag for the PM, not something to silently resolve in the mockup.

Record findings in the mockup's head comment (`Convention survey:` line) and carry conflicts into the handoff announcement.

### Task — write mockup.html

Structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Mockup: <feature-slug></title>
  <!--
    Mockup for: <brief slug>
    Generated: <date>
    Style discovery: <Tailwind config @ <path> | CSS vars @ <path> | theme @ <path> | neutral fallback>
    Convention survey: <convention doc @ <path> | Figma @ <ref> | similar surface: <symbol at path> | none found>
    Conventions codified this round: <doc path(s) | none>
    Conflicts surfaced: <one line each | none>
    Trigger reason: <new screen | ≥2-step flow | IA change>
  -->
  <style>
    /* Inline tokens, derived from discovery */
    :root { --bg: ...; --text: ...; ... }
    /* layout + components */
    /* unchanged-context treatment — applied to existing surfaces the edit does NOT touch */
    .unchanged { opacity: .5; }
    .change-marker { outline: 2px dashed var(--accent); }  /* mark new/changed regions */
  </style>
</head>
<body>
  <!-- Mockup body. Use brief deliverables as the structural outline. -->
  <!-- Render surrounding EXISTING surfaces (nav, chrome, adjacent sections) with class="unchanged". -->
  <!-- Mark NEW/CHANGED regions with class="change-marker" and a visible NEW/CHANGED tag. -->
  <!-- For multi-step flows, render each step in a separate section. -->
</body>
</html>
```

### Task — handoff

Write `<feature-folder>/mockup.html`. Return path and announce:

> "Mockup drafted at `<path>`. Tokens: `<what was found>`. Convention survey: `<doc / Figma / similar surface, or none found>`. Conflicts with existing conventions: `<one line each, or none>`. Conventions codified: `<doc path(s), or none>`. The mockup shows the edit in place — surrounding surfaces are dimmed as unchanged; new/changed regions are marked. Review by opening the file in a browser. Describe any changes in chat and reply 'revise', or reply 'approve' to proceed to execution planning."

Do NOT auto-advance. If conflicts were surfaced, the PM resolves them before approving (a conflict may route to `conflict-back-to-brief`).

---

## Mode: revise

You receive:
- Path to existing `mockup.html`
- Brief path (for conflict checks)
- PM feedback (given conversationally in chat)

### Task — collect feedback

1. Read `mockup.html` (via the store cache / `store.sh read`).
2. Take the PM's chat feedback as the list of items.
3. (no file-embedded feedback — the record is output-only.)

### Task — conflict scan (per item)

For each feedback item, scan brief deliverables and HARD DECISIONs for textual conflict (the comment asks to change something the brief explicitly specifies). On conflict, switch to `conflict-back-to-brief` mode for that item; do not apply silently.

### Task — apply non-conflicting items

For each non-conflicting item:
1. Apply the change and re-emit `mockup.html` with it.

### Task — codify resolved conventions

If this round resolved a reusable convention, run the **Codify resolved conventions** step (see below). Skip if nothing reusable was resolved.

### Task — append revision-log block

Prepend a comment block at the top of the `<body>` recording: revision number, date, one-line summary of what changed.

### Task — handoff

Write `mockup.html`. Announce:

> "Mockup revised. `<Conventions codified: doc path(s), or omit if none.>` Reload the file. Review or reply 'approve' to proceed."

---

## Mode: conflict-back-to-brief

Triggered when a PM feedback item contradicts a brief deliverable or HARD DECISION.

### Task — surface the contradiction

Show the PM:
- The feedback item verbatim
- The conflicting brief line (deliverable D<n> or HARD DECISION row) verbatim
- The choice: `revise brief` / `abandon mockup change`

### Task — route

- **revise brief** → invoke `strategic-implementation:product-brief-drafter` in `revise` mode, passing the conflict as out-of-band feedback. After brief revision, the orchestrator returns to mockup revision.
- **abandon mockup change** → drop the feedback item. Continue with remaining items.

A mockup never silently overrides the brief. The brief is the contract; the mockup is its visualization.

---

## Codify resolved conventions (generate + revise)

The mockup phase is where UI conventions get *decided* — control placement, state handling, naming, layout skeleton. When a decision is made that should bind future work on this surface (and is not already written down), codify it so the next maintainer inherits it instead of re-deciding. This is the mockup's half of the brief's maintainer goal (`product-brief-drafter` rule 13).

**When to codify** — a convention resolved during this round that is (a) not already in a convention doc the survey found, and (b) reusable beyond this one feature (it describes how *this kind of surface* behaves, not a one-off choice). One-off layout calls specific to this feature do NOT get codified.

**How:**
1. If a UI-convention doc already exists (from Task B's survey), append the resolved convention to it in that doc's existing style.
2. If none exists and ≥1 reusable convention was resolved, create `docs/strategic-implementation/ui-conventions.md` (or the repo's documented location, if conventions live elsewhere — mirror the repo, don't impose a new home) with a one-line purpose preamble, and add the convention.
3. **Register it.** Upsert a row in `docs/strategic-implementation/documentation-registry.md` (`Path | Covers | Last Updated | Update Trigger | Owning Area`) so `execution-plan`'s `may-invalidate` pass and future `clarify` runs know it exists. Set `Last Updated` to today.
4. Record the codified doc path(s) in the mockup head comment (`Conventions codified this round:`).

Codifying is additive and low-stakes — but do not over-codify. If nothing reusable was resolved, write `none` and move on.

---

## Handoff

The orchestrator waits for PM approval. On approval, the orchestrator passes the mockup path to `execution-plan` as the `Mockup path` input, and execution-plan + post-execution treat it as the visual contract.

---

## Record routing — externalized artifact store

Per-feature **records** (brief / plan / validation-log / checkpoint / reports / mockup / brief-meta) route through the store adapter, not the feature folder directly: wherever a step says write/read `<feature-folder>/<file>`, use the store address `<repo-id>/<date-slug>/<file>` with in-repo fallback. Full read/write/fallback protocol: [`scripts/store/README.md`](../../scripts/store/README.md#record-routing-protocol-agent-facing). **Durable tier — `project-learnings.md`, `documentation-registry.md` — stays in-repo, never routed to the store.**
