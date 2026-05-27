#!/bin/sh
# Install the code-review-graph freshness post-merge hook machine-wide.
#
# Mechanism (chosen over global core.hooksPath, which is all-or-nothing and
# would hijack every hook type for every repo, silently disabling existing
# per-repo hooks such as axiph's pre-commit):
#   1. Per-repo: copy the post-merge hook into each target repo's .git/hooks/,
#      APPEND-ONLY — never overwrite a foreign hook.
#   2. Future clones: set git init.templateDir so new repos are seeded with it.
#
# Usage:
#   install-graph-freshness-hooks.sh [REPO ...]      # install into given repos
#   install-graph-freshness-hooks.sh                 # scan $CRG_REPO_BASE (default ~/Documents/Development)
#   install-graph-freshness-hooks.sh --uninstall     # remove our hook + unset template
#
# Idempotent. Safe to re-run.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC_HOOK="$SCRIPT_DIR/git-hooks/post-merge"
MARKER="code-review-graph freshness"
TEMPLATE_DIR="${CRG_TEMPLATE_DIR:-$HOME/.config/git/template}"
REPO_BASE="${CRG_REPO_BASE:-$HOME/Documents/Development}"

[ -f "$SRC_HOOK" ] || { echo "FATAL: canonical hook not found at $SRC_HOOK" >&2; exit 1; }

is_ours() { grep -q "$MARKER" "$1" 2>/dev/null; }

install_into_repo() {
  repo="$1"
  hooks_dir="$repo/.git/hooks"
  [ -d "$repo/.git" ] || { echo "skip   $repo (not a git repo)"; return; }
  mkdir -p "$hooks_dir"
  dest="$hooks_dir/post-merge"
  if [ -e "$dest" ] && ! is_ours "$dest"; then
    echo "WARN   $repo: foreign post-merge hook present — NOT overwriting. Merge manually if needed."
    return
  fi
  cp "$SRC_HOOK" "$dest"
  chmod +x "$dest"
  echo "ok     $repo (post-merge installed/refreshed)"
}

uninstall() {
  echo "Uninstalling..."
  git config --global --unset init.templateDir 2>/dev/null || true
  [ -f "$TEMPLATE_DIR/hooks/post-merge" ] && rm -f "$TEMPLATE_DIR/hooks/post-merge"
  for repo in "$@"; do
    dest="$repo/.git/hooks/post-merge"
    if [ -e "$dest" ] && is_ours "$dest"; then rm -f "$dest"; echo "removed $repo/.git/hooks/post-merge"; fi
  done
  echo "Done. (Foreign hooks left untouched.)"
}

# --- seed future clones via init.templateDir ---
setup_template() {
  mkdir -p "$TEMPLATE_DIR/hooks"
  cp "$SRC_HOOK" "$TEMPLATE_DIR/hooks/post-merge"
  chmod +x "$TEMPLATE_DIR/hooks/post-merge"
  git config --global init.templateDir "$TEMPLATE_DIR"
  echo "template: future clones seeded via init.templateDir=$TEMPLATE_DIR"
}

# --- resolve target repos ---
collect_targets() {
  if [ "$#" -gt 0 ]; then
    for r in "$@"; do printf '%s\n' "$r"; done
  else
    for d in "$REPO_BASE"/*/.git; do [ -d "$d" ] && printf '%s\n' "$(dirname "$d")"; done
  fi
}

case "${1:-}" in
  --uninstall)
    shift
    # shellcheck disable=SC2046
    uninstall $(collect_targets "$@")
    exit 0 ;;
esac

setup_template
collect_targets "$@" | while IFS= read -r repo; do install_into_repo "$repo"; done

cat <<EOF

Done. Rollback / uninstall:
  $0 --uninstall
  (removes only OUR post-merge hooks + unsets init.templateDir; foreign hooks untouched)

Note: companion ~/.claude/settings.json hooks (SessionStart full build, PostToolUse
all-tools matcher) are documented in the graph-freshness setup-and-findings.md.
EOF
