#!/usr/bin/env python3
"""Scaffold the default real-world skill improvement path.

Copies a deployed skill into workshop/skills/, creates a smoke-test worksheet,
and creates records folders. It does not run a model and does not edit the
source skill.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store', 'records')


def skill_dir_from(path: Path) -> Path:
    return path.parent if path.name == 'SKILL.md' else path


def scaffold(source: Path, name: str | None = None, force: bool = False, root: Path = ROOT) -> dict[str, Path]:
    source = skill_dir_from(source).resolve()
    if not (source / 'SKILL.md').exists():
        raise FileNotFoundError(f'no SKILL.md found at {source}')
    skill_name = name or source.name
    dest = root / 'workshop' / 'skills' / skill_name
    evals = root / 'workshop' / 'evals'
    records = root / 'records'

    if dest.exists():
        if not force:
            raise FileExistsError(f'{dest} already exists; pass --force to replace it')
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, ignore=IGNORE)

    evals.mkdir(parents=True, exist_ok=True)
    smoke = evals / f'{skill_name}-smoke-tests.md'
    if force or not smoke.exists():
        smoke.write_text(smoke_template(skill_name, source), encoding='utf-8')

    for rel in ('accepted', 'rejected', 'snapshots', 'releases'):
        (records / rel).mkdir(parents=True, exist_ok=True)
        keep = records / rel / '.gitkeep'
        if not keep.exists():
            keep.touch()

    checklist = dest / 'LITE_IMPROVE.md'
    checklist.write_text(checklist_template(skill_name, source, smoke), encoding='utf-8')
    return {'skill_copy': dest, 'smoke_tests': smoke, 'checklist': checklist, 'records': records}


def smoke_template(skill_name: str, source: Path) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    return f'''# Smoke tests — {skill_name}

Source skill: `{source}`
Created: {today}

Use these for the **lite path**. They are not a scored SkillOpt gate; they are the cheap
regression net you run before/after a bounded patch.

| ID | Prompt | Observable pass criterion | Catches |
|----|--------|---------------------------|---------|
| smoke-001 | Replace with the skill's most common trigger request. | The answer follows the core workflow and required output shape. | Core path drift |
| smoke-002 | Replace with an edge case or known failure mode. | The answer avoids the named pitfall. | Missing guardrail |
| smoke-003 | Replace with a near-miss request that should not invoke this skill. | The answer does not over-apply the skill. | Bad routing / overspec |

## Result log

- Baseline:
- Patch tried:
- After patch:
- Decision: keep / accept / reject / needs more evidence
'''


def checklist_template(skill_name: str, source: Path, smoke: Path) -> str:
    return f'''# Lite improvement checklist — {skill_name}

Source: `{source}`
Smoke tests: `{smoke}`

1. Run/paste `prompts/audit/skill_audit.md` against this copy and its static audit findings.
2. Fill in the 3 smoke tests before changing the skill.
3. Apply one bounded patch only (`replace`, `append`, `prepend`, `insert_after`, `delete`).
4. Re-run the smoke tests in a fresh context.
5. Record accepted/rejected evidence under `records/`.
6. Package the release:

```bash
python3 scripts/package_release.py workshop/skills/{skill_name} --before {source}
```

Do not run the full scored loop unless `docs/when-to-optimize.md` says the ROI gate passes.
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill', type=Path, help='skill directory or SKILL.md path')
    parser.add_argument('--name', default=None, help='workshop skill name; defaults to source folder name')
    parser.add_argument('--force', action='store_true', help='replace an existing workshop copy')
    args = parser.parse_args()
    try:
        out = scaffold(args.skill, name=args.name, force=args.force)
    except (OSError, FileNotFoundError, FileExistsError) as exc:
        print(f'ERROR: {exc}')
        return 1
    print('Lite path scaffolded:')
    for label, path in out.items():
        print(f'- {label}: {path}')
    print('\nNext: fill the smoke tests, run the audit prompt, make one bounded patch, then package the release.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
