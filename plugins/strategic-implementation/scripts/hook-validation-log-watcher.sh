#!/bin/bash
# FileChanged(validation-log.md) hook for strategic-implementation.
# When the validation log gains a new ⚠️ REVISION NEEDED line or a DEV-NNN
# of type blocker, sets pending_deviation_surface flag so the Stop orchestrator
# nudges the agent on the next turn.

SI_HOOK_INPUT=$(cat)
source "$(dirname "$0")/hook-helpers.sh"

si_is_active || si_noop

FEATURE_FOLDER=$(si_state_read '.feature_folder')
[[ -z "$FEATURE_FOLDER" ]] && si_noop

LOG="$(si_cwd)/$FEATURE_FOLDER/validation-log.md"
[[ -f "$LOG" ]] || si_noop

# Cheap last-mtime compare to avoid re-processing the same write.
MTIME=$(stat -f '%m' "$LOG" 2>/dev/null || stat -c '%Y' "$LOG" 2>/dev/null || echo 0)
LAST_MTIME=$(si_state_read '.validation_log_last_mtime')
[[ "$MTIME" = "$LAST_MTIME" ]] && si_noop
si_state_mutate ".validation_log_last_mtime = \"$MTIME\""

# Surface only on high-signal additions, not every append.
LAST_LINES=$(tail -50 "$LOG")
if echo "$LAST_LINES" | grep -qE "⚠️ REVISION NEEDED|\*\*Type:\*\* blocker|\*\*Type:\*\* error-loop-escalation"; then
  si_state_mutate '.pending_deviation_surface = true'
fi

exit 0
