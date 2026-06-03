#!/usr/bin/env bash
# bootstrap.sh — first-run setup for the externalized artifact store.
# Ensures the shared private store repo exists, then writes this repo's committed
# locator (repo-id + store coordinates; NO secret). Idempotent: safe to re-run.
#
# Usage: bootstrap.sh [--repo <owner/repo>] [--branch <name>]
#   --repo/--branch override the store target (default wayneliuq/strategic-artifacts @ main).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
. "$HERE/common.sh"

STORE_REPO="$STORE_REPO_DEFAULT"
STORE_BRANCH="$STORE_BRANCH_DEFAULT"
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) STORE_REPO="$2"; shift 2 ;;
    --branch) STORE_BRANCH="$2"; shift 2 ;;
    -h|--help) echo "usage: bootstrap.sh [--repo owner/repo] [--branch name]"; exit 0 ;;
    *) echo "[bootstrap] unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! gh_ok; then
  echo "[bootstrap] gh unavailable/unauthenticated/offline — cannot bootstrap. Run \`gh auth login\`." >&2
  exit 1
fi

RID="$(si_repo_id)"
[ -n "$RID" ] || { echo "[bootstrap] could not derive repo-id" >&2; exit 1; }

# --- ensure the shared private store repo exists, private-by-default (asserted, not assumed) ---
# Use the boolean isPrivate field ("true"/"false") — the visibility enum is uppercase and case-trips comparisons.
is_priv="$(gh repo view "$STORE_REPO" --json isPrivate -q .isPrivate 2>/dev/null)"
if [ -z "$is_priv" ]; then
  echo "[bootstrap] creating private store repo $STORE_REPO"
  gh repo create "$STORE_REPO" --private --description "strategic-implementation externalized artifact store" >/dev/null \
    || { echo "[bootstrap] repo create failed" >&2; exit 1; }
  is_priv="true"
fi
if [ "$is_priv" != "true" ]; then
  echo "[bootstrap] REFUSING: store repo $STORE_REPO is not private (spec §10). Make it private and re-run." >&2
  exit 1
fi

# --- write the locator if absent (idempotent); never embed a secret ---
LOC="$(si_locator_path)"
if [ -f "$LOC" ]; then
  echo "[bootstrap] locator already present ($LOC) — reusing (repo-id=$(si_locator_field repo_id))"
  exit 0
fi

mkdir -p "$(dirname "$LOC")"
read -r -d '' BODY <<EOF
# strategic-implementation store locator — machine-maintained, committed, NO secret.
# Points at the shared store; the credential is supplied out-of-band (gh ambient auth).
repo_id: "$RID"
store:
  kind: github
  repo: "$STORE_REPO"
  branch: "$STORE_BRANCH"
EOF

if ! assert_no_secret block "$BODY"; then
  echo "[bootstrap] aborting: locator body tripped the secret guard" >&2
  exit 1
fi
printf '%s\n' "$BODY" > "$LOC"
echo "[bootstrap] wrote locator $LOC (repo-id=$RID, store=$STORE_REPO@$STORE_BRANCH)"
