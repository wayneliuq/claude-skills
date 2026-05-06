# Success criteria (blind rubric)

Score the response against the rubric below. Do NOT assume the responder had any extra context beyond `task.md`.

## Items

1. **Identifies the cache vs working-tree gap.** The response notes the agent loads from a cached install path, not the working tree, AND that the freshly-edited agent file is therefore not what `cli` actually invokes. (≥1 of: "plugin cache", "cached install", "not loaded from working tree", or equivalent paraphrase.) — required for `task_complete: true`.

2. **Recommends a validation method that does not depend on in-session live invocation of the just-edited file.** Acceptable: `post-hoc` (with manual reinstall + invoke), `cli` against a working-tree grep (proves prose-correctness, not behavior), or splitting into two steps (working-tree grep + post-hoc smoke). Not acceptable: keeping the original `cli` invocation against the agent without any acknowledgement of the cache. — drives `code_quality` upper bound.

3. **Names a concrete failure mode**: the validation passes (e.g. cli output happens to match) while the working-tree edit is not actually what produced the match — the cached-version behavior was tested instead. Bonus if it names the specific consequence: the reviewer's new `mock-placement` dimension wasn't actually exercised.

4. **Stays on the validation question.** Does not refactor D2's other fields, propose new deliverables, or rewrite unrelated prose. — penalize off-topic suggestions in `code_quality`.

5. **Provides a concrete corrected `Validation:` line.** Not a vague "fix the method"; an actual replacement line in the same format.

## Bug counting

Count as bugs (severity 1):
- Defends the original `cli` invocation as fully sufficient with no caveat.
- Recommends `tdd` against the cached agent (mocks the dependency that's the very thing being changed).

Count as bugs (severity 2):
- Misidentifies the failure mode (e.g. "the cli command might fail" instead of "the cli command might pass for the wrong reason").

Count as bugs (severity 3):
- Recommends bypassing the validation entirely / removing it.
- Misses item 1 entirely (no acknowledgement of where the agent loads from).
