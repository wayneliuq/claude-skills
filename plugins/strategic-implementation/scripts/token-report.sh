#!/usr/bin/env bash
# token-report.sh — deterministic post-run telemetry for strategic-implementation.
#
# Reads the harness's session JSONL transcript + `rtk gain` (if present),
# emits a five-section token-report.md to <feature-folder>. No LLM step.
# Exits 0 even on partial failure; missing data renders as "unavailable".
#
# Usage:
#   token-report.sh <feature-folder> [<session-start-iso>]
#
# Format pin: TRANSCRIPT_FORMAT_VERSION below. Bump if Claude Code's JSONL
# event schema changes in a way that invalidates the jq filters here.

set -uo pipefail

TRANSCRIPT_FORMAT_VERSION="v1 (2026-05)"

FEATURE_FOLDER="${1:-}"
SESSION_START="${2:-}"

if [[ -z "$FEATURE_FOLDER" ]]; then
  echo "usage: token-report.sh <feature-folder> [<session-start-iso>]" >&2
  exit 2
fi

if [[ ! -d "$FEATURE_FOLDER" ]]; then
  echo "feature folder not found: $FEATURE_FOLDER" >&2
  exit 2
fi

REPORT="$FEATURE_FOLDER/token-report.md"

# ---- Resolve transcript dir for current cwd ----
CWD_ENC="$(pwd | sed 's|/|-|g')"
TRANSCRIPT_DIR="$HOME/.claude/projects/$CWD_ENC"

# Pre-flight: project-specific transcript dir exists AND contains *.jsonl.
TRANSCRIPT_AVAILABLE=0
TRANSCRIPT_FILE=""
if [[ -d "$TRANSCRIPT_DIR" ]]; then
  TRANSCRIPT_FILE="$(ls -t "$TRANSCRIPT_DIR"/*.jsonl 2>/dev/null | head -1)"
  if [[ -n "$TRANSCRIPT_FILE" && -r "$TRANSCRIPT_FILE" ]]; then
    TRANSCRIPT_AVAILABLE=1
  fi
fi

# ---- Tool-call mix + graph-vs-read ratio + tool-output volume ----
TOOL_CALL_MIX="unavailable"
GRAPH_VS_READ="unavailable"
OUTPUT_VOLUME="unavailable"

if [[ "$TRANSCRIPT_AVAILABLE" -eq 1 ]] && command -v jq >/dev/null 2>&1; then
  # Build a jq-safe filter expression for an optional session-start cutoff.
  if [[ -n "$SESSION_START" ]]; then
    SINCE_FILTER="select(.timestamp >= \"$SESSION_START\")"
  else
    SINCE_FILTER="."
  fi

  # Tool-call counts by name (lowercased categories at the end).
  TOOL_CALL_MIX="$(jq -r --arg since "$SESSION_START" '
    select(.type=="assistant") | $since as $s |
    (if $s == "" then . else select(.timestamp >= $s) end) |
    .message.content[]? | select(.type=="tool_use") | .name
  ' "$TRANSCRIPT_FILE" 2>/dev/null | sort | uniq -c | sort -rn | awk '{printf "- `%s`: %d\n", $2, $1}' )"
  [[ -z "$TOOL_CALL_MIX" ]] && TOOL_CALL_MIX="(no tool calls in window)"

  # Graph-vs-read ratio.
  GRAPH_COUNT="$(jq -r --arg since "$SESSION_START" '
    select(.type=="assistant") |
    (if $since == "" then . else select(.timestamp >= $since) end) |
    .message.content[]? | select(.type=="tool_use") |
    select(.name | startswith("mcp__code-review-graph__")) | .name
  ' "$TRANSCRIPT_FILE" 2>/dev/null | wc -l | tr -d ' ')"

  READ_COUNT="$(jq -r --arg since "$SESSION_START" '
    select(.type=="assistant") |
    (if $since == "" then . else select(.timestamp >= $since) end) |
    .message.content[]? | select(.type=="tool_use") |
    select(.name == "Read") | .name
  ' "$TRANSCRIPT_FILE" 2>/dev/null | wc -l | tr -d ' ')"

  GRAPH_COUNT=${GRAPH_COUNT:-0}
  READ_COUNT=${READ_COUNT:-0}
  if [[ "$GRAPH_COUNT" -gt "$READ_COUNT" ]]; then
    VERDICT="graph-dominant"
  elif [[ "$GRAPH_COUNT" -eq "$READ_COUNT" ]]; then
    VERDICT="mixed"
  else
    VERDICT="read-dominant"
  fi
  GRAPH_VS_READ="$GRAPH_COUNT graph-tool calls : $READ_COUNT Read calls — **$VERDICT**"

  # Tool-output volume (sum of tool_result content sizes, broken down by category).
  OUTPUT_VOLUME="$(jq -r --arg since "$SESSION_START" '
    select(.type=="user") |
    (if $since == "" then . else select(.timestamp >= $since) end) |
    .message.content[]? | select(.type=="tool_result") |
    {tool_use_id: .tool_use_id, size: (.content | tostring | length)}
  ' "$TRANSCRIPT_FILE" 2>/dev/null | jq -s -r '
    map(.size) | add // 0 | "Total tool-output bytes: \(.)"
  ' 2>/dev/null)"
  [[ -z "$OUTPUT_VOLUME" ]] && OUTPUT_VOLUME="unavailable"
fi

# ---- Bash savings via rtk ----
RTK_SECTION="unavailable"
if command -v rtk >/dev/null 2>&1; then
  RTK_VERSION_LINE="$(rtk --version 2>&1 | head -1)"
  if echo "$RTK_VERSION_LINE" | grep -qiE "rtk[ ]*[0-9]"; then
    # Heuristic: the Rust Token Killer prints `rtk X.Y.Z`. Confirm via `rtk gain` no-op.
    if RTK_OUT="$(rtk gain -p -H -f json 2>&1)"; then
      # Aggregate via jq if it parses; else summary fallback.
      if echo "$RTK_OUT" | jq -e . >/dev/null 2>&1; then
        RTK_SECTION="$(echo "$RTK_OUT" | jq -r '
          if type == "object" then
            (
              ("- Total saved (tokens): \(.total_saved // .saved // "?")"),
              ("- Commands counted: \(.commands_count // (.history|length?) // "?")"),
              (if (.history? | type) == "array" then
                "- Top contributors:\n" + ([.history | sort_by(.saved // 0) | reverse | .[0:5][] | "  - `\(.command // .cmd // "?")` saved \(.saved // "?")"] | join("\n"))
               else "" end)
            ) | tostring
          else
            "raw rtk output: \(. | tostring)"
          end
        ' 2>/dev/null)"
        [[ -z "$RTK_SECTION" ]] && RTK_SECTION="$(echo "$RTK_OUT" | head -20)"
      else
        RTK_SECTION="raw rtk output (non-JSON):\n\`\`\`\n$(echo "$RTK_OUT" | head -20)\n\`\`\`"
      fi
    else
      RTK_SECTION="rtk present but \`rtk gain -p -H -f json\` failed"
    fi
  else
    RTK_SECTION="rtk binary present but version string did not match expected (got: \`$RTK_VERSION_LINE\`); possible name collision with reachingforthejack/rtk"
  fi
fi

# ---- Simplify dispositions ----
SIMPLIFY_SECTION="(no simplify reports in this feature folder)"
shopt -s nullglob
REPORTS=( "$FEATURE_FOLDER"/simplify-report-*.md )
shopt -u nullglob
if [[ ${#REPORTS[@]} -gt 0 ]]; then
  TOTAL_FINDINGS=0
  APPLIED=0
  DEFERRED=0
  DISMISSED=0
  UNFILLED=0
  for r in "${REPORTS[@]}"; do
    # grep -c with no matches returns exit 1 + stdout "0"; force a clean integer.
    F=$(grep -c '^### F-' "$r" 2>/dev/null); F=${F:-0}; F=$(printf '%d' "${F//[^0-9]/}" 2>/dev/null || echo 0)
    A=$(grep -c '<!-- pm-disposition: apply -->' "$r" 2>/dev/null); A=${A:-0}; A=$(printf '%d' "${A//[^0-9]/}" 2>/dev/null || echo 0)
    D=$(grep -c '<!-- pm-disposition: defer -->' "$r" 2>/dev/null); D=${D:-0}; D=$(printf '%d' "${D//[^0-9]/}" 2>/dev/null || echo 0)
    X=$(grep -c '<!-- pm-disposition: dismiss -->' "$r" 2>/dev/null); X=${X:-0}; X=$(printf '%d' "${X//[^0-9]/}" 2>/dev/null || echo 0)
    U=$(grep -c '<!-- pm-disposition: -->' "$r" 2>/dev/null); U=${U:-0}; U=$(printf '%d' "${U//[^0-9]/}" 2>/dev/null || echo 0)
    TOTAL_FINDINGS=$((TOTAL_FINDINGS + F))
    APPLIED=$((APPLIED + A))
    DEFERRED=$((DEFERRED + D))
    DISMISSED=$((DISMISSED + X))
    UNFILLED=$((UNFILLED + U))
  done
  SIMPLIFY_SECTION="- Reports: ${#REPORTS[@]}
- Findings (total): $TOTAL_FINDINGS
- Disposition: apply=$APPLIED · defer=$DEFERRED · dismiss=$DISMISSED · unfilled=$UNFILLED"
fi

# ---- Write the report ----
{
  echo "<!-- transcript-format: $TRANSCRIPT_FORMAT_VERSION -->"
  echo "# Token report — $(basename "$FEATURE_FOLDER")"
  echo "_Generated: $(date '+%Y-%m-%d %H:%M:%S') · script: \`plugins/strategic-implementation/scripts/token-report.sh\` (deterministic, no LLM step)_"
  echo ""
  echo "## Tool-call mix"
  if [[ "$TOOL_CALL_MIX" == "unavailable" ]]; then
    echo "unavailable (no transcript dir or jq missing)"
  else
    echo "$TOOL_CALL_MIX"
  fi
  echo ""
  echo "## Graph-vs-read ratio"
  echo "$GRAPH_VS_READ"
  echo ""
  echo "## Tool-output volume"
  echo "$OUTPUT_VOLUME"
  echo ""
  echo "## Bash savings (rtk)"
  echo -e "$RTK_SECTION"
  echo ""
  echo "## Simplify dispositions"
  echo "$SIMPLIFY_SECTION"
  echo ""
  echo "---"
  echo "_Source transcript: \`${TRANSCRIPT_FILE:-unavailable}\` · session-start filter: \`${SESSION_START:-(none)}\`_"
} > "$REPORT"

echo "token-report written: $REPORT"
exit 0
