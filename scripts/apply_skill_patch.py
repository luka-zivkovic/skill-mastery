#!/usr/bin/env python3
"""Apply bounded JSON text patches to files inside a skill directory.

Two invariants the SkillOpt discipline relies on, now enforced (not just documented):

- **Atomic.** A multi-patch list is applied to in-memory copies first; if ANY patch
  fails to anchor, nothing is written. No more half-applied skills.
- **Slow-update is protected.** Single-pass edits may not change the `## Slow-update`
  region. Pass --slow-update to run a dedicated slow-update consolidation.

Bounded ops only: replace / append / prepend / insert_after / delete. The target file
must already exist (a skill patch edits the skill, it does not conjure new files).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_OPS = {'replace', 'append', 'prepend', 'insert_after', 'delete'}
SLOW_UPDATE_RE = re.compile(r"^##\s*Slow-update.*?(?=^##\s|\Z)", re.M | re.S)


def safe_path(root: Path, rel: str) -> Path:
    target = (root / rel).resolve()
    root_resolved = root.resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError(f'path escapes root: {rel}')
    return target


def slow_update_region(text: str) -> str:
    m = SLOW_UPDATE_RE.search(text)
    return m.group(0) if m else ''


def apply_op(text: str, patch: dict) -> str:
    """Pure: return the patched text, or raise ValueError if the anchor is missing."""
    op = patch.get('op')
    if op not in VALID_OPS:
        raise ValueError(f'invalid op {op!r}; expected one of {sorted(VALID_OPS)}')
    if op == 'replace':
        if patch['old'] not in text:
            raise ValueError('replace anchor not found')
        return text.replace(patch['old'], patch['new'], 1)
    if op == 'append':
        return text.rstrip() + '\n\n' + patch['text'].strip() + '\n'
    if op == 'prepend':
        return patch['text'].strip() + '\n\n' + text.lstrip()
    if op == 'insert_after':
        if patch['anchor'] not in text:
            raise ValueError('insert_after anchor not found')
        return text.replace(patch['anchor'], patch['anchor'] + '\n' + patch['text'].rstrip(), 1)
    if op == 'delete':
        if patch['old'] not in text:
            raise ValueError('delete anchor not found')
        return text.replace(patch['old'], '', 1)
    raise AssertionError(op)  # pragma: no cover


def plan(root: Path, patches: list[dict], allow_slow_update: bool) -> dict[Path, tuple[str, str]]:
    """Compute final text per file without writing. Raises on any failure (atomicity)."""
    staged: dict[Path, str] = {}
    originals: dict[Path, str] = {}
    for i, patch in enumerate(patches):
        try:
            target = safe_path(root, patch.get('path', 'SKILL.md'))
        except ValueError as exc:
            raise ValueError(f'patch {i}: {exc}') from exc
        if target not in staged:
            if not target.exists():
                raise ValueError(f'patch {i}: target does not exist: {patch.get("path", "SKILL.md")}')
            originals[target] = staged[target] = target.read_text(encoding='utf-8')
        try:
            required = {'replace': ('old', 'new'), 'delete': ('old',), 'insert_after': ('anchor', 'text'),
                        'append': ('text',), 'prepend': ('text',)}.get(patch.get('op'), ())
            missing = [k for k in required if k not in patch]
            if missing:
                raise ValueError(f'missing key(s) {missing} for op {patch.get("op")!r}')
            staged[target] = apply_op(staged[target], patch)
        except (ValueError, KeyError) as exc:
            raise ValueError(f'patch {i} ({patch.get("op")}) on {patch.get("path", "SKILL.md")}: {exc}') from exc

    if not allow_slow_update:
        for target, final in staged.items():
            if slow_update_region(originals[target]) != slow_update_region(final):
                raise ValueError(
                    f'{target.name}: edit changes the protected ## Slow-update region; '
                    'use the slow-update consolidation flow (--slow-update) for that'
                )
    return {t: (originals[t], final) for t, final in staged.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('skill_dir', type=Path)
    parser.add_argument('patch_json', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--slow-update', action='store_true',
                        help='allow edits to the protected ## Slow-update region (consolidation flow)')
    args = parser.parse_args()

    data = json.loads(args.patch_json.read_text(encoding='utf-8'))
    patches = data if isinstance(data, list) else [data]
    try:
        result = plan(args.skill_dir, patches, args.slow_update)
    except ValueError as exc:
        print(f'ERROR: {exc} (nothing written)', file=sys.stderr)
        return 1

    for target, (_, final) in result.items():
        rel = target.relative_to(args.skill_dir.resolve())
        if not args.dry_run:
            target.write_text(final, encoding='utf-8')
        print(f'{"DRY-RUN" if args.dry_run else "APPLIED"}: {len(patches)} patch(es) -> {rel}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
