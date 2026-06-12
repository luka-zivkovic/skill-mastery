---
name: capture-lesson
description: >-
  Distill a durable rule from a correction or failure into a one-line entry in
  .ai/lessons.md so it doesn't recur; propose a CLAUDE.md rule when it's
  load-bearing. Use when the user corrects the same thing twice, says 'remember
  this', 'add a lesson', 'don't do that again', or in a post-mortem of a failed
  approach. Do NOT use for one-off task-specific instructions.
---

# Capture Lesson

The bane: corrections evaporate — the same mistake gets re-corrected every
session because nothing durable records the rule. Distill it once, store it
where the next session will actually read it.

## Workflow

1. Qualify against the bar: the same correction given twice, OR one failure with
   concrete evidence (an actual wrong output/command in this session). A one-off
   task-specific instruction never qualifies — comply and write nothing.
2. Dedup: read `.ai/lessons.md` first (create it with the header below if missing).
   If an existing entry covers the situation, strengthen it in place — bump the
   date, sharpen the rule, tighten the evidence — never add a reworded duplicate.
3. Distill to one line, generalized past the current task ("when writing shell
   commands", not "in deploy.sh"):
   `- YYYY-MM-DD · when <trigger condition> → <rule> · evidence: <one clause> · scope: project|claude-md`
4. Route by scope: project habit → entry only. Load-bearing cross-task rule →
   entry + propose the exact CLAUDE.md line (the user applies it). Reusable
   multi-step procedure → no entry; route to improve-prompt (fixing an existing
   instruction file) or skill creation instead.
5. Append, show the entry verbatim, and enforce the cap: max 20 active entries /
   one screen. When an append would exceed it, merge duplicates, delete
   superseded entries, and propose promoting repeat offenders to CLAUDE.md in
   the same pass.

File header when creating `.ai/lessons.md`:
`# Lessons` then
`<!-- one line per lesson: - YYYY-MM-DD · when <trigger> → <rule> · evidence: <clause> · scope: project|claude-md. Cap: 20 entries. -->`

## Guardrails

- No one-offs: if it wouldn't apply to a future, different task, it is not a lesson.
- One line per lesson — no essay entries, no multi-paragraph context.
- Evidence is one clause, never a transcript or pasted output.
- Read before write: duplicates are strengthened, not re-added.
- Never edit CLAUDE.md silently — propose the exact line and let the user apply it.
- One lesson per capture; a flood of lessons from one incident means they aren't distilled.

## Output

The appended (or strengthened) entry verbatim → `Scope:` one line → optional
`## Proposed CLAUDE.md rule` with the exact line and where it goes.

## Known failure modes

- **One-off hoarding.** Recording task-specific instructions. Rule: the corrected-twice-or-failed-with-evidence bar.
- **Duplicate drift.** Re-adding reworded versions of an existing lesson. Rule: strengthen in place.
- **Essay entries.** Multi-line lessons nobody re-reads. Rule: one line; cap the file at 20.
- **Silent CLAUDE.md edits.** Promoting a rule without consent. Rule: propose only, user confirms.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
