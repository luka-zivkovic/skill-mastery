---
name: improve-prompt
description: >-
  Rewrite a prompt, skill, or agent-instruction file (CLAUDE.md / AGENTS.md /
  system prompt) so it routes reliably and constrains behavior. Use when the
  user asks to improve/fix a prompt or instructions, "make this prompt better",
  "why won't the agent listen", or when an agent keeps misbehaving on the same
  instruction. The suite's quality multiplier.
---

# Improve Prompt

The bane: vague instructions produce vague agents. A prompt fails for nameable
reasons — no trigger, no constraints, buried priorities, contradictions. Fix the cause.

## Workflow

1. Identify what the prompt is for and the observed failure ("agent does X when it should do Y").
2. Diagnose against the common faults below — pick the specific ones in play, don't rewrite blind.
3. Rewrite for: clear **trigger** (when to apply / when NOT), **constraints** (do/don't),
   **output shape**, and **priority order** when rules can conflict.
4. Cut dead weight: redundancy, contradictions, polite filler, instructions for cases that never occur.
5. Show before→after for the changed parts and name which fault each edit fixes.
6. If it's a routing description (skill/tool), make it say both what it does and when to invoke it.

## Guardrails

- Edit for a named failure mode; don't reword for style alone.
- Be specific over exhaustive — one sharp constraint beats five vague ones.
- Surface contradictions instead of silently picking a side; ask if intent is unclear.
- Preserve the author's voice and any load-bearing domain rules; don't homogenize.
- For trigger/description text: include negative triggers (when NOT to fire) to stop over-routing.
- Keep it as short as it can be while still unambiguous; length is not rigor.

## Output

`## Diagnosis` (faults found) → `## Rewrite` (the improved text) →
`## Changes` (before→after · fault fixed). For small fixes, just the rewrite + a line on why.

## Known failure modes

- **Blind rewrite.** Polishing without diagnosing. Rule: name the fault each edit addresses.
- **Length-as-rigor.** Adding paragraphs that don't constrain. Rule: cut anything that doesn't change behavior.
- **Lost intent.** Smoothing away a load-bearing rule. Rule: preserve domain rules and voice.
- **No negative trigger.** Description that over-fires. Rule: state when NOT to apply.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
