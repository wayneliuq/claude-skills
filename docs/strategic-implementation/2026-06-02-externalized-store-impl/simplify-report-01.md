# Simplify report 01 — externalized-store-impl
_Target ref: `3d5e4c4...HEAD` (store adapter scripts) · Date: 2026-06-02 · Mode: graph-aware + read_

## Summary
- Files scanned: 4 (`common.sh`, `bootstrap.sh`, `store.sh`, `cache.sh`) + setup.sh/hooks.json edits
- Findings: 4 (high: 0, med: 1, low: 3)
- Categories: reuse-miss 0, dead-code 2, comment-hygiene 0, shape/naming 2

## Findings

### F-01 — dead-code — med — `si_locator_exists()` has zero callers
**File:** `plugins/strategic-implementation/scripts/store/common.sh`
**Symbol / region:** `si_locator_exists()`
**Why:** defined but unused; `bootstrap.sh` checks `[ -f "$LOC" ]` directly. `query_graph callers_of` → none.
**Suggested action:** keep — D4's routing convention needs a "locator present?" predicate; wire callers there, else remove.

<!-- pm-disposition: defer -->

### F-02 — dead-code — low — `cache.sh refresh` and `store.sh --capabilities` have no in-repo callers yet
**File:** `plugins/strategic-implementation/scripts/store/cache.sh`, `store.sh`
**Symbol / region:** `refresh` subcommand; `--capabilities`
**Why:** zero callers in-repo today. `refresh` is the post-write mirror seed the D4 rewiring will call; `--capabilities` is an external-API surface (spec §6.5). Intentional, not removable.
**Suggested action:** none now; `refresh` gains its caller in D4.

<!-- pm-disposition: dismiss -->

### F-03 — shape/naming — low — `si_` prefix applied inconsistently
**File:** `plugins/strategic-implementation/scripts/store/common.sh`
**Symbol / region:** `gh_ok`, `assert_valid_address`, `assert_no_secret` (unprefixed) vs `si_repo_root`/`si_repo_id`/`si_locator_*`
**Why:** mixed convention — `si_`-prefixed accessors alongside unprefixed verbs. Readable, but not uniform.
**Suggested action:** acceptable — the unprefixed names are public "verbs" shared across the suite; leave as-is.

<!-- pm-disposition: dismiss -->

### F-04 — shape/naming — low — `local_out` var name in `store.sh list`
**File:** `plugins/strategic-implementation/scripts/store/store.sh`
**Symbol / region:** `local_out` (the `list` capture var)
**Why:** named `local_out` to avoid the `local` keyword outside a function (the case branch isn't a function); reads oddly.
**Suggested action:** cosmetic; rename to `listing` if touched again. Not worth a dedicated edit.

<!-- pm-disposition: dismiss -->
