#!/usr/bin/env bash
# refresh.sh — (re)build the memory index for a repo. Two uses:
#   1. SessionStart hook (invoked with --background): forks a detached worker
#      and returns instantly, so session start is never blocked.
#   2. Manual: `refresh.sh` rebuilds in the foreground and prints a summary.
#
# Safe anywhere: if the repo has no docs/strategic-implementation/, it is a
# no-op. Any failure degrades to silence (exit 0) — it never blocks a session.
# A mkdir-based lock prevents concurrent rebuilds (e.g. two sessions at once)
# from racing on the rebuild-from-scratch db.
set -uo pipefail

REPO="$PWD"
BG=0
while [ $# -gt 0 ]; do
  case "$1" in
    --background) BG=1 ;;
    --repo) shift; REPO="${1:-$REPO}" ;;
    --worker) BG=0 ;;            # internal: the detached worker runs foreground
    *) ;;
  esac
  shift
done

ROOT="$REPO/docs/strategic-implementation"
[ -d "$ROOT" ] || exit 0        # nothing to index in this repo

HERE="$(cd "$(dirname "$0")" && pwd)"

# Detach for the hook path: relaunch as a foreground worker, return now.
if [ "$BG" = "1" ]; then
  nohup "$0" --worker --repo "$REPO" >/dev/null 2>&1 &
  exit 0
fi

# --- worker / manual path ---
# Single-writer lock (mkdir is atomic). Stale-lock guard: 10 min.
LOCK="$ROOT/.memory/.rebuild.lock"
mkdir -p "$ROOT/.memory" 2>/dev/null
if ! mkdir "$LOCK" 2>/dev/null; then
  # If the lock is older than 10 min, assume a crashed run and take over.
  if [ -d "$LOCK" ] && [ -n "$(find "$LOCK" -maxdepth 0 -mmin +10 2>/dev/null)" ]; then
    rm -rf "$LOCK" 2>/dev/null; mkdir "$LOCK" 2>/dev/null || exit 0
  else
    exit 0   # another rebuild in progress
  fi
fi
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT

# Interpreter resolution (same order as recall.sh): explicit override →
# auto-discovered venv (enables vectors) → resident python3 (BM25-only).
DEFAULT_VENV_PY="${SI_MEMORY_VENV:-$HOME/.claude/strategic-implementation/.memory-venv}/bin/python"
PY="${SI_MEMORY_PYTHON:-}"
[ -n "$PY" ] && [ ! -x "$PY" ] && PY=""
[ -z "$PY" ] && [ -x "$DEFAULT_VENV_PY" ] && PY="$DEFAULT_VENV_PY"
[ -z "$PY" ] && PY="$(command -v python3 || true)"
[ -z "$PY" ] && exit 0

# --vectors auto: build vectors iff the chosen interpreter has the embedder,
# else BM25 only. build_index commits BM25 before attempting vectors, so a
# vector failure can never lose the BM25 index.
"$PY" "$HERE/build_index.py" --root "$ROOT" --vectors auto 2>/dev/null || exit 0
exit 0
