# Resume & memory — the bridge to the Context + Memory pillars

The skill review surfaced one dominant gap in *continuing* work: when context is lost
(session ended, compacted, branch switched, days passed), the next context **starts cold** —
re-deriving decisions and re-hitting dead ends. That gap is not a prompting or planning problem;
it's the **Context + Memory** pillars, scheduled next. This doc is the seam so that turn plugs in
cleanly with no rework.

## The ideal resume flow

1. **Load state** — read the prior `handoff`: goal · decisions+why · state · open threads · dead ends · orient.
2. **Confirm goal validity** — quick `clarify` gate: "we were doing X under constraints Y — still true?"
3. **Spot drift** — does HEAD / `.ai/todo.md` / the roadmap still match? Reconcile before building on a stale plan.
4. **Continue** — next task → build → `prove-it` → `review-code`.

> **Status (2026-06-10): steps 1–3 are now implemented** by the `resume` skill
> (`claude-skills/resume/`), which loads `.ai/handoff.md` + `.ai/lessons.md`, confirms the goal,
> and runs a bounded drift check before continuing. See the updated build list below.

## Ownership split — what `handoff` owns vs what durable memory will own

| Concern | Owner | Lifespan |
|---|---|---|
| Goal, decisions+why, in-progress state, open threads, orient map | **`handoff`** (writes `.ai/handoff.md` with a `Saved` stamp) | One task / one resume hop |
| Dead ends from the current task | `handoff` | One task |
| Auto-load of prior state on session start | **`resume`** + SessionStart hook (`resume/references/session-start-hook.md`) | Cross-session |
| Durable cross-session store | **`.ai/handoff.md`** (git-tracked prose; supersedes the `.claude/resume.json` idea) | Cross-session, team-shareable |
| Plan-vs-code drift detection on resume | **`resume`** (bounded: stamp → `git log` → existence → contradictions) | Cross-session |
| Lesson/dead-end registry that accumulates across tasks | **`capture-lesson`** → `.ai/lessons.md` (one line per rule, capped at 20) | Long-lived |
| Durable project facts not derivable from the repo | `capture-lesson` proposes; **CLAUDE.md** holds (user applies) | Long-lived |

## Build list status (updated 2026-06-10)

1. ~~**Session-start auto-load**~~ — **done**: the `resume` skill (model-invocable) fires on
   "resume work"/"pick up where we stopped"; true session-start auto-load comes from the
   SessionStart hook in `claude-skills/resume/references/session-start-hook.md` (skills route
   off message text and cannot fire on file existence alone — review finding, 2026-06-10).
2. ~~**Durable resume store**~~ — **done**: `handoff` now persists to git-tracked `.ai/handoff.md`
   with a `Saved: date · branch · HEAD sha` stamp on line 1. Decided **against** `.claude/resume.json` /
   git-notes: prose markdown in the repo is reviewable in PRs and portable across Claude/Codex.
3. ~~**Plan-drift check**~~ — **done** (bounded, inside `resume`): parse stamp → `git log <sha>..HEAD` →
   branch/file existence → contradiction flags. Deliberately ≤5 read-only commands, not a full audit.
4. ~~**Dead-end / lesson registry**~~ — **done**: `capture-lesson` accumulates one-line rules in
   `.ai/lessons.md` (cap 20, dedup by strengthening); `resume` loads them at session start.
5. **Context hygiene guide** — still deferred: when to `/clear`, what compaction keeps vs drops,
   keeping context budget < ~30–40%.

Items 1–4 shipped 2026-06-10 as `claude-skills/resume/`, `claude-skills/capture-lesson/`, and a
bounded persistence patch to `claude-skills/handoff/` (releases under `records/releases/*@20260609-220828/`,
3/3 smoke tests each).
