#!/usr/bin/env python3
"""Guided first-run entrypoint for skill-mastery.

Audits a repo, writes an optional inventory, and prints the next concrete action.
This is intentionally a thin orchestrator around audit_skills.py: first-time users
need a path, not another framework.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_skills import audit_one, discover, render_markdown  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent


def choose_next(results: list[dict]) -> dict | None:
    """Pick the most useful next skill: revise before keep, avoid FAIL unless all fail."""
    order = {'revise': 0, 'split': 1, 'keep': 2, 'retire': 3}
    candidates = sorted(results, key=lambda r: (order.get(r.get('verdict', 'retire'), 9), r['grade'] == 'FAIL', r['path']))
    return candidates[0] if candidates else None


def summarize(results: list[dict], root: Path, inventory: Path | None) -> str:
    counts = {g: sum(1 for r in results if r['grade'] == g) for g in ('PASS', 'WARN', 'FAIL')}
    verdicts: dict[str, int] = {}
    for r in results:
        verdicts[r['verdict']] = verdicts.get(r['verdict'], 0) + 1

    lines = [f'# skill-mastery start — `{root}`', '']
    if not results:
        lines += [
            'No `SKILL.md` files found.',
            '',
            'Recommended next step:',
            '- Create a focused workshop draft with `scripts/create_skill.py`.',
            '- Example: `python3 scripts/create_skill.py my-skill --description "Do X. Use when..."`.',
            '- Add 3 smoke tests before considering any optimizer loop.',
        ]
        return '\n'.join(lines)

    lines += [
        f"Found {len(results)} skill(s): {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL.",
        'Verdicts: ' + ', '.join(f'{k}={v}' for k, v in sorted(verdicts.items())),
    ]
    if inventory:
        lines.append(f'Inventory: `{inventory}`')
    lines.append('')

    chosen = choose_next(results)
    if chosen:
        lines += [
            '## Recommended first action',
            '',
            f"Skill: `{chosen['path']}`",
            f"Verdict: **{chosen['verdict']}** — {chosen['suggested_patch_type']}",
            f"Next command: `{chosen['next_command']}`",
            '',
            'After that: run the qualitative audit prompt, add 3 smoke tests, apply one bounded patch, then package the release.',
        ]
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, nargs='?', default=Path('.'), help='repo or folder to audit')
    parser.add_argument('--out', type=Path, default=None, help='write full inventory markdown')
    parser.add_argument('--no-inventory', action='store_true', help='do not write an inventory file')
    args = parser.parse_args()

    root = args.root.resolve()
    skills = discover(root)
    results = [audit_one(p) for p in skills]

    inventory_path = None if args.no_inventory else (args.out or Path('inventory.md'))
    if inventory_path:
        inventory_path.write_text(render_markdown(results, root) + '\n', encoding='utf-8')

    print(summarize(results, root, inventory_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
