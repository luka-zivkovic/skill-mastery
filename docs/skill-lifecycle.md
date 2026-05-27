# Skill Lifecycle

## 1. Create

Define concrete user requests that should trigger the skill. Start with the helper so the
draft is born in the workshop with smoke tests and a creation checklist:

```bash
python3 scripts/create_skill.py my-skill \
  --description "Do the focused workflow. Use when the user asks for the specific trigger." \
  --kind claude
```

Then draft a compact `SKILL.md`, add only required resources, and validate metadata.

## 2. Seed evals

First decide whether to optimize at all (`when-to-optimize.md`): the full loop needs reuse
≥ ~10×, a verifier, and ≥2 real failures. Otherwise take the lite path and stop here.

Create a manifest with train, validation, and test tasks. Declare a `verifiability` tier
(`objective` / `rubric` / `subjective`) and set the matching `accept_rule`. For scored
tiers, validation and test need ≥ 8 cases each and `grading_runs` ≥ 3. Include prompts,
success criteria, optional fixtures, and (for rubric) the `rubric.criteria`. Record the
`source`/`deployed` provenance so drift can be detected.

## 3. Run and collect

For each task, save the prompt, skill version, model/backend, trajectory notes, final output, and score.

## 4. Analyze

Analyze failures first. Identify missing instructions, ambiguous rules, brittle workflows, bad resource choices, and places where deterministic scripts would help. Analyze successes separately to preserve behavior that already works.

## 5. Patch

Generate a small candidate patch. Apply it to a copy of the skill. Record the patch with rationale.

## 6. Validate

Run validation tasks and apply the **tier's** gate:

- `objective`: run the verifier over ≥3 runs; accept iff the mean improves and no run
  regresses.
- `rubric`: grade old-vs-new **blind, pairwise, randomized order**, with a **different
  model if available** (`prompts/optimizer/rubric_judge.md`, `record_eval_result.py`);
  accept iff NEW wins a majority every run.
- `subjective`: no scored gate — review qualitatively; do not claim a measured gain.

Reject ties, regressions, and unverifiable changes. Store rejected patches with the reason
in `records/rejected/` and paste them into the next analysis pass so they aren't reproposed.

## 7. Snapshot

Snapshot accepted skill versions before the next optimization epoch.

## 8. Maintain

Periodically prune stale instructions, move bulky detail into references, add scripts for repeated fragile work, and refresh evals when real usage changes.

## 9. Package and ship

Before touching the deployed skill, create a reviewable release package:

```bash
python3 scripts/package_release.py workshop/skills/<name> --before /path/to/deployed/skill
```

The package gives reviewers the before/after diff material, validation summary, and ship
checklist in one place. If the change never ships back to the deployed skill, it does not
count as an improvement.
