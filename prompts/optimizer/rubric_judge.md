# Rubric Judge (blind pairwise)

Use this for the `rubric` verifiability tier. The judge MUST be independent of the
editor: a **different model** when available (e.g. editor = Opus → judge = Sonnet/Haiku,
or a cross-provider model); otherwise a **fresh context** of the same model, recorded as
a caveat. The editor never grades its own edit.

## Inputs given to the judge

- The fixed rubric criteria from the eval manifest (`rubric.criteria`).
- The task prompt.
- Two outputs labeled **A** and **B**, with order **randomized per task** so the judge
  cannot infer which is the candidate. The judge is NOT told which skill produced which.

## Instructions to the judge

1. For each rubric criterion, decide which output better satisfies it: A, B, or tie.
2. Do not reward length, confidence, or formatting unless a criterion asks for it.
3. Pick an overall winner (A, B, or tie). Ties count as a non-win for the candidate.
4. Return strict JSON only:

```json
{
  "per_criterion": [{"criterion": "...", "winner": "A|B|tie"}],
  "overall_winner": "A|B|tie",
  "reason": "one sentence grounded in the criteria"
}
```

## Caller responsibilities (orchestration)

- Run the judge `grading_runs` times (>= 3), re-randomizing A/B order each run.
- Un-blind after grading: convert each result to a win-rate for the NEW skill.
- Accept only if NEW is a majority win in **every** run (see `record_eval_result.py`).
- Record `judge_model` and whether grading was blind via `--judge-model` / `--judge-blind`.
