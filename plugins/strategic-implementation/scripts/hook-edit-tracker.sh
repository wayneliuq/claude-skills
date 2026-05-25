#!/bin/bash
# PostToolUse(Edit|Write) hook for strategic-implementation.
# Tracks per-file edit counts within the current deliverable. On the 4th edit
# to the same file, sets pending_thrash_pause flag for the Stop orchestrator
# to surface as guidance on the next turn. Counts reset when bash-counter
# detects a deliverable commit.

SI_HOOK_INPUT=$(cat)
source "$(dirname "$0")/hook-helpers.sh"

si_is_active || si_noop

FILE=$(printf '%s' "$SI_HOOK_INPUT" | jq -r '.tool_input.file_path // empty')
[[ -z "$FILE" ]] && si_noop

# Normalize to repo-relative path for stable counting across editors.
CWD=$(si_cwd)
case "$FILE" in
  "$CWD"/*) FILE="${FILE#$CWD/}" ;;
esac

# Atomic per-file increment.
si_state_mutate "
  .current_deliverable_edit_counts[\"$FILE\"] =
    ((.current_deliverable_edit_counts[\"$FILE\"] // 0) + 1)
"

COUNT=$(si_state_read ".current_deliverable_edit_counts[\"$FILE\"]")
if [[ -n "$COUNT" && "$COUNT" -gt 3 ]]; then
  si_state_mutate ".pending_thrash_pause = \"$FILE\""
fi

exit 0
