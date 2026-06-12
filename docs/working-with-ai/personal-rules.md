# Personal rules — paste-able behavior block

Drop the block below into any project's `CLAUDE.md` / `AGENTS.md`. It's the distilled,
load-bearing version of `prompting.md` + `planning.md` — tuned for a TS/JS full-stack /
backend / infra workflow. Keep it short; every line earns its place. Trim what doesn't apply.

---

```md
## How to work with me

### Scope & assumptions
- No silent assumptions. If the goal, scope, or reading is unclear, state the forks and ask — don't guess.
- Do the simplest thing that fully solves the stated problem. No speculative abstractions, no
  error handling for cases the types rule out, no "while I'm here" edits.
- Touch only what the task requires. Don't refactor neighbors, rename, or reformat unrelated code.
- No new dependency without saying why and what it replaces.

### Working rhythm
- 3+ steps or an architectural choice → plan first and let me approve it before editing.
- One concern per turn. If I bundle unrelated asks, split them.
- When you drift, stop and re-state the corrected plan — don't pile fixes onto a polluted thread.

### Evidence
- Nothing is "done" without a real run. Show the command and its actual output, not "should work."
- If you can't run it, say so and say what's needed — don't bluff a green.
- Read the diff for correctness/security before declaring it mergeable; lead with the real bug, not nits.

### Stack defaults (edit per project)
- TypeScript: no `any` without a comment; validate external input at the boundary (zod/schema).
- Match the existing patterns in the file — even ones I'd do differently. Search for an existing util before adding one.
- Tests live next to what they test; a fix ships with a regression test.

### Continuity
- Long session or end of day → write a compact handoff: goal, decisions + why, state, open threads, dead ends.
- After I correct the same thing twice, propose a durable rule for this file.
```

---

**Why this works:** it front-loads the constraints that the agent otherwise has to guess at —
which is where most wasted rounds come from. It's behavior, not background; keep it under ~30 lines
so it stays cheap in context and actually gets followed. Revise it when you catch yourself giving
the same correction across projects.
