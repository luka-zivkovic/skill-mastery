---
name: clarify
description: >-
  Before building from a vague or ambiguous request, surface the interpretations
  that change the work, then turn the ask into a tight spec — and stop. Use when
  the user asks to build, add, change, or fix something and the goal, scope, or
  reading is underspecified, or says "spec this out", "what do you need before
  you start", "ask me questions first", or "don't assume". Do NOT use for
  already-precise asks or pure questions; for multi-feature asks use roadmap; for
  fixing a prompt/instruction file use improve-prompt.
---

# Clarify

The bane: a fuzzy or ambiguous ask produces confident, wrong work — the agent
picks one reading and burns a whole build on it. Surface the forks, pin the spec,
then stop. This skill does not implement.

## Workflow

1. Restate the request in one sentence as you currently understand it.
2. Surface the **interpretations** that would change what you build. If there's only one
   reasonable reading and the downside is small, skip questions and go straight to the spec.
3. Draft the spec with five fields, marking every guessed field `(assumed)`:
   - **Goal** — the user-visible outcome, not the implementation.
   - **In scope** — what this change touches.
   - **Out of scope / non-goals** — what it must NOT touch or attempt.
   - **Constraints** — stack, files, perf, compat, deadlines already known.
   - **Success criteria** — checkable conditions (a command, a screen state, a test) that prove it's done.
4. Split unknowns into **blocking** (can't proceed correctly without) vs **assumable** (a stated default is fine).
   State each assumable as "I'll assume X unless you say otherwise."
5. Ask only the **blocking** questions whose answer changes the build. Batch them, cap at 5, prefer "A or B?" forks.
   Always confirm for irreversible/destructive actions even if a reading seems obvious.
6. Stop at the spec. Hand to implementation only after the user confirms or answers — never silently proceed.

## Guardrails

- Do not write or edit application code here. Spec only.
- Look first: never ask what the codebase, files, or prior messages already answer.
- Prefer competing interpretations over a single silent guess; mark every inference `(assumed)`.
- Success criteria must be observable, not "works well" / "make it clean".
- Keep the spec to one screen. If it won't fit, the ask is really several requests — say so and point to roadmap.
- Don't hide behind questions to dodge easy work — if a safe default exists, state it and move.

## Output

`## Spec` (the five fields) → `## Assuming` (defaults you'll proceed on) →
`## Need from you` (numbered blocking questions, ≤5) → one line: `Ready to build on confirm.`
Omit `Assuming`/`Need from you` if nothing is unknown.

## Known failure modes

- **Charging ahead.** Producing code from a vague ask. Rule: stop at the spec.
- **Silent guess.** Picking one reading and building. Rule: surface forks before specifying.
- **Interrogation dump.** Asking everything. Rule: only build-changing blocking questions, ≤5, batched.
- **Vibe criteria.** "Make it clean." Rule: every success criterion must be checkable.
- **Scope creep.** Quietly widening the ask. Rule: anything beyond the literal request goes under non-goals.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
