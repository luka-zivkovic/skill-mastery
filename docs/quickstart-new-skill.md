# Quickstart: Create a New Skill

Use this when no deployed skill exists yet.

## 1. Run the creation helper

```bash
python3 scripts/create_skill.py my-skill \
  --description "Do the focused workflow. Use when the user asks for the specific trigger." \
  --kind claude \
  --resources references,scripts
```

The helper copies the right template into `workshop/skills/`, fills frontmatter,
creates optional resource folders, scaffolds smoke tests, writes a creation
brief/checklist, creates records folders, and runs structural validation.

## 2. Fill only what changes behavior

A good first skill has:

- a specific trigger description,
- a short workflow,
- tool policies or house conventions,
- output constraints,
- known failure modes,
- optional references/scripts/assets for bulky detail.

Do not write a long guide in `SKILL.md`. Use progressive disclosure.

## 3. Add smoke tests

Fill `workshop/evals/my-skill-smoke-tests.md` with 3 prompts:

1. common trigger,
2. edge/failure-mode case,
3. near-miss that should not over-trigger the skill.

## 4. Validate and ship

```bash
python3 scripts/validate_skill.py workshop/skills/my-skill
python3 scripts/package_release.py workshop/skills/my-skill
```

Ship once the smoke tests pass. Do not build a scored loop until the skill has real repeated use and real failures.
