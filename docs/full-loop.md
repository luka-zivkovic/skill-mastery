# The Full Scored Loop

The full loop is advanced and rare. Use it only when the ROI gate in `docs/when-to-optimize.md` passes.

## Use when all hold

1. The skill is reused often enough to repay eval-building cost.
2. The task has an objective verifier or a credible blind rubric judge.
3. The skill has failed at least twice in real use.

## Flow

```txt
manifest → train rollout → failure reflection → bounded edits → validation gate → accept/reject → slow-update → release package
```

## Commands

```bash
python3 scripts/validate_eval_manifest.py workshop/evals/<name>.yaml
python3 scripts/skillopt_run.py workshop/skills/<name> workshop/evals/<name>.yaml --adapter mock
python3 scripts/package_release.py workshop/runs --before /path/to/deployed/skill
```

For real model runs, use `--adapter command` and separate target/optimizer commands.

## Non-negotiables

- Validation split gates edits; test split is report-only.
- Rejected edits feed the next epoch as negative feedback.
- Rubric judges are blind, pairwise, and independent when possible.
- The release package is the review artifact before shipping.
