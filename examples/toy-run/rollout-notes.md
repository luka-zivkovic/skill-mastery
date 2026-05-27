# Rollout notes — toy-skill, epoch 1 (2026-06-01)

Tier: `rubric` (output quality judged against a fixed rubric; no objective verifier).
Ran the train split with the current skill and looked for the *recurring* failure across
the minibatch — not one-off anecdotes.

## Train failures observed

- **train-002** (commit one file): answer was correct but **omitted the self-check line**.
- **train-004** (grep in a directory): four steps instead of three; no self-check.

Recurring pattern: under mild pressure the skill **drops the self-check** and **lets the
step count drift past three**. Both are behaviors the Constraints section *names* but does
not defend — there is no "failure modes" reminder, so the model treats them as soft.

## Candidate edits proposed

- **E1 (accepted):** add a `## Known failure modes` section spelling out the two recurring
  misses. Generalizable, ties directly to the observed failures.
  → `records/accepted/0001-add-failure-modes.json`
- **E2 (rejected):** add a step-5 rule specific to README-verification tasks. Surfaced by
  **val-001** alone, helps no other case, and hardcodes one task type into a general skill.
  Overspecification — the SkillOpt anti-pattern.
  → `records/rejected/0001-overspec-readme-rule.json` (in the buffer; do not re-propose this epoch)

See `records/eval_results.jsonl` for the blind pairwise grades and the gate decisions, and
`records/snapshots/toy-skill@2026-06-01.md` for the accepted skill + slow-update note.
