#!/bin/bash
# Stop hook (command-type) for strategic-implementation.
# Reads state.json, collects any pending deterministic triggers, and either
#   - returns {"ok": false, "reason": "<consolidated guidance>"} so the agent
#     continues the next turn with the guidance injected, or
#   - returns {"ok": true} so the agent stops normally.
#
# Triggers handled (deterministic, harness-fired, no model judgment):
#   pending_chapter_rotation  → rotate chapter + emit new <active-goal> block
#   pending_simplify          → instruct invocation of strategic-implementation:simplify
#   pending_thrash_pause      → instruct re-read of brief before further edits to <file>
#   pending_error_loop        → instruct escalation to post-execution:triage
#   pending_deviation_surface → instruct surfacing of last validation-log entry
#
# Goal-condition evaluation (model judgment) is handled by a sibling prompt-type
# Stop hook declared in hooks.json; the two compose — when this hook fires
# {ok:false} with deterministic guidance, that guidance wins.

SI_HOOK_INPUT=$(cat)
source "$(dirname "$0")/hook-helpers.sh"

si_is_active || si_noop_stop

# Build instruction list from pending flags.
INSTRUCTIONS=""

# 1. Chapter rotation — highest priority.
PENDING_ROT=$(si_state_read '.pending_chapter_rotation')
if [[ "$PENDING_ROT" = "true" ]]; then
  CUR_CH=$(si_state_read '.current_chapter')
  NEXT_CH=$((CUR_CH + 1))
  CHAPTER_SIZE=$(si_state_read '.chapter_size')
  TOTAL=$(si_state_read '.total_deliverables')
  # Compute next chapter's deliverable range (D<start>..D<end>).
  START_IDX=$(( (NEXT_CH - 1) * CHAPTER_SIZE + 1 ))
  END_IDX=$(( NEXT_CH * CHAPTER_SIZE ))
  if [[ -n "$TOTAL" && "$END_IDX" -gt "$TOTAL" ]]; then END_IDX="$TOTAL"; fi

  BRIEF_SIGNAL=$(si_state_read '.brief_success_signal')
  PLAN_PATH=$(si_state_read '.plan_path')

  # Compose the new active-goal block. The skill (executing-plans) reads this
  # block from chat on its next turn and treats it as the binding chapter goal.
  if [[ -n "$TOTAL" && "$START_IDX" -gt "$TOTAL" ]]; then
    INSTRUCTIONS="All chapters complete. Invoke strategic-implementation:post-execution in regression-check mode now."
    si_state_mutate '.pending_chapter_rotation = false | .current_chapter = (.current_chapter + 1) | .deliverables_done_in_chapter = []'
  else
    NEW_GOAL=$(cat <<EOF

<active-goal chapter="$NEXT_CH" range="D${START_IDX}..D${END_IDX}">
condition: complete deliverables D${START_IDX} through D${END_IDX} as specified in ${PLAN_PATH}. Each must commit atomically with subject \`D<n>: ...\`, validation per its declared method recorded in validation-log.md, and checkpoint.md advanced.
brief success signal: ${BRIEF_SIGNAL}
constraints:
  - No edits outside file lists declared in deliverables D${START_IDX}..D${END_IDX}
  - No amending prior deliverable commits
  - Every Edit/Write announces \`touched: <files> deliverable: D<n>\` in chat
  - Stop and surface to PM on any BLOCK or unresolved ⚠️ in validation-log.md
turn-cap: stop after 40 turns and surface checkpoint.md to PM
</active-goal>

Chapter ${CUR_CH} complete. Beginning chapter ${NEXT_CH} (D${START_IDX}..D${END_IDX}). Resume execution at the next pending deliverable.
EOF
)
    INSTRUCTIONS="$NEW_GOAL"
    si_state_mutate ".pending_chapter_rotation = false
      | .current_chapter = $NEXT_CH
      | .deliverables_done_in_chapter = []
      | .deliverables_since_last_simplify = 0
      | .loc_since_last_simplify = 0"
  fi
fi

# 2. Simplify trigger.
PENDING_SIMPLIFY=$(si_state_read '.pending_simplify')
if [[ "$PENDING_SIMPLIFY" = "true" ]]; then
  DSINCE=$(si_state_read '.deliverables_since_last_simplify')
  LSINCE=$(si_state_read '.loc_since_last_simplify')
  INSTRUCTIONS="$INSTRUCTIONS

[hook] Simplify threshold crossed: ${DSINCE} deliverables / ${LSINCE} LOC since last report. Invoke strategic-implementation:simplify against the feature folder before the next deliverable's build phase. Per executing-plans Step 2f."
  si_state_mutate '.pending_simplify = false | .deliverables_since_last_simplify = 0 | .loc_since_last_simplify = 0'
fi

# 3. Edit-thrashing.
THRASH_FILE=$(si_state_read '.pending_thrash_pause')
if [[ -n "$THRASH_FILE" && "$THRASH_FILE" != "false" ]]; then
  INSTRUCTIONS="$INSTRUCTIONS

[hook] Edit-thrashing detected on \`${THRASH_FILE}\` (>3 edits in current deliverable). Pause: re-read the brief and the current deliverable's plan block before any further Edit/Write to that file. Log a thrash-pause deviation per executing-plans Step 2b."
  si_state_mutate '.pending_thrash_pause = false'
fi

# 4. Error-loop.
PENDING_ERR=$(si_state_read '.pending_error_loop')
if [[ "$PENDING_ERR" = "true" ]]; then
  INSTRUCTIONS="$INSTRUCTIONS

[hook] Error-loop detected: 3 consecutive tool failures without a strategy change. Do not retry. Escalate to strategic-implementation:post-execution in triage mode with the error trace. Log an error-loop-escalation deviation."
  si_state_mutate '.pending_error_loop = false | .consecutive_failures = 0'
fi

# 5. Validation-log surfacing.
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

# No deterministic triggers pending — defer to the sibling prompt-type goal evaluator.
echo '{"ok": true}'
exit 0
