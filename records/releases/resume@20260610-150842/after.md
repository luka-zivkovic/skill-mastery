---
name: resume
description: >-
  Start a work session warm: load the prior handoff from .ai/handoff.md (or a
  pasted handoff) plus .ai/lessons.md, restate the goal, and drift-check the
  stated state against the repo before continuing. Use when the user says
  'resume work', 'continue where we left off', 'pick up where we stopped', or
  refers to continuing a prior session. Do NOT use for mid-session 'continue'
  when the work is already in context, for an unrelated new task (even if a
  handoff file exists — then just load lessons and mention the parked handoff
  in one line), or for résumé/CV documents.
---

# Resume

Load the saved session state, verify it still holds against the repo, then continue.

## Workflow

1. Locate state: read `.ai/handoff.md`. If absent, ask for a pasted handoff or
   offer a fresh start — never invent prior-session state. Read `.ai/lessons.md`
   if present and keep its rules active for the whole session.
2. Restate the goal and key decisions in 2–3 lines: "we were doing X under
   constraints Y — still true?"
3. Drift-check, using at most these read-only checks:
   - Parse line 1's stamp. Handoff writes exactly:
     `_Saved: <date> · branch: <branch> · HEAD: <short-sha>_`
   - `git log --oneline <sha>..HEAD` for commits since the stamp. If the sha is
     unknown (rebase/force-push), say history was rewritten, use
     `git log --oneline --since=<stamp date>` instead, and treat `## State`
     claims as unverified.
   - Compare the stamped branch to the current branch — a mismatch is drift finding #1.
   - `git status --porcelain` — uncommitted changes are state the handoff can't know.
   - One batched existence check for files named in `## Orient`.
4. Reconcile: report "state holds" or numbered drift findings. On contradiction
   (in-progress items finished by later commits, missing branch/files), list it
   and ask before building. If the stamp is weeks old or more than ~30 commits
   behind, don't reconcile line-by-line — report the gap and offer a fresh start.
5. Confirm the next action from `## Open threads`, then proceed normally:
   confirm scope, make the smallest change, verify it (via the clarify /
   simplest-thing / prove-it skills when installed).

## Guardrails

- Read-only: never write `.ai/` files here — handoff and capture-lesson own the writes.
- Never build past unresolved drift; a stale plan executed well is still wrong work.
- No `Saved` stamp → fall back to branch/file existence checks and say so. Missing
  sections (pasted or foreign handoffs) → use what's there and name what's absent.
- Lessons outrank handoff decisions; if they conflict, surface it as a drift finding.
  If the lessons file is over ~20 entries, load the most recent and flag it for pruning.
- Don't relitigate recorded decisions unless the drift check contradicts them.
- Don't dump the handoff or lessons verbatim into chat; summarize and point. No test
  runs, no diff reading, no repo audit — this is a state check, not a review.

## Output

`## Resuming` (goal · N commits since handoff) → `## State check` ("holds" or
numbered drift findings) → `## Lessons active` (count + the load-bearing ones) →
`## Next` (proposed action + one confirm question). Keep it under ~15 lines.

## Auto-load at session start

Skills route off the user's message; they cannot fire on file existence alone. For
true session-start auto-load, install the SessionStart hook from
`references/session-start-hook.md` — it surfaces an existing `.ai/handoff.md` and
points the session at this skill.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
