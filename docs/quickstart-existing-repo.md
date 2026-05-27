# Quickstart: Improve Skills in an Existing Repo

Use this when a repo already has one or more `SKILL.md` files and you want the fastest useful result.

## 1. Start with guided triage

```bash
python3 scripts/start.py /path/to/repo --out inventory.md
```

This discovers skills, writes an inventory, and recommends one next action. The first win is usually **not** the full SkillOpt loop; it is a lite revision with smoke tests.

## 2. Scaffold the lite path for one skill

```bash
python3 scripts/lite_improve.py /path/to/repo/.claude/skills/some-skill
```

This creates:

```txt
workshop/skills/<name>/          # copy to edit, never the deployed source
workshop/evals/<name>-smoke-tests.md
records/{accepted,rejected,snapshots,releases}/
```

## 3. Audit qualitatively

Run `prompts/audit/skill_audit.md` in a fresh context against the copied skill and the static findings from `inventory.md`.

Output should be:

- keep / revise / split / retire
- lite path / full loop
- 3 smoke tests with observable criteria

## 4. Make one bounded patch

Use small local edits only: `replace`, `append`, `prepend`, `insert_after`, or `delete`. Avoid broad rewrites unless the skill is structurally broken.

## 5. Package the release

```bash
python3 scripts/package_release.py workshop/skills/<name> --before /path/to/deployed/skill
```

Review `records/releases/<name>@<timestamp>/` before shipping.

## 6. Only then consider the full loop

Run the scored loop only if all hold:

1. reuse ≥ ~10x,
2. objective/rubric verifier exists,
3. recurring real failures exist.

If any are false, stop at the lite path.
