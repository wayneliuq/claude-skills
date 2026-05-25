#!/bin/bash
# PostToolUseFailure hook for strategic-implementation.
# Increments consecutive_failures. When >= 3, sets pending_error_loop flag.
# Reset to 0 happens in hook-bash-counter on successful deliverable commit.

SI_HOOK_INPUT=$(cat)
source "$(dirname "$0")/hook-helpers.sh"

si_is_active || si_noop

si_state_mutate '.consecutive_failures = (.consecutive_failures + 1)'

COUNT=$(si_state_read '.consecutive_failures')
if [[ -n "$COUNT" && "$COUNT" -ge 3 ]]; then
  si_state_mutate '.pending_error_loop = true'
fi

exit 0
