# Worked example — one full loop on `toy-skill`

A frozen, committed run of the whole loop so you can read the discipline instead of
imagining it. It optimizes `examples/toy-skill` against `examples/toy-evals/eval-manifest.yaml`
(tier: `rubric`). Numbers are illustrative but the artifacts are real and internally
consistent — every file here is what the scripts actually produce.

## The loop, start to finish

1. **Rollout** on the train split → found a recurring failure (dropped self-check, step
   drift). See `rollout-notes.md`.
2. **Reflect → bounded edits.** Two candidates: E1 (add a `Known failure modes` section)
   and E2 (a README-specific step). Generalizable vs. overspecified.
3. **Gate on validation (blind pairwise, different model, 3 runs):**
   - E2 → win-rates `[0.50, 0.625, 0.50]` → **reject** (not a majority every run). Lands in
     `records/rejected/` as negative feedback for the rest of the epoch.
   - E1 → win-rates `[0.75, 0.875, 0.75]` → **accept** (majority every run, no regression).
4. **Snapshot + slow-update.** Accepted skill saved to
   `records/snapshots/toy-skill@2026-06-01.md`, with one dated, ≥2-cited note in the
   protected `## Slow-update` region.
5. **Test check.** Periodic unbiased read of the test split held up (`[0.75, 0.75, 0.875]`).

## Files

| File | What it shows |
|------|---------------|
| `rollout-notes.md` | the recurring failure + why each edit was proposed |
| `records/accepted/0001-add-failure-modes.json` | the accepted bounded patch |
| `records/rejected/0001-overspec-readme-rule.json` | the rejected patch + its rationale |
| `records/eval_results.jsonl` | the blind grades + gate decisions (valid JSONL) |
| `records/snapshots/toy-skill@2026-06-01.md` | the accepted skill + slow-update note |

## Reproduce / inspect

```bash
# from examples/toy-run/ — history summary + the rejected-edit buffer to avoid re-proposing
python3 ../../scripts/summarize_skill_history.py records

# confirm the accepted patch applies cleanly to a copy of the skill (dry run)
cp -r ../toy-skill /tmp/toy-skill-copy
python3 ../../scripts/apply_skill_patch.py /tmp/toy-skill-copy \
  records/accepted/0001-add-failure-modes.json --dry-run
```

This is the `rubric`-tier path. An `objective`-tier run looks the same but the gate is a
script/exact-match instead of a blind judge, compared against baseline runs.
