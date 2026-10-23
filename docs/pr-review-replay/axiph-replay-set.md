# pr-review replay set (axiph)

Real bugs that shipped inside a reviewed axiph change, each with the commit that introduced it and the commit that fixed it. Use it to measure whether a review (or a second-look lane) would have caught them.

**Replay a case:** `git worktree add --detach <dir> <introducer>` in axiph, then review `git show <introducer>` with the repo at that commit readable. **Caught** = a finding that names the same user-visible wrong result as the fix's subject. Introducers were found by blaming the lines each fix changed (most-blamed commit), except E2, whose fix message names it.

| id | finder | introducer | fix | size of introducer | the bug, as the fix states it |
|---|---|---|---|---|---|
| E1 | escape (5 follow-up fixes in #987, 2 more in #1040) | `d65e96836` | `f90395fc7` | 27, 1474, 6 | fix(feedback): a feedback report never carries a sign-in token or cookie from a recent error |
| E2 | escape (sibling readers missed in #844, fixed in #987) | `436cbad98` | `a85ddff8a` | 15, 628, 65 | fix(box): on a log axis every box arm reads only the positive values |
| S1 | second look | `1bc9653b9` | `15ccbb492` | 7, 103, 10 | fix(results): a result table saved while you were in another project stops reading Saving |
| S2 | second look | `843b077bd` | `da3b3e179` | 16, 244, 146 | fix(stats): a number column that also groups the figure stays numbers; paired lines follow the figure's order |
| S3 | second look | `5edba6d9b` | `55352d327` | 5, 51, 16 | fix(plots): a point whose shape cell is blank wears no level's shape |
| S4 | second look | `1f452a162` | `316a4e5c9` | 8, 51, 14 | fix(stats): a run's record names DuckDB only when DuckDB read its table |
| W1 | in-app sweep | `68ef3adcf` | `4c76d66ee` | 5, 276, 16 | fix(plots): a date axis whose ticks share a month tells them apart by day |
| W2 | in-app sweep | `c8c51586a` | `fcd73ecd7` | 2, 79, 4 | fix(plots): a paired comparison's subject lines end on their own dots |
| W3 | in-app sweep | `341141b9b` | `1ceabdf39` | 2, 14, 1 | fix(stats): a ROC curve's label reads "CRP AUC = 0.84", not "CRP AUC AUC = 0.84" |
| W4 | in-app sweep | `f6a350975` | `501b343c0` | 6, 153, 43 | fix(stats): a p-value below the floor reads "p < 1 × 10⁻⁹", not "p = < 1 × 10⁻⁹" |
| W5 | in-app sweep | `8d2416996` | `a458c18b4` | 3, 48, 6 | fix(plots): a line joins its points left to right, on a number, a date or categories |
| W6 | in-app sweep | `46c13779a` | `296d0dcd5` | 3, 53, 1 | fix(plots): a size or a shape is not held where no row draws every value |

Size is files, lines added, lines removed. Built 2026-10-23 from the commit history of axiph #844 and #987.
