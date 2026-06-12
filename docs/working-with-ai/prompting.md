# Prompting & interaction — the moves that change hit-rate

How *you* drive the agent matters more than the model. These are the ten moves that
separate a one-shot success from a three-round cleanup. Each has a bad→good in
TS/JS-backend terms. The matching skills (`clarify`, `improve-prompt`, `simplest-thing`,
`prove-it`, `diagnose`) encode these so the agent self-applies them — but the habit is yours.

> Grounding: Anthropic's [effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
> and [Claude Code best practices](https://code.claude.com/docs/en/best-practices). Core idea:
> the agent's context is a budget; spend it on signal, not restating, guessing, or chatter.

## 1. Spec before code
State goal · scope · non-goals · success criteria. An agent given a fuzzy ask fills the gaps
with confident guesses you then have to unwind.
- ❌ "Add caching to the API."
- ✅ "Cache the `GET /orders/:id` response in Redis, 60s TTL, key by order id. In scope: that one
  route. Non-goal: don't touch the write path or add a cache layer abstraction. Done when a second
  request inside 60s hits Redis (visible in the log) and the cache busts on order update."
- → `clarify` produces exactly this spec from a vague ask.

## 2. Surface assumptions / ask the forks
Make it list the interpretations that change the build *before* it picks one silently.
- ❌ Letting it choose between optimistic vs pessimistic locking on its own.
- ✅ "If there's a fork (e.g. lock strategy, sync vs async), name it and ask — don't just pick."

## 3. One concern per turn
Bundling orthogonal asks causes orthogonal edits — it "helpfully" refactors three unrelated
things and you can't tell the fix from the noise. Use `/clear` between unrelated tasks
(the "kitchen-sink session" anti-pattern).
- ❌ "Fix the auth bug and also clean up the logging and bump the deps."
- ✅ Three turns, or three sessions.

## 4. Show, don't tell
Paste the real error, stack trace, failing test, or file — not a paraphrase. Concrete artifacts
are higher-signal than your description of them.
- ❌ "The migration is failing with some constraint error."
- ✅ Paste the actual `ERROR: duplicate key value violates unique constraint "orders_pkey"` + the migration SQL.

## 5. Constrain the output shape
Say the form you want; otherwise you get a wall of prose around the one line you needed.
- ✅ "Diff only, no preamble." / "Answer in one line." / "Cite `file:line`." / "≤10 lines."

## 6. Negative space — bound the blast radius
Tell it what NOT to touch. This is the single highest-leverage line for surgical work.
- ✅ "Don't add dependencies. Don't refactor neighboring code. Touch only `orderService.ts`."
- → `simplest-thing` enforces this by default.

## 7. Plan mode for anything non-trivial
3+ steps or an architectural choice → make it plan and approve the plan before it edits.
Cheap to redirect a plan; expensive to unwind a wrong build. For big features, let it
interview you first (it asks about edge cases, tradeoffs, UI) rather than guessing.

## 8. Correct, don't accumulate
When it drifts, stop and re-plan or restart the turn — don't pile correction onto correction
in a polluted context. A fresh, well-framed turn beats a long contaminated one.
- ❌ Ten "no, not like that" replies deep in a derailed thread.
- ✅ "Stop. Here's the actual state and the corrected spec: …" (or `/clear` and re-frame).

## 9. Verify before you trust
Demand a run, not a "should work." Read the diff yourself before accepting.
- ✅ "Prove it: run the test and paste the output." → `prove-it` returns VERIFIED / NOT VERIFIED / INCONCLUSIVE.

## 10. Capture the lesson
When you correct the same mistake twice, write the rule down (`.ai/lessons.md`, project `CLAUDE.md`,
or a skill) so it compounds instead of recurring. That's what `personal-rules.md` is for.

---

### The 20-second pre-send checklist
Goal stated? · Scope bounded (what NOT to touch)? · Real artifacts pasted, not described? ·
Output shape named? · One concern? · Non-trivial → plan mode?

Sources: [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) ·
[Claude Code best practices](https://code.claude.com/docs/en/best-practices) ·
[Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
