---
name: resume
description: >-
  Start a work session warm: load the prior handoff from .ai/handoff.md (or a
  pasted handoff) plus .ai/lessons.md, restate the goal, and drift-check the
  stated state against the repo before continuing. Use when the user says
  'resume', 'continue where we left off', 'pick up where we stopped', or at
  session start when .ai/handoff.md exists. Do NOT use for mid-session
  'continue' when the work is already in context.
---

# Resume

The bane: the next session starts cold — re-deriving decisions, re-hitting
recorded dead ends, or worse, building confidently on a plan the repo has
already moved past. Load the saved state, verify it still holds, then continue.

## Workflow

1. Locate state: read `.ai/handoff.md`. If absent, ask for a pasted handoff or
   offer a fresh start. Read `.ai/lessons.md` if present and keep its rules active
   for the whole session.
2. Restate the goal and key decisions in 2–3 lines: "we were doing X under
   constraints Y — still true?"
3. Drift-check (≤5 read-only commands): parse the `Saved` stamp (date · branch ·
   HEAD sha) from line 1; run `git log --oneline <sha>..HEAD`; confirm the branch
   and the files named in `## Orient` still exist; compare `## State` claims
   against commit subjects since the stamp.
4. Reconcile: report "state holds" or numbered drift findings. On any
   contradiction (finished items marked in-progress, missing branch/files,
   conflicting commits), list it and ask before building.
5. Confirm the next action from `## Open threads`, then hand into the normal
   loop (clarify → simplest-thing → prove-it).
6. Summarize, don't replay: the whole resume output fits in half a screen.

## Guardrails

- Read-only: never write `.ai/` files here — handoff and capture-lesson own the writes.
- Never build past unresolved drift; a stale plan executed well is still wrong work.
- The drift check is at most 5 read-only commands — no test runs, no diff reading, no audit.
- Don't relitigate recorded decisions unless the drift check contradicts them.
- Don't dump the handoff or lessons file verbatim into chat; summarize and point.
- If the handoff has no `Saved` stamp, fall back to branch/file existence checks and say so.

## Output

`## Resuming` (goal · N commits since handoff) → `## State check` ("holds" or
numbered drift findings) → `## Lessons active` (count + the load-bearing ones) →
`## Next` (proposed action + one confirm question). Half a screen max.

## Known failure modes

- **Cold start anyway.** Ignoring saved state and re-deriving. Rule: check `.ai/handoff.md` first, always.
- **Stale-plan continuation.** Building before checking the repo moved. Rule: drift-check before any build step.
- **Replay dump.** Pasting the whole handoff back. Rule: half-screen summary, point to the file.
- **Audit creep.** Turning the drift check into a repo review. Rule: stamp + log + existence checks only.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
