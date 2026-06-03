#!/usr/bin/env bash
# common.sh — shared primitives for the externalized artifact store adapter.
# Sourced by bootstrap.sh / store.sh / cache.sh. No secret is ever echoed or written.
# House style: set -uo pipefail in callers; functions here avoid `set -e` surprises.
set -uo pipefail

# --- store target defaults (the chosen execution target; recorded in the locator) ---
STORE_REPO_DEFAULT="wayneliuq/strategic-artifacts"
STORE_BRANCH_DEFAULT="main"

# --- repo root ---
si_repo_root() { git rev-parse --show-toplevel 2>/dev/null; }

# --- repo-id: slug of the origin remote (owner-repo), normalized across ssh/https,
#     trailing .git stripped; frozen into the locator at bootstrap.
#     No origin → deterministic fallback (basename of repo root) + warn. Never crashes.
si_repo_id() {
  local url cleaned
  url="$(git remote get-url origin 2>/dev/null)"
  if [ -z "$url" ]; then
    local root; root="$(si_repo_root)"
    echo "[store] WARN: no origin remote; using repo dir name as repo-id" >&2
    printf '%s' "$(basename "${root:-$PWD}")" | _si_slug
    return 0
  fi
  # Normalize: git@github.com:owner/repo(.git) | https://github.com/owner/repo(.git) | ssh://git@host/owner/repo
  cleaned="${url%.git}"
  cleaned="$(printf '%s' "$cleaned" | sed -E 's#^(git@|ssh://git@|https?://)##; s#github\.com[:/]##')"
  printf '%s' "$cleaned" | _si_slug   # -> owner-repo
}

# slug: lowercase, non-alnum → '-', squeeze, trim.
_si_slug() { tr '[:upper:]' '[:lower:]' | sed -E 's#[^a-z0-9]+#-#g; s#^-+##; s#-+$##'; }

# --- locator ---
si_locator_path() { printf '%s/docs/strategic-implementation/store-locator.yaml' "$(si_repo_root)"; }
si_locator_exists() { [ -f "$(si_locator_path)" ]; }
# read a top-level or nested scalar by leaf key (simple yaml; values are plain scalars)
si_locator_field() {
  local key="$1" f; f="$(si_locator_path)"
  [ -f "$f" ] || return 1
  sed -nE "s/^[[:space:]]*${key}:[[:space:]]*\"?([^\"#]+)\"?[[:space:]]*$/\1/p" "$f" | head -1 | sed -E 's/[[:space:]]+$//'
}

# --- gh availability (auth + network), degrade-to-silence; never echoes the token ---
gh_ok() {
  command -v gh >/dev/null 2>&1 || return 1
  gh auth status >/dev/null 2>&1 || return 1
  gh api rate_limit >/dev/null 2>&1 || return 1   # lightweight network probe
  return 0
}

# --- address validation: <repo-id>/<date-slug>/<artifact-name>, no traversal/metachars.
#     Reject anything that could escape the namespace on the wire or the cache on disk.
assert_valid_address() {
  local addr="$1" seg
  case "$addr" in
    /*) echo "[store] invalid address (leading slash): $addr" >&2; return 1 ;;
    *//*) echo "[store] invalid address (empty segment): $addr" >&2; return 1 ;;
    *$'\n'*|*$'\t'*) echo "[store] invalid address (control char)" >&2; return 1 ;;
  esac
  # at least 2 segments
  case "$addr" in */*) : ;; *) echo "[store] invalid address (need <repo-id>/.../<name>): $addr" >&2; return 1 ;; esac
  local IFS=/
  for seg in $addr; do
    [ -n "$seg" ] || { echo "[store] invalid address (empty segment)" >&2; return 1; }
    [ "$seg" = "." ] && { echo "[store] invalid address ('.')" >&2; return 1; }
    [ "$seg" = ".." ] && { echo "[store] invalid address ('..')" >&2; return 1; }
    case "$seg" in
      *[!A-Za-z0-9._-]*) echo "[store] invalid address (illegal char in '$seg')" >&2; return 1 ;;
    esac
  done
  return 0
}

# --- secret scan. mode=block → nonzero on hit; mode=warn → log only, return 0.
#     Patterns: GitHub tokens, AWS keys, PEM, Authorization/Bearer, long high-entropy runs.
assert_no_secret() {
  local mode="$1" text="$2" hit=""
  if printf '%s' "$text" | grep -Eq \
    'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(Authorization|Bearer)[: ]+[A-Za-z0-9._-]{20,}|[A-Za-z0-9+/]{40,}={0,2}'
  then
    hit="yes"
  fi
  if [ -n "$hit" ]; then
    if [ "$mode" = "block" ]; then
      echo "[store] SECRET DETECTED — refusing to write (locator/secret guard)" >&2
      return 1
    else
      echo "[store] WARN: possible secret in record body (write proceeding; review)" >&2
      return 0
    fi
  fi
  return 0
}
