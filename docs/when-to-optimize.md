# When to Optimize (and When Not To)

SkillOpt spent 0.6M–46.4M tokens per absolute test-point gained, with an automatic
verifier. You are doing this by hand. The scored loop is the **rare, expensive
exception** — not the default. Most skills should be written well once and revised
on observed failure.

## The ROI gate — run the full loop only if ALL hold

1. **Reuse ≥ ~10×.** The skill runs often enough that systematic improvement pays back
   the hours of eval-building and grading.
2. **A verifier exists** — tier is `objective` (a script/test/exact-match decides) or
   `rubric` (a fixed rubric a blind, different-model judge can apply). If the only judge
   is "does this feel better," it's `subjective`: do not run the scored loop.
3. **It failed ≥2× for real.** You have concrete, recurring failures — not a hunch.

If any fails, take the lite path.

## The lite path (default)

1. Write a tight `SKILL.md` (300–2000 tokens): procedural rules, tool policies, output
   constraints, known failure modes.
2. Add ~3 smoke-test prompts you can eyeball.
3. Ship it. Revise only when you see it fail in real use.

No splits, no gate, no grading runs. This covers the large majority of real skills.

## Picking the tier

- **objective** — output is checkable by a script: tests pass, types/lint clean, exact
  string or JSON match, deterministic transform. Use the full strict-greater gate.
- **rubric** — output quality is judgeable against fixed, observable criteria (e.g. "cites
  the exact source line", "no inline DB write"). Use blind pairwise grading with a
  **different model** when available; accept only on a majority win every run.
- **subjective** — taste, open-ended design, one-off prose. No scored gate is honest here;
  iterate qualitatively and don't pretend the number means anything.

## Why this matters

The headline gains (+19 to +25 pts on GPT-5.5, per the current paper) are `objective`-tier results. Quoting it for a `subjective`
skill is cargo-culting. This repo's value in the common case is the **discipline**
(bounded edits, snapshots, attribution, anti-noise guardrails), not a reproduction of the
paper's optimizer.
