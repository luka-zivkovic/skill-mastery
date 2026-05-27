#!/usr/bin/env python3
"""Summarize patch records + eval history, and surface two things the loop needs:

1. A "rejected edits to avoid re-proposing" block — paste it into the next
   failure-analysis pass so the optimizer doesn't re-suggest a known-bad edit.
2. Slow-update rot warnings — flag protected-region notes that lack a date or
   fewer than two validation citations (an unpruned slow-update region is the
   exact failure SkillOpt shows costs the most).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
VAL_ID_RE = re.compile(r"val[-_ ]?\d+", re.I)


def is_cited(note_without_date: str) -> bool:
    """True if the note references >= 2 validation examples.

    Counts explicit IDs (val-003) first; falls back to prose forms like
    "validation examples 3 and 7" so a correctly-cited note isn't flagged just
    for not using the ID syntax.
    """
    if len(VAL_ID_RE.findall(note_without_date)) >= 2:
        return True
    if re.search(r"example", note_without_date, re.I):
        return len(re.findall(r"\d+", note_without_date)) >= 2
    return False


def count_files(path: Path) -> int:
    return len([p for p in path.glob('**/*') if p.is_file() and p.name != '.gitkeep']) if path.exists() else 0


def read_eval_scores(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({'error': 'invalid jsonl row', 'raw': line})
    return rows


def rejection_reason(p: Path) -> str:
    """Pull the human-readable reason from a rejected record, not its first line.

    JSON patch records carry it under `_rejection.reason` (or `rationale`); for
    other files fall back to the first non-trivial line.
    """
    text = p.read_text(encoding='utf-8', errors='replace')
    if p.suffix == '.json':
        try:
            data = json.loads(text)
            reason = (data.get('_rejection', {}) or {}).get('reason') or data.get('rationale')
            if reason:
                return reason
        except (json.JSONDecodeError, AttributeError):
            pass
    for line in text.splitlines():
        s = line.strip()
        if s and s not in ('{', '}', '['):
            return s
    return '(no reason recorded)'


def rejected_block(rejected_dir: Path) -> list[str]:
    if not rejected_dir.exists():
        return []
    return [
        f'- {p.name}: {rejection_reason(p)}'
        for p in sorted(rejected_dir.glob('**/*'))
        if p.is_file() and p.name != '.gitkeep'
    ]


def slow_update_warnings(skill_md: Path) -> list[str]:
    if not skill_md.exists():
        return [f'{skill_md} not found']
    text = skill_md.read_text(encoding='utf-8')
    m = re.search(r"^##\s*Slow-update.*$", text, re.M)
    if not m:
        return ['no ## Slow-update section found']
    body = text[m.end():]
    nxt = re.search(r"^##\s", body, re.M)
    body = body[: nxt.start()] if nxt else body
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)  # drop HTML comment guidance blocks
    notes = [ln.strip() for ln in body.splitlines() if ln.strip()]
    warnings = []
    for note in notes:
        if not DATE_RE.search(note):
            warnings.append(f'undated note (prune candidate): {note[:80]}')
        elif not is_cited(DATE_RE.sub('', note)):
            warnings.append(f'note cites < 2 validation examples (prune candidate): {note[:80]}')
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('records_dir', type=Path)
    parser.add_argument('--skill', type=Path, default=None,
                        help='skill folder to scan its SKILL.md slow-update region for rot')
    args = parser.parse_args()

    accepted = count_files(args.records_dir / 'accepted')
    rejected = count_files(args.records_dir / 'rejected')
    snapshots = count_files(args.records_dir / 'snapshots')
    evals = read_eval_scores(args.records_dir / 'eval_results.jsonl')

    print(f'accepted_patches: {accepted}')
    print(f'rejected_patches: {rejected}')
    print(f'snapshots: {snapshots}')
    print(f'eval_results: {len(evals)}')
    if evals:
        latest = evals[-1]
        print(f"latest_eval: skill={latest.get('skill')} split={latest.get('split')} "
              f"tier={latest.get('tier')} mean={latest.get('mean')} decision={latest.get('decision')}")

    block = rejected_block(args.records_dir / 'rejected')
    print('\n# Rejected edits to avoid re-proposing (paste into next failure analysis):')
    print('\n'.join(block) if block else '(none)')

    if args.skill:
        print('\n# Slow-update rot check:')
        warnings = slow_update_warnings(args.skill / 'SKILL.md')
        print('\n'.join(f'WARN: {w}' for w in warnings) if warnings else 'OK: slow-update region clean')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
