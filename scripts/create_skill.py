#!/usr/bin/env python3
"""Create a new skill workspace with the helper files people forget.

This is the creation on-ramp: copy a Claude/Codex template into workshop/skills,
fill the frontmatter, optionally create resource folders, scaffold smoke tests,
write a creation brief/checklist, create records folders, and validate the draft.
It never deploys the skill.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIRS = {'references', 'scripts', 'assets'}
NAME_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,62}$')


def normalize_name(value: str) -> str:
    """Normalize a title into the skill folder/name convention."""
    name = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    name = re.sub(r'-{2,}', '-', name)[:63].strip('-')
    if not name or not NAME_RE.match(name):
        raise ValueError('skill name must contain letters/digits and normalize to lowercase-hyphen form')
    return name


def parse_resources(raw: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if raw is None:
        return []
    items = raw if isinstance(raw, (list, tuple)) else raw.split(',')
    resources = [item.strip().lower() for item in items if item.strip()]
    unknown = sorted(set(resources) - RESOURCE_DIRS)
    if unknown:
        raise ValueError(f'unknown resource dir(s): {", ".join(unknown)}; use references,scripts,assets')
    return sorted(set(resources), key=resources.index)


def yaml_block(value: str, indent: str = '  ') -> str:
    collapsed = ' '.join(value.split())
    lines = textwrap.wrap(collapsed, width=78) or ['TODO: write a specific trigger description.']
    return '\n'.join(indent + line for line in lines)


def titleize(name: str) -> str:
    return ' '.join(part.capitalize() for part in name.split('-'))


def short_description(description: str, limit: int = 120) -> str:
    text = ' '.join(description.split())
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + '…'


def yaml_quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def rewrite_skill_md(path: Path, name: str, description: str) -> None:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    body = text
    if lines and lines[0].strip() == '---':
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == '---':
                body = '\n'.join(lines[i + 1:])
                break
    frontmatter = f'---\nname: {name}\ndescription: >-\n{yaml_block(description)}\n---\n\n'
    path.write_text(frontmatter + body.lstrip() + ('\n' if not body.endswith('\n') else ''), encoding='utf-8')


def write_openai_yaml(skill_dir: Path, name: str, description: str) -> None:
    agents = skill_dir / 'agents'
    if not agents.exists():
        return
    display = titleize(name)
    prompt = f'Use the {display} skill for requests matching its trigger description.'
    text = (
        f'display_name: {yaml_quote(display)}\n'
        f'short_description: {yaml_quote(short_description(description))}\n'
        f'default_prompt: {yaml_quote(prompt)}\n'
    )
    (agents / 'openai.yaml').write_text(text, encoding='utf-8')


def smoke_template(name: str, description: str) -> str:
    return f'''# Smoke tests — {name}

Skill status: new workshop draft
Trigger description: {description}

Fill these before shipping. They are the minimum regression net for a brand-new skill.

| ID | Prompt | Observable pass criterion | Catches |
|----|--------|---------------------------|---------|
| smoke-001 | Replace with the most common request that should trigger this skill. | The answer follows the intended workflow and output shape. | Core happy path |
| smoke-002 | Replace with an edge case or known failure mode. | The answer avoids the named pitfall. | Missing guardrail |
| smoke-003 | Replace with a near-miss request that should not trigger this skill. | The agent declines/routes normally instead of over-applying the skill. | Bad routing |

## Result log

- Baseline draft:
- Patch tried:
- After patch:
- Decision: ship / revise / hold
'''


def brief_template(name: str, kind: str, description: str, resources: list[str], skill_dir: Path, smoke: Path) -> str:
    res = ', '.join(resources) if resources else 'none yet'
    return f'''# Creation brief — {name}

Kind: `{kind}`
Skill draft: `{skill_dir}`
Smoke tests: `{smoke}`
Requested resource dirs: {res}

## Fill this before editing heavily

- Primary users:
- 3 requests that SHOULD trigger this skill:
  1.
  2.
  3.
- 3 near-miss requests that should NOT trigger this skill:
  1.
  2.
  3.
- Repeated/fragile operations that deserve scripts:
- Bulky domain details that belong in references:
- Assets/templates needed at runtime:

## Creation checklist

- [ ] `SKILL.md` description says both what the skill does and when to use it.
- [ ] Body is compact; bulky material is in `references/`, `scripts/`, or `assets/`.
- [ ] Known failure modes are explicit.
- [ ] Output constraints/tool policies are explicit when they matter.
- [ ] The three smoke tests are filled and run in a fresh context.
- [ ] `python3 scripts/validate_skill.py {skill_dir}` passes.
- [ ] `python3 scripts/package_release.py {skill_dir}` creates a review package before shipping.

## Initial trigger description

{description}
'''


def ensure_records(root: Path) -> Path:
    records = root / 'records'
    for rel in ('accepted', 'rejected', 'snapshots', 'releases'):
        d = records / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / '.gitkeep'
        if not keep.exists():
            keep.touch()
    return records


def create(name: str, description: str, kind: str = 'claude', resources: str | list[str] | tuple[str, ...] | None = None,
           force: bool = False, root: Path = ROOT, validate_draft: bool = True) -> dict:
    skill_name = normalize_name(name)
    if kind not in {'claude', 'codex'}:
        raise ValueError('kind must be claude or codex')
    if not description or not description.strip():
        raise ValueError('description is required; include concrete trigger conditions')
    resource_dirs = parse_resources(resources)

    template = root / 'templates' / f'{kind}-skill'
    if not template.exists():
        raise FileNotFoundError(f'missing template: {template}')

    dest = root / 'workshop' / 'skills' / skill_name
    if dest.exists():
        if not force:
            raise FileExistsError(f'{dest} already exists; pass --force to replace it')
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))

    rewrite_skill_md(dest / 'SKILL.md', skill_name, description)
    write_openai_yaml(dest, skill_name, description)
    for rel in resource_dirs:
        (dest / rel).mkdir(parents=True, exist_ok=True)
        keep = dest / rel / '.gitkeep'
        if not keep.exists():
            keep.touch()

    eval_root = root / 'workshop' / 'evals'
    eval_root.mkdir(parents=True, exist_ok=True)
    smoke = eval_root / f'{skill_name}-smoke-tests.md'
    brief = eval_root / f'{skill_name}-creation-brief.md'
    smoke.write_text(smoke_template(skill_name, description), encoding='utf-8')
    brief.write_text(brief_template(skill_name, kind, description, resource_dirs, dest, smoke), encoding='utf-8')
    records = ensure_records(root)

    errors: list[str] = []
    warnings: list[str] = []
    if validate_draft:
        errors, warnings = validate(dest, 500, 20000)

    return {
        'skill_dir': dest,
        'skill_md': dest / 'SKILL.md',
        'smoke_tests': smoke,
        'creation_brief': brief,
        'records': records,
        'validation_errors': errors,
        'validation_warnings': warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', help='skill name or title; normalized to lowercase-hyphen form')
    parser.add_argument('--description', required=True,
                        help='specific trigger description; include "Use when..." or equivalent conditions')
    parser.add_argument('--kind', choices=['claude', 'codex'], default='claude')
    parser.add_argument('--resources', default='', help='comma-separated optional dirs: references,scripts,assets')
    parser.add_argument('--force', action='store_true', help='replace an existing workshop draft')
    parser.add_argument('--no-validate', action='store_true', help='skip structural validation after creation')
    args = parser.parse_args()

    try:
        out = create(args.name, args.description, kind=args.kind, resources=args.resources,
                     force=args.force, validate_draft=not args.no_validate)
    except (OSError, ValueError, FileExistsError) as exc:
        print(f'ERROR: {exc}')
        return 1

    print('New skill workspace created:')
    for key in ('skill_dir', 'skill_md', 'smoke_tests', 'creation_brief', 'records'):
        print(f'- {key}: {out[key]}')
    if out['validation_errors']:
        print('\nValidation errors:')
        for err in out['validation_errors']:
            print(f'- ERROR: {err}')
        return 1
    if out['validation_warnings']:
        print('\nValidation warnings:')
        for warn in out['validation_warnings']:
            print(f'- WARN: {warn}')
    print('\nNext: fill the creation brief + smoke tests, edit SKILL.md, run validate_skill.py, then package the release.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
