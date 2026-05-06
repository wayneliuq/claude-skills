# Benchmarks corpus

Tasks consumed by `learnings-benchmark` Phase 2.

## Layout

```
benchmarks/
  <theme>/
    <task-slug>/
      task.md
      success-criteria.md
```

`<theme>` matches a `#tag` in `docs/strategic-implementation/project-learnings.md` (today: `scope`, `security`, `technical`, `tests`) or a sibling agent role.

`task.md` — self-contained prompt. MUST NOT name any project learning, group label, or "with/without" framing. Reads like a normal task assignment.

`success-criteria.md` — rubric items for the blind judge. Items must be observable from the worker's diff/output alone, without group context.

## How tasks are selected

Phase 2 looks for a `task.md` + `success-criteria.md` pair under `<theme>` matching each selected learning group. If none exists, the skill synthesizes a task from the learning's WHEN/DO text. Corpus tasks make repeated runs comparable; synthesis covers gaps.

A discriminating task is one where the right answer is itself contested — a learning that points to it pays off, and a model that already gets it without the learning makes the learning retire-eligible.

## Adding tasks

Drop a new folder under the appropriate theme. Keep `task.md` short (≤200 words) and self-contained; keep `success-criteria.md` to 3–6 rubric items.
