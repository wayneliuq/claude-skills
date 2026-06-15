#!/bin/bash
# PostToolUse(Bash) hook for strategic-implementation.
# Detects atomic deliverable commits (subjects matching `^D[0-9]+: `) and
# updates the per-feature counters in state.json:
#   - deliverables_since_last_simplify (increment)
#   - loc_since_last_simplify (estimate from git diff stat of the commit)
# Sets flag pending_simplify when simplify thresholds are crossed.
# No-ops silently when no feature is active.

SI_HOOK_INPUT=$(cat)
source "$(dirname "$0")/hook-helpers.sh"

si_is_active || si_noop

COMMAND=$(printf '%s' "$SI_HOOK_INPUT" | jq -r '.tool_input.command // empty')
# Only act on git commit calls. Don't try to be clever; subject parsing comes from git itself.
case "$COMMAND" in
  *"git commit"*|*"git -c"*"commit"*) : ;;
  *) si_noop ;;
esac

# Pull subject from HEAD instead of parsing $COMMAND — handles heredocs, -m, -F, --amend, etc.
CWD=$(si_cwd)
SUBJECT=$(cd "$CWD" && git log -1 --format='%s' 2>/dev/null || true)
[[ -z "$SUBJECT" ]] && si_noop

# Match `D<n>:` (deliverable commit). Note: heredoc commits land the same.
DLV=$(echo "$SUBJECT" | sed -nE 's/^(D[0-9]+):.*/\1/p')
[[ -z "$DLV" ]] && si_noop

# LOC delta for this commit, excluding the feature folder itself (mirrors executing-plans Step 2f).
FEATURE_FOLDER=$(si_state_read '.feature_folder')
LOC_DELTA=0
if [[ -n "$FEATURE_FOLDER" ]]; then
  LOC_DELTA=$(cd "$CWD" && git show --numstat --format= HEAD 2>/dev/null \
    | awk -v ff="$FEATURE_FOLDER" '$3 !~ "^"ff"/" {s+=$1+$2} END{print s+0}')
else
  LOC_DELTA=$(cd "$CWD" && git show --numstat --format= HEAD 2>/dev/null \
    | awk '{s+=$1+$2} END{print s+0}')
fi

# Bail if this commit was already counted (idempotent against the same HEAD).
LAST_COUNTED=$(si_state_read '.last_counted_sha')
HEAD_SHA=$(cd "$CWD" && git rev-parse HEAD 2>/dev/null || echo "")
[[ "$LAST_COUNTED" = "$HEAD_SHA" ]] && si_noop

# Update counters + last_counted_sha.
si_state_mutate "
  .deliverables_since_last_simplify = (.deliverables_since_last_simplify + 1)
  | .loc_since_last_simplify = (.loc_since_last_simplify + $LOC_DELTA)
  | .last_counted_sha = \"$HEAD_SHA\"
  | .current_deliverable_edit_counts = {}
  | .consecutive_failures = 0
"

# Re-read updated counters and set the deterministic flags.
SIMPLIFY_DELIVERABLES=$(si_state_read '.simplify_thresholds.deliverables')
SIMPLIFY_LOC=$(si_state_read '.simplify_thresholds.loc')
DSINCE=$(si_state_read '.deliverables_since_last_simplify')
LSINCE=$(si_state_read '.loc_since_last_simplify')

# Simplify trigger?
if [[ -n "$DSINCE" && -n "$SIMPLIFY_DELIVERABLES" && "$DSINCE" -ge "$SIMPLIFY_DELIVERABLES" ]] \
  || [[ -n "$LSINCE" && -n "$SIMPLIFY_LOC" && "$LSINCE" -ge "$SIMPLIFY_LOC" ]]; then
  si_state_mutate '.pending_simplify = true'
fi

exit 0
