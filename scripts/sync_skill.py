#!/usr/bin/env python3
"""Guard against drift between a workshop skill copy and its deployed source.

Computes a content hash over a skill folder (all files except records/caches), and
compares the local workshop copy against the `source`/`deployed` hashes recorded in
an eval manifest. Refuses to start a loop when they diverge, so edits are never
computed against a stale base — and improvements have a defined path back to deploy.

  # before optimizing: confirm the local copy matches what is deployed
  python3 scripts/sync_skill.py check workshop/skills/my-skill examples/toy-evals/eval-manifest.yaml

  # print the current hash to paste into the manifest's source/deployed blocks
  python3 scripts/sync_skill.py hash workshop/skills/my-skill
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

IGNORE_DIRS = {'.git', 'records', '__pycache__', '.DS_Store'}


def skill_hash(skill_dir: Path) -> str:
    h = hashlib.sha256()
    files = sorted(
        p for p in skill_dir.rglob('*')
        if p.is_file() and not (set(p.relative_to(skill_dir).parts) & IGNORE_DIRS)
        and p.name != '.gitkeep'
    )
    for p in files:
        rel = p.relative_to(skill_dir).as_posix()
        h.update(rel.encode('utf-8'))
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()[:16]


def manifest_block_hash(manifest: Path, block: str) -> str | None:
    text = manifest.read_text(encoding='utf-8')
    m = re.search(rf"^{re.escape(block)}:\s*$", text, re.M)
    if not m:
        return None
    body = text[m.end():]
    stop = re.search(r"^\S", body, re.M)
    body = body[: stop.start()] if stop else body
    inner = re.search(r"^\s+hash:\s*(.+?)\s*$", body, re.M)
    return inner.group(1).strip().strip('"\'') if inner else None


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)

    h = sub.add_parser('hash', help='print the content hash of a skill folder')
    h.add_argument('skill_dir', type=Path)

    c = sub.add_parser('check', help='verify a workshop copy matches manifest source/deployed hashes')
    c.add_argument('skill_dir', type=Path)
    c.add_argument('manifest', type=Path)

    args = parser.parse_args()

    if args.cmd == 'hash':
        print(skill_hash(args.skill_dir))
        return 0

    current = skill_hash(args.skill_dir)
    source = manifest_block_hash(args.manifest, 'source')
    deployed = manifest_block_hash(args.manifest, 'deployed')
    print(f'current:  {current}')
    print(f'source:   {source}')
    print(f'deployed: {deployed}')

    if source == 'none' or deployed == 'none' or source is None or deployed is None:
        print('NOTE: skill is not deployed yet (source/deployed = none). Safe to iterate; '
              'set the hashes once it ships.')
        return 0
    if current != source:
        print('ERROR: local copy drifted from the manifest source hash — re-sync before optimizing '
              '(edits would be computed against a stale base).', file=sys.stderr)
        return 1
    if source != deployed:
        print('WARNING: deployed skill is ahead of the source the manifest was built on; '
              'reconcile before accepting edits.', file=sys.stderr)
        return 1
    print('OK: local copy matches deployed skill; safe to optimize.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
