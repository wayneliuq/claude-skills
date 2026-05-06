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

`task.md` is a self-contained prompt — what the worker is asked to do. It must NOT name any project learning, group label, or "with/without" framing. It reads like a normal task assignment.

`success-criteria.md` lists rubric items for the blind judge. Items must be observable from the worker's diff/output alone, without group context.

## How tasks are selected

`learnings-benchmark` Phase 2 looks for a `task.md`+`success-criteria.md` pair under `<theme>` matching each selected learning group. If none exists, the skill synthesizes a task from the learning's WHEN/DO text. Corpus tasks make repeated runs comparable; synthesis fallback covers gaps.

A discriminating task is one where the right answer is itself contested — a learning that points to the right answer pays off, and a model that already gets the right answer without the learning makes the learning retire-eligible.

## Adding tasks

Drop a new folder under the appropriate theme. Keep `task.md` short (≤200 words) and self-contained; keep `success-criteria.md` to 3–6 rubric items.
