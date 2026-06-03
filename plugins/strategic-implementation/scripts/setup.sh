#!/usr/bin/env bash
# setup.sh — bootstrap strategic-implementation plugin dependencies on a machine.
#
# Verifies (and, with --install, sets up) everything the plugin relies on:
#   - core tools: git, python3 (+ sqlite FTS5), jq
#   - code-review-graph (structural-graph MCP; performance dependency)
#   - rtk (optional token-savings telemetry)
#   - memory recall Phase 1a (BM25/FTS5 — stdlib only)
#   - memory recall Phase 1b (vector leg — extension-capable interpreter + a
#     persistent venv with sqlite-vec + model2vec)
#
# Default mode is --check (report only; NO changes). Re-run with --install to
# apply. Idempotent: safe to run repeatedly. Portable to macOS bash 3.2.
#
# Usage:
#   setup.sh [--check | --install] [--build-index] [--repo <path>] [-h]
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
MEMORY_DIR="$HERE/memory"
VENV_DIR="${SI_MEMORY_VENV:-$HOME/.claude/strategic-implementation/.memory-venv}"
REPO_ROOT="$(pwd)"
MODE="check"
DO_BUILD=0

# Pinned versions — source of truth: scripts/memory/requirements.txt
SQLITE_VEC_PIN="sqlite-vec==0.1.9"
MODEL2VEC_PIN="model2vec==0.8.2"
EMBED_MODEL="minishlab/potion-base-8M"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --install) MODE="install" ;;
    --check) MODE="check" ;;
    --build-index) DO_BUILD=1 ;;
    --repo) shift; REPO_ROOT="${1:-$REPO_ROOT}" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1"; usage; exit 2 ;;
  esac
  shift
done

PASS=0; WARN=0; FAIL=0
ok()   { echo "  [ok]   $1"; PASS=$((PASS+1)); }
warn() { echo "  [warn] $1"; WARN=$((WARN+1)); }
bad()  { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
note() { echo "         -> $1"; }
have() { command -v "$1" >/dev/null 2>&1; }
section() { echo ""; echo "== $1 =="; }

brew_install() {  # $1 = formula; returns 0 if installed
  if [ "$MODE" = "install" ] && have brew; then
    echo "         installing $1 via brew ..."
    brew install "$1" >/dev/null 2>&1 && return 0
  fi
  return 1
}

echo "strategic-implementation setup — mode: $MODE"
echo "repo: $REPO_ROOT"

# --------------------------------------------------------------------------
section "Core tools"
if have git; then ok "git $(git --version | awk '{print $3}')"
else bad "git missing"; note "install Xcode CLT (xcode-select --install) or 'brew install git'"; fi

if have python3; then
  PV="$(python3 -c 'import sys;print(sys.version.split()[0])' 2>/dev/null)"
  if python3 -c "import sqlite3;sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')" 2>/dev/null; then
    ok "python3 $PV (sqlite FTS5 available — BM25 recall works)"
  else
    bad "python3 $PV present but sqlite FTS5 unavailable"
    note "BM25 recall needs FTS5; install a python build that bundles it"
  fi
else
  bad "python3 missing"; note "install python (brew install python, or python.org)"
fi

if have jq; then ok "jq $(jq --version)"
elif brew_install jq; then ok "jq installed"
else bad "jq missing (hooks + token-report.sh need it)"; note "brew install jq"; fi

# gh — required by the externalized artifact store adapter (scripts/store/). Presence + auth + version floor.
if have gh; then
  GHV="$(gh --version 2>/dev/null | sed -nE 's/^gh version ([0-9]+)\.([0-9]+).*/\1.\2/p' | head -1)"
  GHMAJ="${GHV%%.*}"
  if [ -n "$GHMAJ" ] && [ "$GHMAJ" -ge 2 ] 2>/dev/null; then
    if gh auth status >/dev/null 2>&1; then ok "gh $GHV (authenticated — store adapter ready)"
    else bad "gh $GHV present but not authenticated"; note "run 'gh auth login' (needs 'repo' scope for the private store)"; fi
  else
    bad "gh version too old ($GHV; need >= 2.0)"; note "brew upgrade gh"
  fi
else
  bad "gh missing (externalized artifact store needs it)"; note "brew install gh && gh auth login"
fi

ok "bash ${BASH_VERSION:-unknown}"

# --------------------------------------------------------------------------
section "Optional telemetry — rtk"
if have rtk && rtk --version 2>/dev/null | grep -qiE 'rtk[ ]*[0-9]'; then
  ok "rtk $(rtk --version 2>/dev/null | head -1)"
else
  warn "rtk not found (token-report savings show 'unavailable' — optional, non-blocking)"
  note "install rtk if you want token-savings analytics"
fi

# --------------------------------------------------------------------------
section "code-review-graph (structural-graph MCP — performance dependency)"
have_crg() { have code-review-graph || python3 -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('code_review_graph') else 1)" 2>/dev/null; }
if have_crg; then
  ok "code-review-graph present"
elif [ "$MODE" = "install" ]; then
  if have uv; then echo "         uv tool install code-review-graph ..."; uv tool install code-review-graph >/dev/null 2>&1; fi
  if ! have code-review-graph; then echo "         pip install code-review-graph ..."; python3 -m pip install --user code-review-graph >/dev/null 2>&1; fi
  if have_crg; then ok "code-review-graph installed"; else warn "install attempted; verify manually (pip install code-review-graph)"; fi
else
  warn "code-review-graph not installed (skills fall back to file-read mode — degrades gracefully)"
  note "pip install code-review-graph   (or: uv tool install code-review-graph)"
fi
if have code-review-graph; then
  if [ "$MODE" = "install" ]; then
    code-review-graph install >/dev/null 2>&1 && ok "MCP server registered with Claude Code" \
      || warn "could not auto-register MCP (run: code-review-graph install)"
  fi
  if [ "$DO_BUILD" = "1" ]; then
    ( cd "$REPO_ROOT" && code-review-graph build >/dev/null 2>&1 ) && ok "graph built for $REPO_ROOT" \
      || warn "graph build failed (run 'code-review-graph build' inside the repo)"
  fi
fi

# --------------------------------------------------------------------------
section "Memory recall — Phase 1a (BM25 / FTS5)"
ok "no third-party deps (stdlib sqlite3 + FTS5, verified above)"
if [ "$DO_BUILD" = "1" ]; then
  if [ -d "$REPO_ROOT/docs/strategic-implementation" ]; then
    if python3 "$MEMORY_DIR/build_index.py" --root "$REPO_ROOT/docs/strategic-implementation" --vectors off --quiet; then
      ok "BM25 index built for this repo"
    else warn "index build returned non-zero (check FTS5 / corpus)"; fi
  else
    note "no docs/strategic-implementation/ in this repo yet — index builds on first feature"
  fi
fi

# --------------------------------------------------------------------------
section "Memory recall — Phase 1b (vector leg — optional)"
CAP=""
for cand in "${SI_MEMORY_PYTHON:-}" /usr/local/opt/python@3/bin/python3 /opt/homebrew/opt/python@3/bin/python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  [ -z "$cand" ] && continue
  if [ -x "$cand" ] || command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c "import sqlite3,sys;sys.exit(0 if hasattr(sqlite3.connect(':memory:'),'enable_load_extension') else 1)" 2>/dev/null; then
      CAP="$cand"; break
    fi
  fi
done

if [ -z "$CAP" ]; then
  warn "no extension-capable interpreter found (the python.org build has enable_load_extension compiled out)"
  note "install Homebrew python: brew install python   (then re-run --install)"
  note "without it, recall runs BM25-only everywhere — graceful, no breakage"
else
  ok "extension-capable interpreter: $CAP ($("$CAP" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null))"
  if [ "$MODE" = "install" ]; then
    if [ ! -x "$VENV_DIR/bin/python" ]; then
      mkdir -p "$(dirname "$VENV_DIR")"
      if "$CAP" -m venv "$VENV_DIR"; then ok "venv created: $VENV_DIR"; else bad "venv creation failed"; fi
    else
      ok "venv exists: $VENV_DIR"
    fi
    if [ -x "$VENV_DIR/bin/pip" ]; then
      if "$VENV_DIR/bin/pip" install -q --disable-pip-version-check "$SQLITE_VEC_PIN" "$MODEL2VEC_PIN"; then
        ok "vector deps installed ($SQLITE_VEC_PIN, $MODEL2VEC_PIN)"
      else
        bad "vector dep install failed (network? py-version wheels?)"
      fi
      if "$VENV_DIR/bin/python" - <<PY 2>/dev/null
import sqlite3, sqlite_vec
c = sqlite3.connect(":memory:"); c.enable_load_extension(True); sqlite_vec.load(c); c.execute("select vec_version()")
from model2vec import StaticModel
StaticModel.from_pretrained("$EMBED_MODEL").encode(["warm the model cache"])
PY
      then ok "sqlite-vec loads + embedding model cached (offline-ready)"
      else warn "vector verify/pre-warm failed (a one-time model fetch needs network)"; fi
    fi
    echo ""
    if [ "$VENV_DIR" = "$HOME/.claude/strategic-implementation/.memory-venv" ]; then
      echo "         Vector leg ready — recall auto-discovers this venv at the default path."
      echo "         No shell export needed. (Optional override: SI_MEMORY_PYTHON=<python>.)"
    else
      echo "         Non-default venv dir — export so recall finds it:"
      echo "           export SI_MEMORY_PYTHON=\"$VENV_DIR/bin/python\""
    fi
  else
    note "run with --install to create the venv + install vector deps (sqlite-vec, model2vec)"
    note "at the default path it is then auto-discovered — no shell export needed"
  fi
fi

# --------------------------------------------------------------------------
section "Summary"
echo "  pass=$PASS  warn=$WARN  fail=$FAIL  (mode: $MODE)"
if [ "$MODE" = "check" ]; then
  echo "  check mode — no changes made. Re-run with --install to apply, --build-index to also build indexes."
fi
[ "$FAIL" -gt 0 ] && exit 1
exit 0
