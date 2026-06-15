# Externalized artifact store — operator setup

The store adapter (`common.sh`, `bootstrap.sh`, `store.sh`, `cache.sh`, `migrate.sh`) keeps each
feature's per-feature **records** (brief, plan, validation-log, checkpoint, reports, mockup, …) in a
shared **private** GitHub repo instead of the working repo. The durable tier
(`project-learnings.md`, `documentation-registry.md`) and the per-repo `store-locator.yaml` stay
in-repo. See `docs/strategic-implementation/2026-06-02-externalized-artifacts/spec.md` for the design.

## Prerequisites (any repo)

1. **`gh` CLI authenticated** with `repo` scope: `gh auth status` must succeed. This is a *global*
   credential — once you're logged in, it works in every repo. The token is never written to the
   repo, the locator, or any record (resolved out-of-band at runtime).
2. **Network** reachable.
3. `setup.sh --check` verifies both (it checks `gh` presence + auth + version floor).

## First use in a new repo (bootstrap)

The skill bootstraps automatically at session entry. To do it by hand:

```bash
bash "$CLAUDE_PLUGIN_ROOT/scripts/store/bootstrap.sh"
```

This ensures the shared store exists (created once, reused thereafter — a *new* repo only adds its
own `<repo-id>` namespace, it does **not** create a second store) and writes the committed
`docs/strategic-implementation/store-locator.yaml` (coordinates only, no secret).

## Migrating an existing repo's notes into the store

`migrate.sh` is a forward-only **copy** (it never deletes in-repo files). It is resume-aware (skips
records already present) and throttled (to dodge GitHub's secondary write-rate limit).

```bash
# from anywhere inside the target repo:
bash "$CLAUDE_PLUGIN_ROOT/scripts/store/migrate.sh"            # copy + byte-identical spot-check
bash "$CLAUDE_PLUGIN_ROOT/scripts/store/migrate.sh" --confirm  # verify only, no writes
```

**Run it in your own terminal and it needs no Claude Code permission** — it's your shell. The
permission question only arises when the *agent* runs store writes on your behalf (see below).

## Permissions (one-time, user scope) — so the agent can write without prompts in every repo

Claude Code's safety classifier flags bulk writes to a repo that isn't the working repo's `origin`
as potential data-exfiltration, and reserves permission-file edits for **you** (the agent cannot
self-grant). To let the agent operate the store adapter across all your repos, add this **user-scope**
allow rule once — via `/permissions` (choose *Add allow rule*, user scope) or by editing
`~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(bash /Users/<you>/.claude/plugins/cache/wayneliuq/strategic-implementation/*/scripts/store/*.sh:*)"
    ]
  }
}
```

- The `*` after the plugin name matches any installed version; `*.sh` covers
  `bootstrap`/`store`/`cache`/`migrate`. The underlying `gh api` calls are children of these
  commands, so they're covered too.
- This is **user scope** on purpose — project-scope rules (`.claude/settings.local.json`) only apply
  to one repo and won't carry to others.
- Tip: the most reliable way to capture the exact command form is to choose **"Yes, and don't ask
  again"** the first time the agent is prompted to run a store command — Claude Code writes the
  precise rule for you.

If you'd rather not pre-authorize the agent, just run `migrate.sh` yourself (above) — zero permission
needed.

## Record routing protocol (agent-facing)

This is the canonical protocol every skill follows. Per-feature **records** (brief / plan /
validation-log / checkpoint / reports / mockup / brief-meta — NOT the durable tier) are read and
written through the store adapter, not the feature folder directly. Wherever a skill step says to
write or read `<feature-folder>/<file>`, route it as below; treat `<file>` as the `<artifact-name>`
of the record address `<repo-id>/<date-slug>/<artifact-name>`.

- **Write (fallback-safe):** `bash "${CLAUDE_PLUGIN_ROOT}/scripts/store/store.sh" put "<repo-id>/<date-slug>/<file>" "<feature-folder>/<file>" <local-tmp> --handle-out <h>` — stores the record, OR writes the in-repo `<feature-folder>/<file>` fallback if gh/locator is unavailable or the store write fails (a surfaced conflict is NOT fallen back). Then best-effort `cache.sh refresh "<address>" <local-tmp>`.
- **Read (this feature):** the human-browsable copy is the cache (`cache.sh path <date-slug>`); the authoritative read is `store.sh read "<address>"`.
- **Read (a PRIOR feature) — live:** `store.sh list "<repo-id>/<prior-date-slug>"` then `store.sh read` per address. Never the active-feature cache (it holds only the active feature).
- **Per-operation fallback (transition safety):** evaluate immediately before EACH record read/write — if the locator (`docs/strategic-implementation/store-locator.yaml`) is absent (bootstrap not run) or `gh` is unavailable/offline, fall back to the in-repo `<feature-folder>/<file>` path for that operation and note the fallback. If a store write fails mid-operation, fall back to the in-repo path within the same operation so no record is ever dropped.
- **Durable tier stays in-repo:** `project-learnings.md` and `documentation-registry.md` are read/written in place — never routed to the store.
