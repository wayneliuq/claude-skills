#!/bin/bash
# Stop hook (command-type) for strategic-implementation.
# Reads state.json, collects any pending deterministic triggers, and either
#   - returns {"ok": false, "reason": "<consolidated guidance>"} so the agent
#     continues the next turn with the guidance injected, or
#   - returns {"ok": true} so the agent stops normally.
#
# Triggers handled (deterministic, harness-fired, no model judgment):
#   pending_simplify          → instruct invocation of strategic-implementation:simplify
#   pending_thrash_pause      → instruct re-read of brief before further edits to <file>
#   pending_error_loop        → instruct escalation to post-execution:triage
#   pending_deviation_surface → instruct surfacing of last validation-log entry
#
# When a flag is pending this hook fires {ok:false} with the consolidated guidance
# so the agent continues next turn; otherwise it allows a normal stop.

SI_HOOK_INPUT=$(cat)
source "$(dirname "$0")/hook-helpers.sh"

si_is_active || si_noop_stop

# Build instruction list from pending flags.
INSTRUCTIONS=""

# 1. Simplify trigger.
PENDING_SIMPLIFY=$(si_state_read '.pending_simplify')
if [[ "$PENDING_SIMPLIFY" = "true" ]]; then
  DSINCE=$(si_state_read '.deliverables_since_last_simplify')
  LSINCE=$(si_state_read '.loc_since_last_simplify')
  INSTRUCTIONS="$INSTRUCTIONS

[hook] Simplify threshold crossed: ${DSINCE} deliverables / ${LSINCE} LOC since last report. Invoke strategic-implementation:simplify against the feature folder before the next deliverable's build phase. Per executing-plans Step 2f."
  si_state_mutate '.pending_simplify = false | .deliverables_since_last_simplify = 0 | .loc_since_last_simplify = 0'
fi

# 2. Edit-thrashing.
THRASH_FILE=$(si_state_read '.pending_thrash_pause')
if [[ -n "$THRASH_FILE" && "$THRASH_FILE" != "false" ]]; then
  INSTRUCTIONS="$INSTRUCTIONS

[hook] Edit-thrashing detected on \`${THRASH_FILE}\` (>3 edits in current deliverable). Pause: re-read the brief and the current deliverable's plan block before any further Edit/Write to that file. Log a thrash-pause deviation per executing-plans Step 2b."
  si_state_mutate '.pending_thrash_pause = false'
fi

# 3. Error-loop.
PENDING_ERR=$(si_state_read '.pending_error_loop')
if [[ "$PENDING_ERR" = "true" ]]; then
  INSTRUCTIONS="$INSTRUCTIONS

[hook] Error-loop detected: 3 consecutive tool failures without a strategy change. Do not retry. Escalate to strategic-implementation:post-execution in triage mode with the error trace. Log an error-loop-escalation deviation."
  si_state_mutate '.pending_error_loop = false | .consecutive_failures = 0'
fi

# 4. Validation-log surfacing.
PENDING_DEV=$(si_state_read '.pending_deviation_surface')
if [[ "$PENDING_DEV" = "true" ]]; then
  FEATURE_FOLDER=$(si_state_read '.feature_folder')
  INSTRUCTIONS="$INSTRUCTIONS

[hook] New high-signal entry in ${FEATURE_FOLDER}/validation-log.md. Read the tail of that file and surface to the PM before proceeding."
  si_state_mutate '.pending_deviation_surface = false'
fi

# Emit decision.
if [[ -n "$INSTRUCTIONS" ]]; then
  # jq -Rs serializes a multi-line string into a JSON string safely.
  REASON_JSON=$(printf '%s' "$INSTRUCTIONS" | jq -Rs '.')
  printf '{"ok": false, "reason": %s}\n' "$REASON_JSON"
  exit 0
fi

# No deterministic triggers pending — allow a normal stop.
echo '{"ok": true}'
exit 0
