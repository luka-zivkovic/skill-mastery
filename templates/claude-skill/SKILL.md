---
name: example-skill
description: Replace with a concise trigger description stating what this skill does and the specific contexts where Claude should invoke it. Be specific enough to route reliably.
---

# Example Skill

Terse operating rules for the agent — not prose explanation. Keep it 300–2000 tokens.

## Procedural rules

1. Identify the user's concrete objective.
2. Load only the references or assets needed for the current request.
3. Prefer bundled scripts for repeated or fragile operations.
4. Produce the requested artifact, then validate it before responding.

## Tool policies

- State which tools/commands are preferred and which are forbidden for this task.
- Name the exact flags/APIs to use when there is a house convention.

## Output constraints

- State the required shape of the answer (format, length, must-include fields).

## Known failure modes

- List the recurring mistakes this skill exists to prevent, each with the corrective rule.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
