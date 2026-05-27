# Example: running skill-mastery against the n8n repository

[n8n](https://github.com/n8n-io/n8n) is a useful external test case because it
contains real team skills under `.claude/plugins/n8n/skills/`. In a shallow sparse
checkout of the current main branch, `audit_skills.py` found 21 `SKILL.md` files
under that path.

Use the external bench mode first: read the n8n skill files, write reports
locally, and do not modify the n8n checkout.

```bash
# 1. Clone only the Claude plugin/skill metadata needed for inspection.
git clone --depth 1 --filter=blob:none --sparse https://github.com/n8n-io/n8n /tmp/n8n
cd /tmp/n8n
git sparse-checkout set .claude

# 2. Run skill-mastery from its own repository.
cd /path/to/skill-mastery
python3 scripts/audit_skills.py /tmp/n8n --out /tmp/n8n-skill-inventory.md
python3 scripts/start.py /tmp/n8n --out /tmp/n8n-start.md
```

To work on one n8n skill without touching the checkout:

```bash
python3 scripts/lite_improve.py \
  /tmp/n8n/.claude/plugins/n8n/skills/create-skill \
  --name n8n-create-skill

python3 scripts/validate_skill.py workshop/skills/n8n-create-skill
python3 scripts/package_release.py workshop/skills/n8n-create-skill \
  --before /tmp/n8n/.claude/plugins/n8n/skills/create-skill
```

The result is a local release package under `records/releases/`. If the change is
worth proposing upstream, copy the final patch into a normal n8n branch and use
n8n's usual pull request process.

Do not run the scored loop until there is a real eval manifest and an appropriate
objective or rubric verifier. See `docs/when-to-optimize.md` and `docs/runner.md`.
