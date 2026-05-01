---
name: ui-mockup
description: Generates a static HTML mockup as the visual contract for non-trivial UI work. Sits between brief approval and execution-plan drafting. One file, inline CSS, no JS framework, no build. Reuses repo design tokens. PM iterates via inline `<!-- pm: -->` comments. Mockup-vs-brief conflicts route back to brief revision.
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
5. **PM feedback marker.** Inline `<!-- pm: ... -->` comments and a sibling `mockup-feedback.md` are the two iteration channels. Both must be supported.
6. **Conflict-back-to-brief.** A PM comment that contradicts a brief deliverable is not silently applied — the conflict is surfaced and the workflow loops back to brief revision.

---

## Mode: generate

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

You receive:
- Brief path
- Feature folder path
- Trigger reason from orchestrator (`new screen` / `≥2-step flow` / `IA change`)

### Task — discover repo styles

Discovery order (stop at first hit, but record what was found):

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
    Trigger reason: <new screen | ≥2-step flow | IA change>
  -->
  <style>
    /* Inline tokens, derived from discovery */
    :root { --bg: ...; --text: ...; ... }
    /* layout + components */
  </style>
</head>
<body>
  <!-- Mockup body. Use brief deliverables as the structural outline. -->
  <!-- For multi-step flows, render each step in a separate section. -->
</body>
</html>
```

### Task — handoff

Write `<feature-folder>/mockup.html`. Return path and announce:

> "Mockup drafted at `<path>`. Discovery: `<what was found>`. Review by opening the file in a browser. Add `<!-- pm: ... -->` comments inline (or write a sibling `mockup-feedback.md`) and reply 'revise', or reply 'approve' to proceed to execution planning."

Do NOT auto-advance.

---

## Mode: revise

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

You receive:
- Path to existing `mockup.html`
- Brief path (for conflict checks)
- PM feedback (inline `<!-- pm: ... -->` comments and/or sibling `mockup-feedback.md`)

### Task — collect feedback

1. Read `mockup.html`. Find every `<!-- pm: ... -->` comment.
2. Read `<feature-folder>/mockup-feedback.md` if it exists.
3. Build a list of feedback items, each tagged with its source (inline / feedback-file).

### Task — conflict scan (per item)

For each feedback item, scan brief deliverables and HARD DECISIONs for textual conflict (the comment asks to change something the brief explicitly specifies). On conflict, switch to `conflict-back-to-brief` mode for that item; do not apply silently.

### Task — apply non-conflicting items

For each non-conflicting item:
1. Address the feedback in-place.
2. Remove the inline `<!-- pm: -->` comment, OR mark the line in `mockup-feedback.md` as `applied`.

### Task — append revision-log block

Prepend a comment block at the top of the `<body>` recording: revision number, date, one-line summary of what changed.

### Task — handoff

Write `mockup.html`. Announce:

> "Mockup revised. Reload the file. Review or reply 'approve' to proceed."

---

## Mode: conflict-back-to-brief

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

Triggered when a PM mockup-feedback item contradicts a brief deliverable or HARD DECISION.

### Task — surface the contradiction

Show the PM:
- The feedback item verbatim
- The conflicting brief line (deliverable D<n> or HARD DECISION row) verbatim
- The choice: `revise brief` / `abandon mockup change`

### Task — route

- **revise brief** → invoke `strategic-implementation:product-brief-drafter` in `revise` mode, passing the conflict as out-of-band feedback. After brief revision, the orchestrator returns to mockup revision.
- **abandon mockup change** → drop the feedback item; remove the comment or mark `dropped` in `mockup-feedback.md`. Continue with remaining items.

A mockup never silently overrides the brief. The brief is the contract; the mockup is its visualization.

---

## Handoff

The orchestrator waits for PM approval. On approval, the orchestrator passes the mockup path to `execution-plan` as the `Mockup path` input, and execution-plan + post-execution treat it as the visual contract.
