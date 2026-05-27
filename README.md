# Skill Mastery

Skill QA and lifecycle tooling for Claude/Codex skills.

This repository provides small, dependency-free scripts for creating, auditing,
validating, changing, and packaging agent skills. The goal is not to make skills
rewrite themselves. The goal is to make skill changes inspectable: what changed,
why it changed, what evidence supports it, and whether it shipped back to the
place where the agent actually loads the skill.

```txt
create or audit -> workshop copy -> smoke tests -> bounded patch -> release package -> ship
```

## Status

- Python 3.9+.
- No third-party runtime dependencies.
- Designed for Claude/Codex style skills that use `SKILL.md` plus optional
  `references/`, `scripts/`, and `assets/` resources.
- The default workflow is the lite path: audit, smoke-test, patch, package.
- The scored optimization loop is available, but should only be used when a
  reliable verifier exists.

## Why this exists

Agent skills are useful because they move recurring workflow knowledge out of a
single prompt and into a versioned artifact. Once a team has more than a few
skills, the maintenance problem starts to look like software maintenance:

- Which skills exist?
- Which skills are too broad, too long, stale, or hard to route?
- Which changes were accepted or rejected?
- What evidence says a change improved behavior?
- Did the accepted change get copied back to the deployed skill?

This project treats skills as lifecycle-managed artifacts. It provides the basic
QA layer around them: creation helpers, static audits, smoke tests, bounded
patches, history, release packages, and optional evaluation gates.

## Relationship to SkillOpt

This repository was influenced by
[SkillOpt: Executive Strategy for Self-Evolving Agent Skills](https://arxiv.org/abs/2605.23904).
SkillOpt's useful contribution is the framing: a skill can be external state that
is improved through repeated attempts, failure analysis, candidate edits,
validation, rejected-edit memory, and snapshots.

The difference is the operating assumption.

SkillOpt is primarily an optimization loop. It works best when there is a task
distribution and an automatic verifier that can repeatedly score candidate skill
versions. That is a reasonable benchmark setup, but it is not how many production
skills behave. A skill for PR review, issue triage, bug reproduction, coding
conventions, support workflows, or design review often has partial evidence,
human judgment, mutable repositories, and side effects.

Skill Mastery keeps the parts of the SkillOpt idea that are useful in real
repositories, but puts a QA and lifecycle workflow first.

| Area | SkillOpt-style loop | Skill Mastery |
|---|---|---|
| Primary goal | Improve benchmark score through iterative optimization. | Make skill creation and maintenance reviewable, testable, and reversible. |
| Default path | Run repeated optimization epochs. | Use a lite workflow: audit, smoke tests, bounded patch, release package. |
| Evidence assumption | Objective verifier or benchmark scorer is available. | Evidence is tiered: objective, rubric, or subjective. |
| Human role | Mostly outside the loop. | Human review is expected before shipping. |
| Real repo fit | Best for stable tasks with repeatable scoring. | Designed for team skills with conventions, side effects, and changing codebases. |
| Output | Best-scoring skill version. | Release artifact with before/after snapshots, validation notes, checklist, and history. |

The optional full loop in this repo should be used only when all of these are
true: the skill is reused often, the team can define a real verifier or robust
rubric, and the skill has failed repeatedly in real use.

## Quickstart

```bash
git clone <this-repo>
cd skill-mastery
make check
```

Create a new skill workspace:

```bash
python3 scripts/create_skill.py pr-reviewer \
  --description "Review pull requests against repository conventions. Use when a user asks for PR review help." \
  --kind codex \
  --resources references,scripts
```

The helper creates:

```txt
workshop/skills/pr-reviewer/SKILL.md
workshop/skills/pr-reviewer/references/
workshop/skills/pr-reviewer/scripts/
workshop/evals/pr-reviewer-smoke-tests.md
workshop/evals/pr-reviewer-creation-brief.md
records/{accepted,rejected,snapshots,releases}/
```

After editing the draft and filling the smoke tests:

```bash
python3 scripts/validate_skill.py workshop/skills/pr-reviewer
python3 scripts/package_release.py workshop/skills/pr-reviewer
```

## Working with an existing repository

Run a read-only audit first:

```bash
python3 scripts/start.py /path/to/repo --out inventory.md
```

Then copy one deployed skill into the local workshop instead of editing it in
place:

```bash
python3 scripts/lite_improve.py /path/to/repo/.claude/skills/some-skill
```

After making a bounded change and recording smoke-test evidence, package the
change for review:

```bash
python3 scripts/package_release.py workshop/skills/some-skill \
  --before /path/to/repo/.claude/skills/some-skill
```

The release package is written to `records/releases/<skill>@<timestamp>/` and
contains:

```txt
before.md
after.md
validation-summary.md
ship-checklist.md
manifest.json
```

## Example: running against the n8n repository

The n8n repository is a useful example because it contains real team skills under
`.claude/plugins/n8n/skills/`. In a shallow sparse checkout of the current main
branch, the audit found 21 `SKILL.md` files under that path.

For a public repository like n8n, use Skill Mastery as an external bench first:
read the skill files, write reports locally, and do not modify the target repo.

```bash
# Clone only the Claude skill/plugin metadata needed for the audit.
git clone --depth 1 --filter=blob:none --sparse https://github.com/n8n-io/n8n /tmp/n8n
cd /tmp/n8n
git sparse-checkout set .claude

# Run skill-mastery from its own repository.
cd /path/to/skill-mastery
python3 scripts/audit_skills.py /tmp/n8n --out /tmp/n8n-skill-inventory.md
python3 scripts/start.py /tmp/n8n --out /tmp/n8n-start.md
```

To work on one n8n skill without touching the n8n checkout:

```bash
python3 scripts/lite_improve.py \
  /tmp/n8n/.claude/plugins/n8n/skills/create-skill \
  --name n8n-create-skill

python3 scripts/validate_skill.py workshop/skills/n8n-create-skill
python3 scripts/package_release.py workshop/skills/n8n-create-skill \
  --before /tmp/n8n/.claude/plugins/n8n/skills/create-skill
```

This produces a local review artifact. If the change is worth proposing upstream,
copy the final patch into a normal n8n branch and review it through n8n's usual PR
process.

## Evidence tiers

Every non-trivial change should declare what kind of evidence can support it.

| Tier | Verifier | Accept rule | Use when |
|---|---|---|---|
| `objective` | Script, test, exact match, schema check, exit code | Strict validation improvement | Deterministic outputs or executable checks. |
| `rubric` | Blind pairwise judge, different model if possible, at least 3 runs | New version wins a majority every run | Quality is observable but not exactly checkable. |
| `subjective` | No reliable scorer | No scored gate | Taste, prose, broad judgment, one-off work. |

Do not grade a rubric edit with the same model context that produced it. For
subjective changes, record the review notes, but do not claim a measured gain.

## Commands

| Command | Purpose |
|---|---|
| `make check` | Run validators, unit tests, and a mock loop. |
| `make new-skill NAME=my-skill DESCRIPTION="Do X. Use when..."` | Shortcut for creating a new workshop skill. |
| `python3 scripts/create_skill.py <name> --description "..."` | Create a new skill plus smoke tests and creation checklist. |
| `python3 scripts/start.py <repo>` | Guided first-run triage for existing skills. |
| `python3 scripts/audit_skills.py <repo>` | Raw static audit report. |
| `python3 scripts/lite_improve.py <skill>` | Copy a skill into the workshop and create smoke-test scaffolding. |
| `python3 scripts/package_release.py <skill>` | Create a reviewable release package. |
| `python3 scripts/validate_skill.py <skill>` | Validate skill structure against Agent Skills conventions. |
| `python3 scripts/record_eval_result.py records ...` | Append tier-aware eval evidence. |
| `python3 scripts/summarize_skill_history.py records` | Summarize accepted/rejected/eval history. |
| `python3 scripts/skillopt_run.py <skill> <manifest>` | Run the optional scored loop. |

## Repository layout

```txt
CLAUDE.md                  Operating contract for this repository
docs/                      Quickstarts, lite/full-loop guides, runner notes
templates/                 Claude/Codex skill templates and eval manifest template
prompts/audit/             Qualitative audit prompt and smoke-test generation
prompts/optimizer/         Failure/success/rank/merge/slow-update prompts
scripts/                   CLIs for create, audit, start, lite, package, validate, run
examples/                  Toy skill, eval manifest, and worked run
workshop/                  Temporary skill copies, evals, and run outputs
records/                   Accepted/rejected patches, snapshots, releases, eval history
tests/                     Standard-library unittest suite
```

## Development

```bash
make check
make test
make demo
make audit
make start
make new-skill NAME=my-skill DESCRIPTION="Do X. Use when..."
```

CI runs `scripts/doctor.py`.

## Scope

This repository is skill QA and lifecycle tooling. It is not a claim that skills
should autonomously rewrite themselves, and it is not a reproduction of
SkillOpt's benchmark results. Do not quote SkillOpt's reported gains as outcomes
of this repository. Use the full optimization loop only when the evaluation setup
is strong enough to justify it.
