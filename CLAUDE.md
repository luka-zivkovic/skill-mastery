# Skill Mastery — Operating Contract

This repo is **skill QA and lifecycle tooling** for Claude/Codex skills. It helps teams audit, create, smoke-test, patch, package, and ship skill changes with evidence. SkillOpt inspired the bounded-edit/scored-loop machinery, but the repo's identity is not self-evolving skills. These rules are binding whenever you work here, for **both** Codex skills (`templates/codex-skill/`) and Claude skills (`templates/claude-skill/`).

## What this repo is — and is not

- It **is** skill QA and lifecycle tooling: guided audits, actionable triage, smoke-test scaffolding, bounded patches, accepted/rejected history, snapshots, release packages, and an optional SkillOpt-style scored loop for verifier-backed cases.
- It is **not** a self-evolving-skills product or a reproduction of the paper's results. SkillOpt's reported gains (+19 to +25 pts on GPT-5.5, depending on harness) came from automatic verifiers over benchmark datasets we don't ship. Do not quote those numbers as outcomes of this repo, and do not call ordinary lite-path maintenance "optimization." When a scored loop is justified, prefer driving the official `microsoft/SkillOpt` package via `scripts/skillopt_bridge.py` over the legacy in-repo loop.

## Hard rules

1. **No blind edits.** Never edit a deployed skill in place. Iterate on a copy in `workshop/skills/`, add smoke-test or validation evidence, and package the release before shipping back.
2. **Declare the evidence level first.** Lite-path work records smoke-test evidence. Full-loop work uses an eval manifest with `verifiability: objective | rubric | subjective`; the gate's rigor scales to the tier. If you can't name the evidence level, you're not ready to change the skill.
3. **Rubric grading must be blind, pairwise, and independent.** Compare old-skill output vs new-skill output as unlabeled A/B with randomized order, scored against a fixed rubric. Use a **different model** than the one under optimization when available (e.g. optimizer = Opus → judge = Sonnet/Haiku, or cross-provider). If a different model isn't available, fall back to a **fresh-context** invocation of the same model and **log the caveat** in the run record. The editor never grades its own edit.
4. **Respect the gate by tier.** Accept only what the tier's accept-rule allows. Ties and regressions are rejected.
5. **Rejected edits are mechanical negative feedback.** Every rejected edit goes to `records/rejected/` and MUST be pasted into the next failure-analysis pass so it isn't re-proposed this epoch. `summarize_skill_history.py` prints the block to copy.
6. **Don't peek at the test split.** It is for periodic unbiased checks only and is hash-locked. Accept/reject decisions use the validation split.
7. **Bounded patches only.** Use `replace / append / prepend / insert_after / delete` via `scripts/apply_skill_patch.py`. Reject broad rewrites unless the skill is structurally broken.
8. **Slow-update region is protected.** Single-pass edits never overwrite the `## Slow-update` section. Every slow-update note must cite ≥2 validation examples and carry a date; un-cited notes are flagged for pruning.
9. **Sync back or it didn't ship.** Before optimizing, `scripts/sync_skill.py` must confirm the local copy matches the deployed skill's hash. On acceptance, emit the patch for the deployed location and record whether it shipped.

## Verifiability tiers (the gate scales to the tier)

| Tier | Verifier | Accept rule |
|------|----------|-------------|
| `objective` | Script / test / exit-code / exact-or-JSON match | Strict-greater on held-out validation (full SkillOpt loop). |
| `rubric` | Blind pairwise judge, different model if possible, n≥3 runs | New wins majority of pairwise comparisons across validation AND no regression run. |
| `subjective` | None possible | **Scored gate disabled.** Use the lite path; this is qualitative review, not optimization. |

## Auditing an existing repo's skills

When this kit is added to a repo that already has skills, **audit before optimizing**.
Run `scripts/start.py <root> --out inventory.md` for guided triage, or
`scripts/audit_skills.py <root>` for the raw mechanical report. Then run
`scripts/lite_improve.py path/to/skill` for one keeper, use `prompts/audit/skill_audit.md`
for the qualitative pass + 3 smoke tests, apply one bounded patch, and package the review
artifact with `scripts/package_release.py`. Triage to keep / revise / split / retire, then
apply the ROI gate. Full workflow in `docs/auditing-existing-skills.md`. Smoke tests are
the default test story; the scored loop is the exception.

## Creating a new skill

Use `scripts/create_skill.py <name> --description "..."` instead of copying templates by
hand. It creates the workshop draft, fills frontmatter, scaffolds smoke tests and a
creation brief, creates records folders, and validates the draft. Keep helper/checklist
artifacts in the workshop; the shipped skill should remain a compact `SKILL.md` plus only
the resources it actually needs.

## When to run the full loop vs. the lite path

Run the full scored loop only when **all** hold: reuse ≥ ~10×, an `objective` or `rubric` verifier exists, and the skill has failed ≥2× in real use. See `docs/when-to-optimize.md`.

Otherwise use the **lite path** (the default): write a tight skill once, add ~3 smoke-test prompts, revise on observed failure. Don't manufacture an optimization loop for a skill you'll run twice.

## Map

- `docs/` — quickstarts, lite/full-loop guides, integration/onboarding, runner, operating principles, lifecycle, when-to-optimize, auditing-existing-skills, paper notes.
- `templates/` — `codex-skill/`, `claude-skill/`, `eval-manifest.yaml`.
- `prompts/optimizer/` — analysis, merge, rank, slow-update, and `rubric_judge.md`.
- `prompts/audit/` — `skill_audit.md` (qualitative audit + smoke-test generation).
- `scripts/` — `start.py`, `create_skill.py`, `lite_improve.py`, `package_release.py`, `skillopt_run.py` (the loop) + adapters/manifest/skilltext, `integrate.py`, validators, `audit_skills.py`, patcher, recorder, history summary, `sync_skill.py`, `doctor.py`.
- `tests/` — stdlib unit tests; `make check` / `python3 scripts/doctor.py` runs everything.
- `workshop/` — where the loop runs: `skills/`, `evals/`, `runs/`.
- `records/` — accepted / rejected patches, snapshots, `eval_results.jsonl`.
- `examples/` — toy skill, tiered eval manifest, and `toy-run/` (one full loop, worked end to end).
