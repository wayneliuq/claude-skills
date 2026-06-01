#!/usr/bin/env bash
# Thin entrypoint for memory recall (house style: token-report.sh).
# Advisory ONLY: any failure — missing interpreter, missing/locked/malformed
# index, a recall.py crash — degrades to silence (exit 0, no stdout) so recall
# can never block execution or leak a stack trace into the agent's context.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# Interpreter resolution, in order:
#   1. $SI_MEMORY_PYTHON  — optional explicit override (custom interpreter)
#   2. the setup.sh venv at the canonical path — AUTO-DISCOVERED, so the vector
#      leg works with no shell-profile export once `setup.sh --install` has run
#   3. resident python3 — BM25-only fallback
# Either way recall degrades to silence; recall.py probes capability per call.
DEFAULT_VENV_PY="${SI_MEMORY_VENV:-$HOME/.claude/strategic-implementation/.memory-venv}/bin/python"
PY="${SI_MEMORY_PYTHON:-}"
[ -n "$PY" ] && [ ! -x "$PY" ] && PY=""                 # invalid override → fall back
[ -z "$PY" ] && [ -x "$DEFAULT_VENV_PY" ] && PY="$DEFAULT_VENV_PY"   # auto-discover venv
[ -z "$PY" ] && PY="$(command -v python3 || true)"
[ -z "$PY" ] && exit 0

out="$("$PY" "$HERE/recall.py" "$@" 2>/dev/null)" || exit 0
printf '%s' "$out"
[ -n "$out" ] && printf '\n'
exit 0
