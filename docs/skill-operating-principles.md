# Skill Operating Principles

## Two layers: discipline vs. the scored loop

Separate what **always** applies from what applies **only with a verifier**:

- **Discipline (always).** Bounded patches, snapshots, change attribution, compact
  inspectable skills, a protected slow-update region, and knowing when not to bother.
  This transfers to every skill.
- **The scored optimization loop (verifier-gated).** Rollout → reflect → bounded edits →
  held-out gate → accept/reject. This transfers **only** when an objective or rubric
  verifier exists. Without one, the "gate" is the model grading its own work — theater.
  See `when-to-optimize.md`.

## Verifiability tiers

Every eval declares a tier; the gate's rigor scales to it.

| Tier | Verifier | Accept rule |
|------|----------|-------------|
| `objective` | script / test / exact-or-JSON match | strict-greater on held-out validation |
| `rubric` | blind pairwise judge, different model if possible, n≥3 runs | NEW wins a majority every run, no regression |
| `subjective` | none possible | no scored gate — qualitative review only |

Never grade a `rubric` edit with the same model+context that produced it. Grade blind,
pairwise (old vs new, order randomized), with a different model when available; otherwise
a fresh context, logged as a caveat.

## Use skills deliberately

Use a skill when the task needs durable procedural knowledge, domain-specific references, deterministic tools, or reusable assets. Do not use a skill merely because the task is related by topic.

## Keep the deployed skill lean

A Codex skill should contain only what another agent needs at execution time:

- `SKILL.md` with concise instructions.
- Optional `agents/openai.yaml` UI metadata.
- Optional `scripts/`, `references/`, and `assets/` resources.

Keep eval logs, changelogs, accepted patches, rejected patches, and optimizer memory outside the deployed skill package.

## Progressive disclosure

Put core routing and workflow instructions in `SKILL.md`. Put long examples, schemas, APIs, and variants into directly linked reference files. Prefer scripts for repeated fragile operations.

## Patch discipline

Skill changes should be small and attributable. Prefer these operations:

- `replace`: exchange exact text for better text.
- `append`: add a small section to the end of a file.
- `prepend`: add context at the start of a file.
- `insert_after`: add text after an exact anchor.
- `delete`: remove exact text.

Reject broad rewrites unless the skill is structurally broken.

## Evaluation discipline

Every serious skill should have:

- Train tasks for discovering issues.
- Validation tasks for accepting/rejecting candidate edits.
- Test tasks for periodic unbiased checks.
- Scoring criteria explicit enough for another agent to apply.

Accept a skill edit only when validation improves and no critical regression appears.

Anti-noise guardrails (enforced by `validate_eval_manifest.py` / `record_eval_result.py`):

- Objective/rubric validation and test splits need ≥ 8 cases — a 1–2 case gate is noise.
- Grade ≥ 3 independent runs per task; accept only if the mean improves AND no single run
  regresses. One lucky run never flips a gate.

## Slow-update region is protected — and must not rot

The protected `## Slow-update` region holds durable cross-iteration lessons. SkillOpt's own
ablation shows getting this region wrong is the highest-blast-radius failure. Rules:

- Only the epoch-end slow-update step writes here; single-pass edits never overwrite it.
- Every note cites ≥ 2 validation examples and carries a date.
- `summarize_skill_history.py --skill <dir>` flags undated or under-cited notes for pruning.

## Sync back, or it didn't ship

Iterate on copies in `workshop/skills/`. Before optimizing, `sync_skill.py check` must
confirm the copy matches the deployed skill's hash (no stale-base edits). On acceptance,
emit the patch for the deployed location and record whether it shipped — otherwise
improvements die in `records/`.
