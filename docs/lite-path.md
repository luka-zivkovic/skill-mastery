# The Lite Path

The lite path is the default workflow for real skills.

```txt
audit → copy to workshop → 3 smoke tests → one bounded patch → package release → ship
```

Use it when:

- the skill is new,
- the skill has low/unknown reuse,
- no reliable verifier exists,
- the change is a small cleanup,
- failures are qualitative or subjective.

## Commands

```bash
python3 scripts/start.py /path/to/repo --out inventory.md
python3 scripts/lite_improve.py /path/to/skill
python3 scripts/package_release.py workshop/skills/<name> --before /path/to/skill
```

## Evidence standard

A lite-path change needs:

- the static audit finding or observed failure,
- 3 smoke tests,
- before/after notes,
- a bounded patch,
- a release package.

It does **not** need train/validation/test splits or optimizer epochs.

## When to reject a lite patch

Reject when it:

- hardcodes a single example,
- broadens the skill to unrelated domains,
- bloats `SKILL.md` instead of using references/scripts,
- changes the protected slow-update region outside the consolidation flow,
- lacks smoke-test evidence.
