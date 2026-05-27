#!/usr/bin/env python3
"""Validate the repo's tiered YAML eval manifests (stdlib only).

Enforces the anti-noise and verifiability-tier guardrails:
- a verifiability tier is declared and the accept_rule matches it,
- objective/rubric tiers keep validation/test splits out of the noise floor
  (>= MIN_SPLIT cases) and run >= MIN_RUNS grading runs,
- the rubric tier ships a rubric, and
- source/deployed provenance is present so sync_skill.py can detect drift.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_SPLITS = ('train', 'validation', 'test')
MIN_SPLIT = 8          # minimum validation/test cases for a scored tier
MIN_RUNS = 3           # minimum grading runs per task for a scored tier
SCORED_TIERS = ('objective', 'rubric')

ACCEPT_RULE_BY_TIER = {
    'objective': 'validation_score_must_strictly_improve',
    'rubric': 'new_must_win_majority_pairwise_no_regression',
    'subjective': 'no_scored_gate',
}


def section_text(text: str, split: str) -> str:
    pattern = re.compile(rf"^\s{{2}}{re.escape(split)}:\s*$", re.M)
    match = pattern.search(text)
    if not match:
        return ''
    start = match.end()
    next_match = re.search(r"^\s{2}(train|validation|test):\s*$", text[start:], re.M)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end]


def count_tasks(body: str) -> int:
    """Count task entries = `- id:` list items at the shallowest list indent.

    Anchoring to the shallowest indent excludes deeper `- id:` lines that are
    really success_criteria bullets, which would otherwise inflate the count and
    let an undersized split slip past the MIN_SPLIT gate.
    """
    indents = [len(m) for m in re.findall(r"^( *)-\s", body, re.M)]
    if not indents:
        return 0
    task_indent = min(indents)
    return len(re.findall(rf"^ {{{task_indent}}}-\s+id:", body, re.M))


def scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.M)
    return match.group(1).strip().strip('"\'') if match else None


def nested_scalar(text: str, parent: str, key: str) -> str | None:
    """Read a one-level-nested scalar like scoring.grading_runs.

    Tolerates a trailing comment after the parent key (`scoring:  # ...`) and
    column-0 comment lines inside the block (a `#` line must not be mistaken for
    the next top-level key that ends the block).
    """
    pattern = re.compile(rf"^{re.escape(parent)}:\s*(#.*)?$", re.M)
    match = pattern.search(text)
    if not match:
        return None
    body = text[match.end():]
    stop = re.search(r"^(?!#)\S", body, re.M)  # next top-level key, ignoring comment lines
    body = body[: stop.start()] if stop else body
    inner = re.search(rf"^\s+{re.escape(key)}:\s*([^#\n]+?)\s*(?:#.*)?$", body, re.M)
    return inner.group(1).strip().strip('"\'') if inner else None


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding='utf-8')
    errors: list[str] = []

    for field in ('id:', 'skill:', 'verifiability:', 'scoring:', 'splits:', 'source:', 'deployed:'):
        if re.search(rf"^{re.escape(field)}", text, re.M) is None:
            errors.append(f'missing top-level {field}')

    tier = scalar(text, 'verifiability')
    if tier not in ACCEPT_RULE_BY_TIER:
        errors.append(f'verifiability must be one of {sorted(ACCEPT_RULE_BY_TIER)}; got {tier!r}')
        tier = None

    accept_rule = nested_scalar(text, 'scoring', 'accept_rule')
    if tier and accept_rule != ACCEPT_RULE_BY_TIER[tier]:
        errors.append(
            f'accept_rule for tier {tier!r} must be {ACCEPT_RULE_BY_TIER[tier]!r}; got {accept_rule!r}'
        )

    if tier in SCORED_TIERS:
        runs = nested_scalar(text, 'scoring', 'grading_runs')
        try:
            if runs is None or int(runs) < MIN_RUNS:
                errors.append(f'scoring.grading_runs must be >= {MIN_RUNS} for the {tier} tier; got {runs!r}')
        except ValueError:
            errors.append(f'scoring.grading_runs must be an integer; got {runs!r}')

    if tier == 'rubric' and re.search(r"^rubric:\s*$", text, re.M) is None:
        errors.append('rubric tier requires a top-level rubric: block with criteria')

    for split in REQUIRED_SPLITS:
        body = section_text(text, split)
        if not body.strip():
            errors.append(f'missing or empty split: {split}')
            continue
        for token in ('id:', 'prompt:', 'success_criteria:'):
            if token not in body:
                errors.append(f'split {split} has no task {token}')
        if tier in SCORED_TIERS and split in ('validation', 'test'):
            n = count_tasks(body)
            if n < MIN_SPLIT:
                errors.append(
                    f'{split} split has {n} cases; the {tier} tier needs >= {MIN_SPLIT} '
                    f'to keep the gate out of the noise floor'
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    errors = validate(args.manifest)
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print(f'OK: {args.manifest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
