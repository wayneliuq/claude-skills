#!/usr/bin/env bash
# store.sh — the GitHub-backed artifact store adapter (spec §6).
# Records are markdown files at <repo-id>/<date-slug>/<artifact-name> in the shared store repo.
#
# Subcommands:
#   store.sh read  <address> [--handle-out <file>]
#   store.sh write <address> <file> [--handle-in <handle>] [--handle-out <file>]
#   store.sh list  <prefix>
#   store.sh --capabilities
#
# The version-handle is OPAQUE to callers (internally a git blob SHA). Best-effort conflict:
# a write whose --handle-in no longer matches the stored handle is SURFACED (exit 3), not applied.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$HERE/common.sh"

STORE_REPO="$(si_locator_field repo 2>/dev/null || true)"; STORE_REPO="${STORE_REPO:-$STORE_REPO_DEFAULT}"
STORE_BRANCH="$(si_locator_field branch 2>/dev/null || true)"; STORE_BRANCH="${STORE_BRANCH:-$STORE_BRANCH_DEFAULT}"

die() { echo "[store] $*" >&2; exit 1; }
need_gh() { gh_ok || die "gh unavailable/unauthenticated/offline"; }

cmd="${1:-}"; shift || true

case "$cmd" in
  --capabilities)
    echo "conflict-surfacing: yes"
    echo "bulk-migration: trivial"
    echo "raw-markdown: yes"
    ;;

  read)
    addr="${1:-}"; shift || true
    handle_out=""
    while [ $# -gt 0 ]; do case "$1" in --handle-out) handle_out="$2"; shift 2;; *) die "read: bad arg $1";; esac; done
    [ -n "$addr" ] || die "read: missing <address>"
    assert_valid_address "$addr" || exit 1
    need_gh
    # body: raw bytes (no base64 reassembly) — byte-identical round-trip
    if ! gh api -H "Accept: application/vnd.github.raw" "repos/$STORE_REPO/contents/$addr?ref=$STORE_BRANCH" 2>/dev/null; then
      die "read: not found ($addr)"
    fi
    # handle: the file's git blob sha (opaque)
    if [ -n "$handle_out" ]; then
      gh api "repos/$STORE_REPO/contents/$addr?ref=$STORE_BRANCH" --jq .sha 2>/dev/null > "$handle_out" || true
    fi
    ;;

  write)
    addr="${1:-}"; file="${2:-}"; shift 2 2>/dev/null || true
    handle_in=""; handle_out=""
    while [ $# -gt 0 ]; do case "$1" in
      --handle-in) handle_in="$2"; shift 2;;
      --handle-out) handle_out="$2"; shift 2;;
      *) die "write: bad arg $1";; esac
    done
    [ -n "$addr" ] && [ -n "$file" ] || die "write: usage write <address> <file>"
    [ -f "$file" ] || die "write: no such file $file"
    assert_valid_address "$addr" || exit 1
    need_gh
    assert_no_secret warn "$(cat "$file")"   # warn (don't block) on record bodies — spec §10
    # current stored handle (empty => create)
    current="$(gh api "repos/$STORE_REPO/contents/$addr?ref=$STORE_BRANCH" --jq .sha 2>/dev/null || true)"
    # best-effort optimistic concurrency: surface stale-handle conflict before writing
    if [ -n "$handle_in" ] && [ "$handle_in" != "$current" ]; then
      echo "[store] conflict: stale handle for $addr (supplied=$handle_in current=${current:-<none>})" >&2
      exit 3
    fi
    b64="$(base64 < "$file" | tr -d '\n')"
    payload="$(jq -n --arg m "store: write $addr" --arg c "$b64" --arg b "$STORE_BRANCH" --arg s "$current" \
      'if $s == "" then {message:$m, content:$c, branch:$b} else {message:$m, content:$c, branch:$b, sha:$s} end')"
    # new handle from the PUT response (authoritative — avoids read-after-write GET staleness)
    newsha="$(printf '%s' "$payload" | gh api -X PUT "repos/$STORE_REPO/contents/$addr" --input - --jq .content.sha 2>/dev/null || true)"
    [ -n "$newsha" ] || die "write: PUT failed for $addr"
    if [ -n "$handle_out" ]; then printf '%s\n' "$newsha" > "$handle_out"; else echo "[store] handle=$newsha" >&2; fi
    ;;

  put)
    # Fallback-safe write (transition wiring): store the record, or write the in-repo fallback so
    # a record is NEVER dropped. A surfaced CONFLICT (exit 3) is propagated, not fallen back.
    #   store.sh put <address> <fallback-path> <file> [--handle-in <h>] [--handle-out <h>]
    addr="${1:-}"; fallback="${2:-}"; file="${3:-}"; shift 3 2>/dev/null || true
    [ -n "$addr" ] && [ -n "$fallback" ] && [ -f "${file:-}" ] || die "put: usage put <address> <fallback-path> <file> [...]"
    assert_valid_address "$addr" || exit 1
    _fallback() { mkdir -p "$(dirname "$fallback")"; cp "$file" "$fallback"; echo "[store] FALLBACK → in-repo $fallback ($1)" >&2; exit 0; }
    if ! gh_ok || ! si_locator_exists; then _fallback "no gh/locator"; fi
    bash "$0" write "$addr" "$file" "$@"; rc=$?
    case "$rc" in
      0) exit 0 ;;
      3) exit 3 ;;                 # conflict surfaced — do NOT fall back (would mask the conflict)
      *) _fallback "store write failed (rc=$rc)" ;;
    esac
    ;;

  list)
    prefix="${1:-}"; shift || true
    [ -n "$prefix" ] || die "list: missing <prefix>"
    assert_valid_address "$prefix" || exit 1
    need_gh
    # contents on a dir → array of entries; 404 (never-written feature) → empty set (spec §6.1).
    # ≤1000 entries; beyond, a git-trees recursive fallback would be needed (defined ceiling).
    # Capture first: on HTTP error gh prints the error body to stdout — must NOT leak it as a "listing".
    local_out="$(gh api "repos/$STORE_REPO/contents/$prefix?ref=$STORE_BRANCH" 2>/dev/null)" || exit 0
    printf '%s' "$local_out" | jq -r '.[]?.path // empty' 2>/dev/null || true
    ;;

  *)
    die "usage: store.sh {read|write|list|--capabilities} ..."
    ;;
esac
