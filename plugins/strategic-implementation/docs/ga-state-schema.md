# GA state schema

The `strategic-implementation` plugin tracks per-repo release maturity in:

```
<repo-root>/.strategic-implementation/ga-state.json
```

This file gates destructive cleanup operations (notably `prune-tests`) so they cannot fire on a pre-GA codebase where test sparsity is intentional.

## Semantics

| State | Meaning | `prune-tests` behavior |
|---|---|---|
| `pre-ga` | Active development. Line-level unit tests are intentionally sparse. | Runs normally. Candidates are unit tests not tied to the brief's user-observable deliverables or success signal. |
| `ga-prep` | Release imminent. Cleanup pass in progress. | Runs normally — this is the state where prune is expected to fire. |
| `ga` | Released. Line-level coverage is now a durable requirement. | **Refuses to run.** Post-GA, test deletion is an explicit code change requiring its own brief. |

If the file does not exist, the plugin defaults to `pre-ga`. The PM initializes the file by hand; no skill creates it automatically.

## Schema

```json
{
  "state": "pre-ga | ga-prep | ga",
  "transitioned_at": "2026-04-20T00:00:00Z",
  "notes": "optional free-form string"
}
```

- `state` (required): one of the three values above.
- `transitioned_at` (required): ISO-8601 timestamp the state was last set.
- `notes` (optional): PM-authored context, e.g. "preparing v1.0 release; prune scheduled for 2026-05-01."

## Example

```json
{
  "state": "pre-ga",
  "transitioned_at": "2026-04-20T00:00:00Z",
  "notes": "active dogfood; no GA target yet"
}
```

## Where this file lives in .gitignore

The `.strategic-implementation/` directory is per-repo workflow state. Whether to commit it is the repo owner's choice:
- **Commit** if the team wants GA state changes to show up in PRs.
- **Ignore** if GA state is a local/operator concern.

The plugin does not enforce either choice.

## Transitions

- `pre-ga` → `ga-prep`: PM decides release is imminent. Typically paired with running `prune-tests`.
- `ga-prep` → `ga`: release has shipped. Lock-down begins.
- `ga` → `pre-ga`: major rework. Rare. Requires explicit PM decision.

Transitions are manual. No skill auto-transitions.
