---
name: frontend-quality
description: Shared frontend taste reference for strategic-implementation. Two tiers — SLIM (legibility/IA, applied to throwaway mockups) and RICH (pixel quality, applied to shipped UI). Owned in-plugin; not a separate skill. Referenced by ui-mockup (slim) and agents/frontend-engineer (rich).
---

# frontend-quality

Anti-slop discipline for everything this plugin renders. The goal is output that
looks *intentional*, not auto-generated. Rules are split into two tiers by where they
apply. **A rule never silently overrides the brief or an approved mockup** — surface a
conflict instead.

---

## SLIM tier — legibility & IA (applies to `ui-mockup`)

These hold even for a throwaway mockup that proves layout/IA, not pixels. They cost
nothing and kill the most common "AI tells."

1. **Zero em-dashes (`—`)** anywhere — headlines, buttons, body, alt text. The single
   most-violated AI tell. Use commas, periods, or restructure.
2. **Eyebrow restraint.** At most one uppercase/`tracking` eyebrow label per ~3 sections.
   Counting more than `ceil(sections / 3)` is a fail.
3. **No repeated section layouts.** Across ~8 sections use at least 4 distinct layout
   families; max 2 consecutive image-left/image-right alternations.
4. **Hero fits the first viewport.** Headline ≤ 2 lines, subtext ≤ ~20 words / 3–4 lines,
   primary CTA visible without scrolling. Move trust logos / pricing teasers below.
5. **No fake-precise numbers.** `92%`, `4.1×`, `48k` must come from real data or be
   explicitly labeled mock — otherwise drop them.
6. **No scroll cues / version tells.** Banned: "Scroll", "↓ scroll", animated mouse
   icons, and hero badges like `BETA` / `INVITE-ONLY` / `V0.6` unless the brief asks.
7. **No section-number eyebrows.** Banned: `00 / INDEX`, `001 · Capabilities`. Use plain
   labels or none.
8. **Real content, not lorem.** Use the brief's actual copy; if the brief is silent,
   leave a visible `TODO`, never lorem filler.
9. **Off-black / off-white, not pure.** Avoid `#000`/`#fff` for large surfaces — they
   flatten depth. Use the discovered tokens or near-black/near-white fallbacks.

---

## RICH tier — pixel quality (applies to `agents/frontend-engineer`)

These apply when the plan ships real UI. They build on the slim tier.

1. **Font discipline.** Don't default to Inter. Prefer Geist / Outfit / Cabinet Grotesk /
   Satoshi. Serif only when the brand names it or the aesthetic is genuinely editorial.
   Emphasis = italic/bold of the *same* family, never a mixed-family swap.
2. **No "LILA" purple/blue AI glow.** No automatic purple button glows or random neon
   gradients as a default. One accent color, used identically across sections.
3. **Motion must be motivated.** Every animation answers what it communicates (hierarchy,
   feedback, state, story). "Looked cool" is invalid — drop it. If `MOTION_INTENSITY` is
   claimed high, the page must actually move; a static "motion: 7" page is broken.
4. **Reduced-motion is mandatory** for any non-trivial motion: gate behind
   `prefers-reduced-motion` / `useReducedMotion()` and degrade to static.
5. **One design system per project.** For branded/enterprise contexts use the official
   package (Fluent / Material 3 / Carbon / Polaris / Primer / Radix / shadcn customized) —
   don't hand-roll, don't mix two systems.
6. **Image/asset strategy.** Real or generated imagery at correct aspect ratio; real SVG
   logos for social proof (Simple Icons). Never div-based fake screenshots, never broken
   placeholder links.
7. **Consistency locks.** One theme (light OR dark), one corner-radius system, one accent —
   applied identically across all sections. Button/text contrast meets WCAG AA (4.5:1).

---

## Conflict rule

If a slim/rich rule contradicts the brief or an approved mockup, the brief/mockup wins —
surface the tension, don't silently restyle. Taste serves the contract, not vice versa.
