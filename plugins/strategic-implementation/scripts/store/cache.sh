#!/usr/bin/env bash
# cache.sh — read-through local mirror of the active feature's records (spec §8).
# Derived, disposable, git-ignored-by-location (lives under the user cache dir, OUTSIDE any
# worktree). Never the source of truth; re-hydratable from the store at any time.
#
#   cache.sh hydrate <date-slug>          # fetch the active feature's records into the cache
#   cache.sh refresh <address> <body>     # best-effort: seed one record's mirror from a known body
#   cache.sh path [<date-slug>]           # print the cache dir (for the human to open in an editor)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$HERE/common.sh"
STORE="$HERE/store.sh"

cache_root() { printf '%s/strategic-artifacts/%s' "${XDG_CACHE_HOME:-$HOME/.cache}" "$(si_repo_id)"; }

# Write $1 (a file already at $2) into the cache at the address's repo-relative path,
# asserting the resolved path stays inside the cache root (realpath containment).
_cache_put() {
  local addr="$1" src="$2" root rel dest destdir canon_root canon_dir
  root="$(cache_root)"; mkdir -p "$root"
  canon_root="$(cd "$root" && pwd -P)"
  rel="${addr#"$(si_repo_id)"/}"          # strip the repo-id namespace segment
  dest="$root/$rel"; destdir="$(dirname "$dest")"
  mkdir -p "$destdir" 2>/dev/null || { echo "[cache] cannot mkdir $destdir" >&2; return 1; }
  canon_dir="$(cd "$destdir" && pwd -P)"
  case "$canon_dir/" in
    "$canon_root"/*) : ;;
    *) echo "[cache] containment violation for $addr — refusing" >&2; return 1 ;;
  esac
  cp "$src" "$dest"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  hydrate)
    slug="${1:-}"; [ -n "$slug" ] || { echo "[cache] hydrate: missing <date-slug>" >&2; exit 0; }  # no-op, not fatal
    gh_ok || { echo "[cache] gh unavailable — skipping hydrate (degrade-to-silence)" >&2; exit 0; }
    rid="$(si_repo_id)"; prefix="$rid/$slug"
    tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
    n=0
    while IFS= read -r addr; do
      [ -n "$addr" ] || continue
      if bash "$STORE" read "$addr" > "$tmp/body" 2>/dev/null; then
        _cache_put "$addr" "$tmp/body" && n=$((n+1))
      fi
    done < <(bash "$STORE" list "$prefix" 2>/dev/null)
    echo "[cache] hydrated $n record(s) for $slug → $(cache_root)/$slug"
    ;;
  refresh)
    addr="${1:-}"; body="${2:-}"
    [ -n "$addr" ] && [ -f "$body" ] || { echo "[cache] refresh: usage refresh <address> <body-file>" >&2; exit 0; }
    _cache_put "$addr" "$body" || exit 0   # best-effort
    ;;
  path)
    slug="${1:-}"
    if [ -n "$slug" ]; then printf '%s/%s\n' "$(cache_root)" "$slug"; else printf '%s\n' "$(cache_root)"; fi
    ;;
  session)
    # SessionStart entrypoint. Resolve the active feature from hook state; no active feature → clean no-op.
    # --background forks a detached worker and returns instantly so session start never blocks (mirrors refresh.sh).
    bg=""; [ "${1:-}" = "--background" ] && bg=1
    st="$(si_repo_root)/.claude/strategic-implementation/state.json"
    [ -f "$st" ] || exit 0
    [ "$(jq -r '.active // false' "$st" 2>/dev/null)" = "true" ] || exit 0
    ff="$(jq -r '.feature_folder // ""' "$st" 2>/dev/null)"; [ -n "$ff" ] || exit 0
    slug="$(basename "$ff")"
    if [ -n "$bg" ]; then nohup bash "$0" hydrate "$slug" >/dev/null 2>&1 & exit 0; fi
    exec bash "$0" hydrate "$slug"
    ;;
  *)
    echo "usage: cache.sh {hydrate <date-slug>|refresh <address> <body>|path [<date-slug>]|session [--background]}" >&2; exit 2 ;;
esac
