#!/bin/bash
# Shared helpers for strategic-implementation hooks.
# Source this from each hook script. Provides state read/write and is-active guards.
# Portable to macOS bash 3.2; no flock, no bash-4 features.

set -uo pipefail

# State file location is project-scoped. CWD is provided in hook stdin JSON.
si_state_dir() { echo "${1}/.claude/strategic-implementation"; }
si_state_file() { echo "$(si_state_dir "$1")/state.json"; }

# Each hook script MUST set SI_HOOK_INPUT at the top before sourcing helpers:
#   SI_HOOK_INPUT=$(cat); source "$(dirname "$0")/hook-helpers.sh"
# Subshell-based caching does not work; stdin is single-pass.
si_read_stdin() { printf '%s' "${SI_HOOK_INPUT:-}"; }

# Extract cwd from hook stdin. Falls back to $PWD if missing.
si_cwd() {
  local cwd
  cwd=$(printf '%s' "${SI_HOOK_INPUT:-}" | jq -r '.cwd // empty' 2>/dev/null)
  if [[ -z "$cwd" ]]; then cwd="$PWD"; fi
  echo "$cwd"
}

# Returns 0 if a feature is active, 1 otherwise.
si_is_active() {
  local f
  f=$(si_state_file "$(si_cwd)")
  [[ -f "$f" ]] || return 1
  [[ "$(jq -r '.active // false' "$f" 2>/dev/null)" = "true" ]]
}

# Atomic state mutation: si_state_mutate '<jq expression>'
si_state_mutate() {
  local f tmp expr
  expr="$1"
  f=$(si_state_file "$(si_cwd)")
  [[ -f "$f" ]] || return 1
  tmp="${f}.tmp.$$"
  if jq "$expr" "$f" > "$tmp" 2>/dev/null; then
    mv "$tmp" "$f"
  else
    rm -f "$tmp"
    return 1
  fi
}

# Read a state field: si_state_read '.field.subfield'
si_state_read() {
  local f
  f=$(si_state_file "$(si_cwd)")
  [[ -f "$f" ]] || return 1
  jq -r "$1 // empty" "$f" 2>/dev/null
}

# Emit a no-op stop-hook decision and exit 0.
si_noop_stop() { echo '{"ok": true}'; exit 0; }

# Emit a no-op generic hook (exits 0 silently).
si_noop() { exit 0; }
