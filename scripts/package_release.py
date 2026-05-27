#!/usr/bin/env python3
"""Create a reviewable release package for a skill change."""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_eval_results(records: Path) -> list[dict]:
    path = records / 'eval_results.jsonl'
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({'error': 'invalid-jsonl', 'raw': line[:200]})
    return rows


def copy_if_exists(src: Path | None, dest: Path) -> bool:
    if not src or not src.exists():
        return False
    if src.is_dir():
        src = src / 'SKILL.md'
    if not src.exists():
        return False
    shutil.copy2(src, dest)
    return True


def after_file_from(path: Path) -> tuple[str, Path]:
    """Return (skill_name, SKILL-like markdown file) from a skill dir, run dir, or file."""
    path = path.resolve()
    if path.is_file():
        return path.parent.name if path.name == 'SKILL.md' else path.stem, path
    skill_md = path / 'SKILL.md'
    if skill_md.exists():
        return path.name, skill_md
    best = path / 'best_skill.md'
    if best.exists():
        return path.name, best
    raise FileNotFoundError(f'no SKILL.md or best_skill.md found at {path}')


def package(skill_dir: Path, before: Path | None = None, patch: Path | None = None,
            records: Path = ROOT / 'records', out_root: Path | None = None,
            version: str | None = None) -> Path:
    skill_name, after_file = after_file_from(skill_dir)
    stamp = version or datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    out_root = out_root or records / 'releases'
    release = out_root / f'{skill_name}@{stamp}'
    release.mkdir(parents=True, exist_ok=False)

    copied_before = copy_if_exists(before, release / 'before.md')
    shutil.copy2(after_file, release / 'after.md')
    if patch and patch.exists():
        shutil.copy2(patch, release / f'patch{patch.suffix or ".json"}')

    evals = read_eval_results(records)
    (release / 'validation-summary.md').write_text(validation_summary(skill_name, copied_before, evals), encoding='utf-8')
    (release / 'ship-checklist.md').write_text(ship_checklist(skill_name), encoding='utf-8')
    (release / 'manifest.json').write_text(json.dumps({
        'skill': skill_name,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'before_included': copied_before,
        'after': 'after.md',
        'patch_included': bool(patch and patch.exists()),
        'eval_result_count': len(evals),
    }, indent=2) + '\n', encoding='utf-8')
    return release


def validation_summary(skill: str, copied_before: bool, evals: list[dict]) -> str:
    lines = [f'# Validation summary — {skill}', '']
    lines.append(f'Before snapshot included: {"yes" if copied_before else "no"}')
    lines.append(f'Eval result rows found: {len(evals)}')
    lines.append('')
    if evals:
        lines += ['| Timestamp | Split | Tier | Decision | Mean | Rationale |', '|-----------|-------|------|----------|------|-----------|']
        for row in evals[-10:]:
            lines.append('| {timestamp} | {split} | {tier} | {decision} | {mean} | {rationale} |'.format(
                timestamp=row.get('timestamp', ''),
                split=row.get('split', ''),
                tier=row.get('tier', ''),
                decision=row.get('decision', ''),
                mean=row.get('mean', ''),
                rationale=str(row.get('rationale', row.get('error', ''))).replace('|', '\\|'),
            ))
    else:
        lines.append('No `records/eval_results.jsonl` found. For lite-path changes, paste smoke-test evidence here before shipping.')
    lines += ['', '## Human review notes', '', '- Reviewer:', '- Decision: ship / do not ship / needs more evidence', '- Caveats:']
    return '\n'.join(lines) + '\n'


def ship_checklist(skill: str) -> str:
    return f'''# Ship checklist — {skill}

- [ ] `after.md` contains only the deployed skill content; no run logs or optimizer scratch notes.
- [ ] Patch is bounded and reviewable.
- [ ] Smoke tests or validation evidence are recorded in `validation-summary.md`.
- [ ] Rejected alternatives, if any, are recorded in `records/rejected/`.
- [ ] Slow-update notes are dated and cite at least two validation examples when present.
- [ ] Deployed skill path/hash has been synced (`scripts/sync_skill.py`).
- [ ] Owner accepted the caveats and shipped the patch.
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill_dir', type=Path)
    parser.add_argument('--before', type=Path, default=None, help='source/deployed skill dir or SKILL.md to snapshot')
    parser.add_argument('--patch', type=Path, default=None, help='accepted patch JSON to include')
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--out', type=Path, default=None, help='release root; defaults to records/releases')
    parser.add_argument('--version', default=None, help='release suffix; defaults to timestamp')
    args = parser.parse_args()
    try:
        release = package(args.skill_dir, before=args.before, patch=args.patch, records=args.records,
                          out_root=args.out, version=args.version)
    except OSError as exc:
        print(f'ERROR: {exc}')
        return 1
    print(f'WROTE: {release}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
