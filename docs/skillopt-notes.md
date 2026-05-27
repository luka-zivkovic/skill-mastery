# SkillOpt Notes

Source paper: **SkillOpt: Executive Strategy for Self-Evolving Agent Skills**, arXiv:2605.23904. See [arXiv](https://arxiv.org/abs/2605.23904), [PDF](https://arxiv.org/pdf/2605.23904), [project page](https://microsoft.github.io/SkillOpt/), and [GitHub](https://github.com/microsoft/SkillOpt).

## Core idea

SkillOpt treats a skill as trainable external state. The base agent remains fixed; the optimizer changes only the skill artifact based on scored task trajectories.

## Mechanism

1. Collect task trajectories with scores.
2. Split examples into train, validation/selection, and test.
3. Analyze failed trajectories and successful trajectories separately.
4. Merge analyses into candidate textual edits.
5. Rank edits and apply a bounded number of patches.
6. Evaluate the edited skill on held-out validation tasks.
7. Accept only strict improvements; reject ties and regressions.
8. Preserve rejected edits as negative feedback for future optimizer passes.

## Practices worth adopting

- Use validation gates for skill edits.
- Make edits patch-sized, not rewrite-sized.
- Keep deployed skills compact and inspectable.
- Store optimizer memory outside the deployed skill where possible.
- Maintain a rejected-edit buffer.
- Forward-test using fresh agents or fresh contexts to avoid leakage.
- Treat eval data and trajectories as first-class assets.

## What we implemented — and what stays out of reach

- **The mechanism is implemented** (`scripts/skillopt_run.py`, see `runner.md`): epochs,
  scored rollouts, minibatch reflection, bounded edits, cosine edit-budget schedule,
  tiered held-out gate, score cache, rejected-edit buffer, slow/meta update, and
  `best_skill.md` export. The discipline around it (snapshots, attribution, audit) ships too.
- **The paper's numbers stay out of reach:** the headline gains (avg +17.6 pts; ablating
  the slow-update region cost −22.5 pts on SpreadsheetBench) came from an **automatic
  objective verifier** over hundreds of held-out items. We supply the loop, not that
  verifier or those datasets — so scoring is yours, via verifiability **tiers**: a real
  check for `objective`, a blind pairwise different-model judge for `rubric`, and no scored
  gate for `subjective` (lite path). A handful of cases graded by the model under
  optimization is noise and self-grading; don't quote the paper's numbers as outcomes here.

## Important limits

- The loop depends on reliable feedback signals.
- Poor eval splits can overfit skills to local quirks.
- A single skill can become incoherent if it tries to cover too many heterogeneous domains.
- Compact skills are easier to deploy, but may need references/scripts/assets for deeper workflows.
