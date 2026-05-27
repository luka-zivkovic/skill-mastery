# Integration & Onboarding

How skill-mastery actually gets used. There are two modes; pick by whether you want the
discipline to live *inside* the target repo or to keep skill-mastery as an external bench.

## Mode 1 — Embed (recommended for repos with real, evolving skills)

Vendor the toolkit into the target repo so the contract auto-loads where skills are built.

```bash
# from the skill-mastery repo
python3 scripts/integrate.py /path/to/target-repo
```

This copies the toolkit into `target-repo/.skill-mastery/`, injects a "Skill discipline"
block into the target's root `CLAUDE.md` (between managed markers — your other content is
untouched), and seeds `.skill-mastery/inventory.md` from an audit of the repo's existing
skills. Re-running refreshes the toolkit and the managed block; it's idempotent. Commit
`.skill-mastery/` and the `CLAUDE.md` change so the team shares one contract.

After that, everything runs from inside the target repo:

```bash
python3 .skill-mastery/scripts/start.py . --out .skill-mastery/inventory.md
python3 .skill-mastery/scripts/create_skill.py my-skill --description "Do X. Use when..."
python3 .skill-mastery/scripts/audit_skills.py .
python3 .skill-mastery/scripts/validate_skill.py path/to/some-skill
```

**Why embed:** the goal is to change how skills get created and maintained *in that repo*.
That only happens if `CLAUDE.md` carries the rules where the work is. An external audit can
inspect but can't shape behavior.

## Mode 2 — External bench (one-off audits, no commitment)

Keep skill-mastery standalone and point its scripts at other repos. Nothing is written to
the target.

```bash
python3 scripts/audit_skills.py /path/to/other-repo --out inventory.md
```

Good for a quick triage, a review, or deciding whether a repo's skills are worth the embed.
You can also pull a single skill into this repo's `workshop/skills/` to iterate, then hand
the resulting patch back. Use this when you don't want to add files to the target.

## Onboarding an EXISTING repo (the common case)

1. `python3 scripts/integrate.py <repo>` (Mode 1) — or Mode 2 for a dry look first.
2. Read `.skill-mastery/inventory.md`: the `PASS/WARN/FAIL` triage of current skills.
3. For the recommended keeper, run
   `python3 .skill-mastery/scripts/lite_improve.py path/to/skill`, then run
   `prompts/audit/skill_audit.md` (fresh context) → 3 smoke tests into the generated
   `.skill-mastery/workshop/evals/<name>-smoke-tests.md`. That's the regression net for
   most skills.
4. Triage the rest: revise (bounded patches on a copy), split, or retire.
5. Package accepted changes with `package_release.py` before shipping.
6. Only run the full scored loop where the ROI gate holds (`docs/when-to-optimize.md`).

## Onboarding a FRESH repo

- **A product repo, skills as a side concern:** run `integrate.py` on day zero. The audit
  finds nothing yet; you get the contract, templates, and workshop ready. Author new skills
  with `.skill-mastery/scripts/create_skill.py`, fill the generated smoke tests, and ship.
  Reach for the loop later, only if a skill earns it.
- **A dedicated skills repo:** just use skill-mastery itself as the base — build skills in
  `workshop/skills/`, keep evals and records here, and deploy out to wherever they run.

## What "deployed" means and syncing back

A skill's deployed location is wherever the agent loads it (e.g. `.claude/skills/<name>/`,
a Codex skill dir, a plugin). Record that path + content hash in the eval manifest's
`source`/`deployed` blocks. Before optimizing, `scripts/sync_skill.py check` refuses to
start if your workshop copy has drifted; on acceptance it emits the patch for the deployed
path, so improvements don't die in `records/`.

## Updating the toolkit later

Re-run `integrate.py` against the repo to pull newer scripts/docs/templates. The managed
CLAUDE.md block is replaced in place; your evals, records, and workshop copies are left
alone (they live in skeleton dirs that aren't overwritten).
