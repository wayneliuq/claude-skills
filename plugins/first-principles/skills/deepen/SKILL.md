---
name: deepen
description: "Rewrite a plan, prompt, goal, spec or brief into a deeper version — not a bigger one — by asking how the best professionals in each domain it touches would find the solution (never prescribing the solution itself), grounded in evidence from the real system, and hand it back in the same form it arrived in (plan file rewritten in place, inline prompt as a fenced block, artifact at its location). Use only when the user invokes deepen by name or asks for \"a deeper version\", \"what would experts do here\", or similar. Never invoke on your own initiative."
---

# deepen

Deeper means each part of the work is aimed at the right target, judged by something other
than anyone's say-so, and carries how the best practitioners would find the solution — never
the solution itself. The deeper version sets up the work that uncovers the answer; it does
not supply the answer. It does not mean more: every added word carries a target, a check, a
way of finding, or a cut.

Canon: `../principles/SKILL.md` — observed / inferred / guessed, and what "verified" means.

## 1. Restate the goal as outcomes, not outputs

"28 tables down to 15" is an output. "The bugs that keep recurring become impossible" is an
outcome. Each outcome names the **oracle** that would judge it — something other than the
user's word or yours.

## 2. Gather evidence before deepening

Look at the real system first: whether the target is still live (retired, superseded,
unused), its history (git log, fix commits, issues), its current measures, and what is missing (no baseline, no scan, a restore never tried). Label each fact
**observed**, **inferred** or **guessed**. Never invent evidence; if something could not be
checked, say so.

Evidence often shows the input is aimed at the wrong target — 124 backend fixes pointing at
the write model, not the table count. When it does, re-aim the work at the target the
evidence supports, and raise the reading you set aside as one of the closing questions. What
you find goes into the deeper version as leads to test, labelled, not as conclusions to act
on: the work that follows confirms or kills them. If the work is moot, the deeper version
closes it, keeping only what is still live. Do not polish the wrong target.

## 3. Bring in the domains the work touches

Each domain below is stated as what true excellence looks like there — the bar a top
0.001% practitioner holds, not the job title. The list is **not exhaustive**, and most work
touches only a few: invoke a domain only when the subject reaches it. A domain not listed
gets the same treatment — name it and state its bar in one line.

| Domain | True excellence |
|---|---|
| **AI-native engineering** | Designs for a codebase that agents write and maintain, where code is nearly free and attention is what's scarce. Builds what others import when owning it buys control, rewrites a hot path in a lower-level language, regenerates rather than patches. Prefers explicit, local, uniform code that an agent can change without holding the whole system in context. |
| **Agents as users** | Knows that in every domain some interactions will be owned wholly by AI agents, and designs for that user too. Every capability an agent needs is a documented, callable tool (an API, an MCP server), not a page to scrape; content states its answer first, in a structure a model cites correctly. Tests it like a human user: an agent given the task cold, watched until it succeeds. |
| **Product** | Ships the smallest change that moves the outcome. Sets an appetite, not an estimate. Says no to most of the backlog, and names in advance the user behaviour that will prove the bet right or wrong. |
| **Engineering** | Ships one line where others ship a thousand. Deletes before adding. Leaves the system with fewer states and fewer paths than it found. |
| **Data integrity** | Makes invalid states unrepresentable. One writer per fact. Every schema change is expand–contract, reversible, and rehearsed on a copy of real data. |
| **Verification** | Every test can fail for a reason a user would care about, and none breaks under a correct refactor. Proves the suite catches the bugs history already produced (defect archaeology, mutation testing, model-based property tests). |
| **Reliability** | Has restored from backup before it was needed. Every change has a rollback that has been tried. Alerts fire on what users feel, not on internals. |
| **Security** | Threat-models (STRIDE) before designing. Removes attack surface rather than guarding it. Least privilege by default; secrets never in code or logs. |
| **Performance** | Measures on real data before touching anything. Sets a budget per user-visible action. Changes the algorithm or the data shape before tuning constants. |
| **Interaction design** | The user finishes the task without reading instructions. Every state is designed: empty, loading, error, partial, and too much. |
| **Visual design** | Hierarchy readable at a glance: one focal point per screen, a type and spacing scale applied without exception, contrast that holds in light and dark. |
| **Accessibility** | Works by keyboard and screen reader the first time, checked with real assistive technology against WCAG, not only a scanner. |
| **Content and docs** | Every word does a job. Docs are organised by what the reader is trying to do (Diátaxis). Every error says what to do next. |
| **User research** | Watches real users attempt real tasks before believing a requirement. Weighs what people do over what they say. |
| **Measurement** | States the hypothesis, the comparison and the decision rule before collecting data. Knows the noise floor — variance and power — before calling any difference real. |
| **Release** | Ships small, dark and reversible: feature flags, staged rollout, a kill switch, and a written condition for rolling back. |

The bar names the kind of result, not the route to it. For each domain invoked, ask one
question: **how would these practitioners find the solution that reaches this kind of result,
here?** Answer it from this situation, not from a fixed procedure, and write down how they
would find it and how they would know they had — never what they would find. The answer is
for your thinking; only what survives §4 reaches the output.

## 4. Filter hard

- Keep an addition only if it changes a decision, catches a failure the input would miss,
  or replaces an assertion with an oracle. Each addition displaces something weaker.
- Cut what the evidence shows the input over-scoped.
- Cut any sentence that states the solution; if it mattered, replace it with how to find it.
- Every item is a recommendation, never a menu.
- **A plan, spec or brief** stays within about 1.2× its word count.
- **A prompt of a few sentences** is short because it leaves out what done looks like, so it
  may grow — but only by the target, the oracle that judges it, what is out of scope, and how
  the answer would be found. Never the answer, and no implementation steps: those are what
  the work uncovers. "The script is too slow, make it faster" deepens to "Find where the time
  actually goes on a real run before changing anything; change only what that points to,
  with every primer identical".

## 5. Hold every unit of work to the bar

If the input is multi-step, each unit gets an acceptance check written first and seen
failing (or a baseline recorded), and replays the earlier units' checks. A claim without
evidence is not done.

## 6. Separate decisions from mechanics

Raise only forks a user would notice: what the product does, what it says, whether it is
worth the cost. Decide everything else and state what you picked in your reply, one line
each.

## Output — same form as the input

- **Plan file:** rewrite it in place. Keep its section structure where it still serves, and
  every decision the user already made.
- **Inline prompt or goal:** reply with the rewritten prompt in a fenced block, then one
  line per change — added, cut or changed — with its reason and evidence label.
- **Artifact or document:** update it at its existing location or URL.
- **Always:** end your reply (not the file) with at most three questions only the user can
  answer, in terms of what the user would see or pay.

Before handing back, check: the form matches the input; the rewrite meets its length rule
above; every addition names its oracle; no sentence states the solution.
