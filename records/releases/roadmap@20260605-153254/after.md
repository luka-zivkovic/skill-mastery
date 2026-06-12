---
name: roadmap
description: >-
  Turn goals or audit findings into a prioritized, ROI-gated plan broken into
  independently-shippable vertical slices. Use when the user asks what to build
  next, to plan/sequence work, "turn this into a roadmap", "break this down", or
  right after an app audit. For a single underspecified feature use clarify, not
  roadmap; ask for audit-app first if the codebase state is unclear. Produces a
  plan (disable-model-invocation); it sequences work, it does not implement.
disable-model-invocation: true
---

# Roadmap

The bane: "what do I do next?" answered by gut, producing a pile of half-done
horizontal work. Turn goals/findings into ranked, shippable slices with a clear why.

## Workflow

1. Gather inputs: the goal(s) and any audit/triage findings. If goals are vague, clarify first.
2. Break work into **vertical slices** — each delivers user-visible value end to end and ships alone.
   Reject horizontal layers ("do all the backend") that ship nothing on their own.
3. Score each slice: **impact** (user/business value) and **effort/risk**. Note dependencies.
4. Rank by ROI; apply the gate — defer or cut low-impact / high-effort items, say so explicitly.
5. Sequence into now / next / later, respecting dependencies; flag the riskiest assumptions to de-risk early.
6. Output the plan with a one-line success criterion per slice. Do not start building.

## Guardrails

- Every item is a vertical slice with a user-visible outcome, not a layer or a chore bucket.
- Rank by impact ÷ effort; make the gate explicit — name what you're deferring and why.
- Surface dependencies and the riskiest assumption; sequence to learn early, not to look busy.
- Keep it small: now/next/later, not a 40-line backlog. Cut ruthlessly.
- Don't implement here; this skill ends at the sequenced plan.
- Tie each slice to a checkable success criterion, not an activity ("build X", not "work on X").

## Output

`## Slices` (slice · impact · effort · success criterion) → `## Sequence` (Now / Next / Later)
→ `## Deferred / cut` (item · why) → `## Risks` (assumption to de-risk first) →
`## Next` (per slice: clarify → simplest-thing → prove-it → review-code).

## Known failure modes

- **Horizontal planning.** "Phase 1: all backend." Rule: every item ships user value alone.
- **Ungated backlog.** Listing everything as equal. Rule: rank by ROI; state what's deferred.
- **Activity not outcome.** "Work on auth." Rule: each slice has a checkable success criterion.
- **Plan-then-build.** Sliding into implementation. Rule: stop at the sequenced plan.

## Slow-update (do not overwrite in single-pass edits)

<!-- Protected region. Only the epoch-end slow-update step writes here.
     Every note must cite >= 2 validation examples and carry a date.
     Durable cross-iteration lessons only — no task-specific answers, no bulky examples. -->
