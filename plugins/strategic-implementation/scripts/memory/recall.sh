#!/usr/bin/env bash
# Thin entrypoint for memory recall (house style: token-report.sh).
# Advisory ONLY: any failure — missing interpreter, missing/locked/malformed
# index, a recall.py crash — degrades to silence (exit 0, no stdout) so recall
# can never block execution or leak a stack trace into the agent's context.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# Interpreter resolution: SI_MEMORY_PYTHON (an extension-capable interpreter,
# e.g. a Homebrew-python venv) enables the vector/fusion path; otherwise the
# resident python3 runs BM25-only. Either way recall degrades to silence.
PY="${SI_MEMORY_PYTHON:-}"
[ -n "$PY" ] && [ ! -x "$PY" ] && PY=""        # invalid override → fall back
[ -z "$PY" ] && PY="$(command -v python3 || true)"
[ -z "$PY" ] && exit 0

out="$("$PY" "$HERE/recall.py" "$@" 2>/dev/null)" || exit 0
printf '%s' "$out"
[ -n "$out" ] && printf '\n'
exit 0
