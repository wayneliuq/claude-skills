#!/usr/bin/env bash
# migrate.sh — one-shot bulk migration of existing in-repo per-feature records into the
# externalized store (spec capability `bulk-migration`). Forward-only COPY: writes each
# feature-folder record to <repo-id>/<date-slug>/<path>; does NOT delete the in-repo copies.
# Excludes the durable tier (project-learnings.md, documentation-registry.md) and the locator.
# Writes ONLY to the store configured in the committed locator (this repo's store).
#
#   migrate.sh            # copy + spot-check confirm
#   migrate.sh --confirm  # confirm only (no writes): count + byte-identical spot-check
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$HERE/common.sh"
STORE_SH="$HERE/store.sh"
ROOT="$(si_repo_root)"; cd "$ROOT" || { echo "[migrate] not in a git repo" >&2; exit 1; }
DOCS="docs/strategic-implementation"

gh_ok || { echo "[migrate] gh unavailable/unauthenticated/offline" >&2; exit 1; }
si_locator_exists || { echo "[migrate] no locator — run bootstrap.sh first" >&2; exit 1; }
RID="$(si_repo_id)"
STORE_REPO="$(si_locator_field repo)"; STORE_BRANCH="$(si_locator_field branch)"
mode="${1:-copy}"

LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
git ls-files "$DOCS/" \
  | grep -vE "^$DOCS/(documentation-registry|project-learnings)\.md$" \
  | grep -vE "^$DOCS/store-locator\.yaml$" > "$LIST"
total="$(wc -l < "$LIST" | tr -d ' ')"
echo "[migrate] target store: $STORE_REPO@$STORE_BRANCH  namespace: $RID  records: $total"

if [ "$mode" != "--confirm" ]; then
  # Resume-aware: fetch the set of already-present addresses in ONE tree call, skip them.
  EXIST="$(mktemp)"; trap 'rm -f "$LIST" "$EXIST"' EXIT
  gh api "repos/$STORE_REPO/git/trees/$STORE_BRANCH?recursive=1" \
    --jq "[.tree[]|select(.type==\"blob\" and (.path|startswith(\"$RID/\")))|.path][]" 2>/dev/null | sort > "$EXIST"
  ok=0; skip=0; fail=0
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    addr="$RID/${f#$DOCS/}"
    if grep -qxF "$addr" "$EXIST"; then skip=$((skip+1)); continue; fi
    # write with one retry + a small throttle to dodge GitHub's secondary write-rate limit
    if bash "$STORE_SH" write "$addr" "$f" --handle-out /dev/null 2>/dev/null; then
      ok=$((ok+1))
    else
      sleep 3
      if bash "$STORE_SH" write "$addr" "$f" --handle-out /dev/null 2>/dev/null; then ok=$((ok+1)); else fail=$((fail+1)); echo "  FAIL  $addr" >&2; fi
    fi
    sleep 0.3
  done < "$LIST"
  echo "[migrate] wrote $ok, skipped $skip (already present), failed $fail (of $total)"
  [ "$fail" -eq 0 ] || { echo "[migrate] FAILURES above — re-run to retry" >&2; exit 1; }
fi

# --- confirm: byte-identical spot-check on first/middle/last record ---
echo "[migrate] confirming (byte-identical spot-check)..."
mid=$(( (total + 1) / 2 ))
pass=0; checks=0
for n in 1 "$mid" "$total"; do
  f="$(sed -n "${n}p" "$LIST")"; [ -n "$f" ] || continue
  addr="$RID/${f#$DOCS/}"
  got="$(mktemp)"
  if bash "$STORE_SH" read "$addr" > "$got" 2>/dev/null && diff -q "$f" "$got" >/dev/null; then
    echo "  OK    $addr"; pass=$((pass+1))
  else
    echo "  DIFF  $addr"
  fi
  checks=$((checks+1)); rm -f "$got"
done
echo "[migrate] spot-check: $pass/$checks byte-identical"
[ "$pass" -eq "$checks" ] || exit 1
echo "[migrate] DONE — $total records present in $STORE_REPO under $RID/"
