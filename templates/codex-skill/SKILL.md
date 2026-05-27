---
name: example-skill
description: Replace with a concise trigger description that states what this skill does and the specific contexts where Codex should use it.
---

# Example Skill

Use this skill to perform the named workflow reliably and consistently.

## Workflow

1. Identify the user's concrete objective.
2. Load only the references or assets needed for the current request.
3. Prefer bundled scripts for repeated or fragile operations.
4. Produce the requested artifact or answer.
5. Validate the result before responding.

## Resources

- `references/`: load only the specific file relevant to the request.
- `scripts/`: run deterministic helpers instead of rewriting fragile code.
- `assets/`: copy or adapt output resources without loading them into context unless necessary.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
