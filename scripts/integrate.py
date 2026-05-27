#!/usr/bin/env python3
"""Vendor the skill-mastery toolkit into a target repo and wire up its CLAUDE.md.

This is the embed path: it copies the discipline (scripts, prompts, docs, templates,
workshop + records skeletons) into `<target>/.skill-mastery/`, injects a concise
"Skill discipline" block into the target repo's root CLAUDE.md (so the contract
auto-loads where skills are actually built), and seeds `.skill-mastery/inventory.md`
from an initial audit of the repo's existing skills.

  python3 scripts/integrate.py /path/to/target-repo
  python3 scripts/integrate.py /path/to/target-repo --dry-run

Idempotent: re-running refreshes the vendored toolkit and replaces the managed CLAUDE.md
block between its markers. Your own CLAUDE.md content outside the markers is untouched.

For a one-off audit WITHOUT vendoring anything, skip this and just run:
  python3 scripts/audit_skills.py /path/to/target-repo
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_skills import discover, audit_one, render_markdown  # noqa: E402

VENDOR_DIR = '.skill-mastery'
VENDORED = ('scripts', 'prompts', 'docs', 'templates', 'CLAUDE.md')
SKELETON_DIRS = ('workshop/skills', 'workshop/evals', 'workshop/runs',
                 'records/accepted', 'records/rejected', 'records/snapshots', 'records/releases')
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store')

BEGIN = '<!-- BEGIN skill-mastery (managed by .skill-mastery/scripts/integrate.py) -->'
END = '<!-- END skill-mastery -->'

BLOCK = f"""{BEGIN}
## Skill discipline (skill-mastery)

Skills in this repo follow the skill-mastery contract. The toolkit and full rules live in
`{VENDOR_DIR}/` — see `{VENDOR_DIR}/CLAUDE.md` and `{VENDOR_DIR}/docs/integration.md`.

- **No blind edits.** Iterate on a copy in `{VENDOR_DIR}/workshop/skills/`, gate on an eval,
  record the decision in `{VENDOR_DIR}/records/`. Never edit a deployed skill in place.
- **Declare a verifiability tier** (objective / rubric / subjective); the gate scales to it.
  Default to the **lite path** (write it well once + ~3 smoke tests, revise on failure)
  unless reuse ≥ ~10× AND a verifier exists AND the skill has failed ≥2× for real.
- **Rubric grading is blind, pairwise, different model if possible** — never self-graded.
- **Start guided triage:** `python3 {VENDOR_DIR}/scripts/start.py . --out {VENDOR_DIR}/inventory.md`
- **Lite path for one skill:** `python3 {VENDOR_DIR}/scripts/lite_improve.py path/to/skill`
- **Author a new skill:** `python3 {VENDOR_DIR}/scripts/create_skill.py my-skill --description "Do X. Use when..."`
{END}"""


def copy_toolkit(repo_root: Path, dest: Path, dry_run: bool) -> list[str]:
    actions = []
    for item in VENDORED:
        src = repo_root / item
        if not src.exists():
            continue
        target = dest / item
        if src.is_dir():
            actions.append(f'copy dir  {item}/ -> {VENDOR_DIR}/{item}/')
            if not dry_run:
                shutil.copytree(src, target, ignore=IGNORE, dirs_exist_ok=True)
        else:
            actions.append(f'copy file {item} -> {VENDOR_DIR}/{item}')
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
    for rel in SKELETON_DIRS:
        actions.append(f'ensure    {VENDOR_DIR}/{rel}/')
        if not dry_run:
            (dest / rel).mkdir(parents=True, exist_ok=True)
            (dest / rel / '.gitkeep').touch()
    return actions


def _marker_lines(lines: list[str], marker: str) -> list[int]:
    """Indices of lines that ARE the marker, ignoring any inside ``` code fences.

    A marker documented inside a fenced block (e.g. this very file shown in a
    README) must not be treated as the managed region — rewriting it would
    corrupt the fence and orphan the user's content.
    """
    out, in_fence = [], False
    for i, line in enumerate(lines):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        if not in_fence and line.strip() == marker:
            out.append(i)
    return out


def wire_claude_md(target_repo: Path, dry_run: bool) -> str:
    claude = target_repo / 'CLAUDE.md'
    existing = claude.read_text(encoding='utf-8') if claude.exists() else ''
    lines = existing.splitlines()
    begins, ends = _marker_lines(lines, BEGIN), _marker_lines(lines, END)

    if not begins and not ends:
        if existing.strip():
            new = existing.rstrip() + '\n\n' + BLOCK + '\n'
            verb = 'append skill-mastery block to existing CLAUDE.md'
        else:
            new = '# Project\n\n' + BLOCK + '\n'
            verb = 'create CLAUDE.md with skill-mastery block'
    elif len(begins) == 1 and len(ends) == 1 and begins[0] < ends[0]:
        pre = '\n'.join(lines[:begins[0]]).rstrip()
        post = '\n'.join(lines[ends[0] + 1:]).strip()
        new = (pre + ('\n\n' if pre else '') + BLOCK + ('\n\n' + post if post else '') + '\n')
        verb = 'refresh managed block in CLAUDE.md'
    else:
        raise ValueError(
            f'CLAUDE.md has malformed skill-mastery markers (BEGIN×{len(begins)}, END×{len(ends)}, '
            'outside code fences). Expected exactly one ordered pair. Fix or remove them and re-run; '
            'CLAUDE.md was left untouched.'
        )

    if not dry_run:
        claude.write_text(new, encoding='utf-8')
    return verb


def seed_inventory(target_repo: Path, dest: Path, dry_run: bool) -> str:
    skills = [p for p in discover(target_repo) if VENDOR_DIR not in p.parts]
    report = render_markdown([audit_one(p) for p in skills], target_repo)
    if not dry_run:
        (dest).mkdir(parents=True, exist_ok=True)
        (dest / 'inventory.md').write_text(report + '\n', encoding='utf-8')
    return f'seed {VENDOR_DIR}/inventory.md from audit of {len(skills)} existing skill(s)'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('target', type=Path, help='the repo to integrate skill-mastery into')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    target = args.target.resolve()
    if not target.is_dir():
        print(f'ERROR: target is not a directory: {target}', file=sys.stderr)
        return 1
    if target == repo_root:
        print('ERROR: target is the skill-mastery repo itself; pick another repo.', file=sys.stderr)
        return 1

    dest = target / VENDOR_DIR
    print(f'Integrating skill-mastery into {target}{"  (dry-run)" if args.dry_run else ""}\n')
    for line in copy_toolkit(repo_root, dest, args.dry_run):
        print(f'  {line}')
    print(f'  {seed_inventory(target, dest, args.dry_run)}')
    try:
        print(f'  {wire_claude_md(target, args.dry_run)}')
    except ValueError as exc:
        print(f'  ERROR: {exc}', file=sys.stderr)
        return 1

    print('\nNext:')
    print(f'  1. Review {VENDOR_DIR}/inventory.md — the triage of your existing skills.')
    print(f'  2. Commit {VENDOR_DIR}/ and the CLAUDE.md change so your team shares the contract.')
    print(f'  3. For any keeper: run {VENDOR_DIR}/scripts/lite_improve.py path/to/skill.')
    print(f'  4. Run {VENDOR_DIR}/prompts/audit/skill_audit.md to add smoke tests, then package the release.')
    print(f'  5. New skills: run {VENDOR_DIR}/scripts/create_skill.py my-skill --description "Do X. Use when..."')
    print('     Optimize only when the ROI gate says so.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
