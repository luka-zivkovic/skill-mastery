---
name: capture-lesson
description: >-
  Distill a durable rule from a correction or failure into a one-line entry in
  .ai/lessons.md so it doesn't recur; propose a CLAUDE.md rule when it's
  load-bearing. Use when the user corrects the same thing twice, says 'remember
  this', 'add a lesson', 'don't do that again', or in a post-mortem of a failed
  approach. One-off or day-scoped facts don't become lessons — but never
  silently drop an explicit 'remember this': say where the fact will live instead.
---

# Capture Lesson

Distill the correction once, store it where the next session will actually read it.

## Workflow

1. Qualify. The bar — same correction given twice, OR one failure with concrete
   evidence (an actual wrong output/command this session) — gates agent-initiated
   captures only. An explicit user ask ("remember this", "add a lesson") always
   gets a response: durable rule → write it; session- or day-scoped fact → don't
   write a lesson, keep it in working context (and the handoff, if one gets
   written) and tell the user where it lives and why.
2. Dedup: read `.ai/lessons.md` first (create it with the header below if missing).
   - Existing entry agrees → strengthen in place: bump the date, sharpen the rule,
     compress the evidence (e.g. `3x since 2026-04`). Never add a reworded duplicate.
   - Existing entry contradicts the new correction → replace its rule: today's
     date, evidence noting it supersedes the old rule. If the old rule was
     promoted to CLAUDE.md, propose the retraction too.
3. Distill to one line, generalized past the current task ("when writing shell
   commands", not "in deploy.sh"):
   `- YYYY-MM-DD · when <trigger condition> → <rule> · evidence: <one clause> · scope: project|all-tasks`
   One lesson per distinct root cause; a post-mortem may yield several (cap ~3),
   each qualified separately.
4. Route by scope: `project` (a habit of this codebase) → entry only. `all-tasks`
   (violating it breaks builds/CI/safety, or it applies regardless of task type) →
   entry + propose the exact CLAUDE.md line; when the user applies it, append
   `· promoted: YYYY-MM-DD` to the entry. A multi-step procedure → still write the
   one-line entry pointing at it, then route to improve-prompt (if an instruction
   file covers the area) or suggest a new skill — never exit with nothing recorded.
5. Append and show the entry verbatim. Cap: 20 entries. If an append would exceed
   it, propose a merge/prune plan (promoted and superseded entries first), show
   before → after, and get a yes before touching any existing line. Appending
   never needs confirmation; rewriting or deleting existing entries does.

File header when creating `.ai/lessons.md`:
`# Lessons` then
`<!-- one line per lesson; format defined by the capture-lesson skill. Cap: 20 entries. -->`

## Guardrails

- If it wouldn't apply to a future, different task, it is not a lesson.
- One line per lesson; evidence is one clause, never a transcript.
- Read before write; duplicates are strengthened or replaced, never re-added.
- Never edit CLAUDE.md silently. Show every change to an existing lesson line as
  old → new; strengthens and user-driven replacements need no confirmation, but
  the cap's merge/prune of other entries always requires a yes first.
- Never silently drop an explicit "remember this" — always say where the fact went.

## Output

The appended (or strengthened/replaced) entry verbatim → one line stating the
routing decision (project entry / CLAUDE.md rule proposed below / kept in session
context / routed to improve-prompt) → optional `## Proposed CLAUDE.md rule` with
the exact line and where it goes.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
