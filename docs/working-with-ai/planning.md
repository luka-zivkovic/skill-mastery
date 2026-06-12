# Planning — and continuing work without starting cold

Planning is how you keep a long task on-rails and how you pick it back up tomorrow. Two halves:
**plan the work** (before/while building) and **continue the work** (resume after a break or a
context reset). The skills `clarify`, `roadmap`, and `handoff` encode the moves; the loop is yours.

> Grounding: Anthropic's [effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> — make incremental progress each session and leave clear artifacts for the next one.

## Part A — Plan the work

### 1. Decide if it needs a plan
3+ steps, an architectural choice, or an ambiguous ask → plan. A typo or a one-line change → just do it.
Don't manufacture ceremony for trivial work.

### 2. Spec → plan → bite-sized verifiable tasks
- **Spec** the outcome first (`clarify`): goal · scope · non-goals · success criteria.
- **Break into tasks** small enough to verify independently — each one checkable in a couple minutes,
  phrased as an outcome ("`POST /orders` returns 201 + persists row"), not an activity ("work on orders").
- A task you can't state a check for is too big or too vague — split it.

### 3. Vertical slices, ROI-gated
Each slice ships user-visible value end-to-end and stands alone. Reject horizontal layers
("do all the backend first") — they ship nothing. Rank impact ÷ effort, sequence now/next/later,
cut ruthlessly. → `roadmap` does this and ends with a per-slice `clarify → simplest-thing → prove-it → review-code` kickoff.

### 4. Use plan mode + the native plan tool
For non-trivial work, make the agent present a plan and approve it before edits. Cheap to fix a plan,
expensive to unwind a build.

### 5. Run the `.ai/todo.md` + `.ai/lessons.md` loop (your CLAUDE.md already mandates it)
- `.ai/todo.md`: checkable items; mark them done as you go. It's the durable in-repo plan, not a doc you write once.
- `.ai/lessons.md`: after any correction, write the rule so it doesn't recur — the `capture-lesson`
  skill writes these entries (one line each, deduped, capped at 20).

### 6. Verify per task, not just at the end
Gate each task with `prove-it` before moving on. Ten unverified tasks stacked up means debugging ten
changes at once when the end-to-end check fails.

## Part B — Continue the work (resume without starting cold)

Context fills and gets summarized; you stop for the day; you switch branches. The failure mode is the
next context **starting cold** — re-deriving decisions, re-hitting dead ends. The fix is a durable artifact.

### The resume flow (steps 1–3 are encoded in the `resume` skill)
1. **Load the handoff** — read the prior `handoff` (goal · decisions+why · state · open threads · dead ends · orient).
2. **Confirm the goal still holds** — a quick `clarify` gate: "we were doing X under constraints Y — still true?"
3. **Spot drift** — has the code moved past what `.ai/todo.md` / the roadmap says? Reconcile before building on a stale plan.
4. **Continue** — pick the next task and run the build→verify loop.

### Write a handoff *before* you lose context
Trigger `handoff` when a session grows long, before compaction, or at end of day. Capture decisions and
**why** (the why is what stops a redo), what's in progress and where, and dead ends ("tried X, failed because Y").
Keep it to one screen — a map, not a transcript.

> The **Context + Memory** pillars are now built: `handoff` persists to `.ai/handoff.md`,
> `capture-lesson` accumulates `.ai/lessons.md`, and `resume` loads both with a drift check at
> session start — see `resume-and-memory-bridge.md` for status and what remains (context hygiene).

---

### Quick reference
Starting: decide-if-plan → `clarify` spec → bite-sized tasks → `roadmap` if multi-slice → plan mode → build/verify loop.
Continuing: `resume` (loads `.ai/handoff.md` + `.ai/lessons.md`, confirms goal, drift-checks) → next task.

Sources: [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) ·
[Claude Code best practices](https://code.claude.com/docs/en/best-practices).
