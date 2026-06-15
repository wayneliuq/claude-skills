#!/bin/bash
# PostToolUse(Bash) hook for strategic-implementation.
# Detects atomic deliverable commits (subjects matching `^D[0-9]+: `) and resets
# the error-loop counter (consecutive_failures) on confirmed progress.
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

# Bail if this commit was already counted (idempotent against the same HEAD).
LAST_COUNTED=$(si_state_read '.last_counted_sha')
HEAD_SHA=$(cd "$CWD" && git rev-parse HEAD 2>/dev/null || echo "")
[[ "$LAST_COUNTED" = "$HEAD_SHA" ]] && si_noop

# Confirmed deliverable progress → reset the error-loop counter so it does not
# carry stale failures across deliverables.
si_state_mutate "
  .last_counted_sha = \"$HEAD_SHA\"
  | .consecutive_failures = 0
"

exit 0
