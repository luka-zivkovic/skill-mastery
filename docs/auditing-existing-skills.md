# Auditing Existing Skills

When you drop skill-mastery into a repo that already has skills, start here. The goal is
**triage**, not a rewrite: find which skills are weak, decide which are worth attention,
and give the keepers a cheap regression net. Most of this is the discipline layer — no
verifier required.

## 1. Discover + static audit (mechanical)

```bash
python3 scripts/start.py . --out inventory.md       # recommended first-run path
python3 scripts/audit_skills.py .                 # or a path to another repo
python3 scripts/audit_skills.py . --out inventory.md
```

`start.py` wraps the static audit and prints the recommended next command for one skill.
`audit_skills.py` finds every `SKILL.md`, grades each `PASS/WARN/FAIL`, estimates token
budget, lists structural/heuristic gaps, suggests a verifiability tier, and now adds an
operator-facing verdict (`keep` / `revise` / `split` / `retire`). `--fail-on warn` makes
it a CI gate. This catches: missing frontmatter, thin/bloated skills, no failure-modes
section, no protected slow-update region, big inline blocks that should be references.

A clean grade means *well-formed*, not *correct*. Correctness is what smoke tests and evals
are for.

Structural checks follow the [Agent Skills spec](https://code.claude.com/docs/en/skills):
`name` is optional (defaults to the directory name) and may be plugin-namespaced
(`plugin:skill`); `description` is recommended and may be a multi-line block scalar; and
fields like `allowed-tools`, `argument-hint`, `when_to_use`, `model`, and `paths` are all
valid. Only genuinely broken frontmatter is a FAIL — length, style, and missing sections
are warnings. (Validated against n8n's 23 real skills: 0 false FAILs.)

## 2. Qualitative audit + smoke tests (judgment)

For each skill worth keeping, scaffold the default workflow first:

```bash
python3 scripts/lite_improve.py /path/to/skill
```

Then run `prompts/audit/skill_audit.md` in a **fresh context** (one skill at a time). It
assesses what static checks can't — ambiguous routing, dead instruction, over-specification,
tool-policy gaps, missing failure modes — and drafts **3 smoke tests** (prompt + observable
pass criterion). Those smoke tests are the lite-path deliverable; write them to the
generated `workshop/evals/<name>-smoke-tests.md` and re-run them whenever the skill changes.
For most skills, this is the entire "test" story.

## 3. Triage decision per skill

- **keep** — clean and used; add smoke tests, move on.
- **revise** — fix the findings via bounded patches on a `workshop/skills/` copy.
- **split** — covers heterogeneous domains; break into focused skills.
- **retire** — unused or superseded; remove it (dead skills are routing noise).

## 4. Decide lite-path vs the full loop

Apply the `docs/when-to-optimize.md` gate: the scored loop only earns its cost when reuse
≥ ~10×, a verifier exists, and the skill has failed ≥2× for real. Otherwise the smoke
tests from step 2 are enough. Don't build an optimization loop for a skill you run twice.

## 5. Iterate without drift

Work on copies in `workshop/skills/`. Record the source/deployed hashes in the eval
manifest and run `scripts/sync_skill.py check` before optimizing, so edits are never
computed against a stale base and accepted improvements have a path back to the deployed
skill.

## 6. Package before shipping

After a lite-path patch or accepted loop result, create the review artifact:

```bash
python3 scripts/package_release.py workshop/skills/<name> --before /path/to/deployed/skill
```

The package under `records/releases/` contains `before.md`, `after.md`, a validation
summary, and a ship checklist. Review that package before copying changes into the
deployed skill.
