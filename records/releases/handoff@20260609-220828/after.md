---
name: handoff
description: >-
  Emit a compact, structured state transfer so work can resume in a fresh
  context without losing the thread. Use when a session grows long, before
  compaction, when switching agents/machines, or when the user says "hand this
  off", "write a handoff", "summarize where we are", or "save context". Produces
  a handoff document in chat and persists it to .ai/handoff.md
  (disable-model-invocation).
disable-model-invocation: true
---

# Handoff

The bane: long sessions drift and the next context starts cold, re-deriving
decisions and repeating mistakes. Capture the durable state, drop the chatter.

## Workflow

1. State the goal: what we're ultimately trying to achieve (one or two sentences).
2. Capture **decisions made** and the reason for each — so they aren't relitigated.
3. Capture **current state**: what's done, what's in progress, where the code/branch is.
4. Capture **open threads**: next actions, unknowns, blockers, and known dead ends to avoid.
5. List the **key files / commands / entry points** the next context needs to get oriented fast.
6. Keep it scannable; omit conversational back-and-forth and anything re-derivable from the repo.
7. Write the identical document to `.ai/handoff.md` (create `.ai/` if missing; overwrite the
   prior handoff — history lives in git). Stamp line 1:
   `_Saved: <date> · branch: <branch> · HEAD: <short-sha>_` so resume can drift-check.

## Guardrails

- Durable state only: decisions, rationale, status, next steps. Cut the transcript and pleasantries.
- Record **why** behind each decision, not just what — the why is what prevents a redo.
- Note dead ends explicitly ("tried X, didn't work because Y") so they aren't retried.
- Point to files/branches/commands instead of pasting large code; keep it a map, not a copy.
- Be honest about uncertainty and unfinished work; a handoff that hides gaps causes the next failure.
- Keep it to roughly one screen; if it's longer, you're including chatter.
- Overwrite `.ai/handoff.md`; never accumulate multiple handoffs — one current handoff per project.

## Output

`## Goal` → `## Decisions` (decision · why) → `## State` (done / in progress / where) →
`## Open threads` (next · blockers · dead ends) → `## Orient` (key files, commands, branch).
Write the same document to `.ai/handoff.md` with the `Saved` stamp as line 1; show it in chat as well.

## Known failure modes

- **Transcript dump.** Replaying the whole chat. Rule: durable state only, no back-and-forth.
- **What without why.** Listing decisions with no rationale. Rule: each decision carries its reason.
- **Dead-end amnesia.** Omitting failed approaches. Rule: record what was tried and why it failed.
- **Code paste.** Inlining large snippets. Rule: link files/commands; keep it a map.
- **Chat-only handoff.** Emitted to chat but never persisted; the next session starts cold. Rule: always write `.ai/handoff.md`.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
