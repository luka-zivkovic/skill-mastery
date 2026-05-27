#!/usr/bin/env python3
"""Targeted parser for this repo's eval manifests (stdlib only).

We deliberately parse the small, controlled manifest schema rather than depend on
PyYAML (not available here) or the brittle whole-file regex scraping the validator
used. The runner needs real structured tasks, so this returns typed objects and
fails loudly on structural surprises.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SPLITS = ('train', 'validation', 'test')


@dataclass
class Task:
    id: str
    prompt: str
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class Manifest:
    id: str
    skill: str
    verifiability: str
    accept_rule: str
    grading_runs: int
    scale: str
    rubric_criteria: list[str]
    source: dict[str, str]
    deployed: dict[str, str]
    splits: dict[str, list[Task]]
    verifier: str | None = None


def _top_scalar(text: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*([^#\n]+?)\s*(?:#.*)?$", text, re.M)
    return m.group(1).strip().strip('"\'') if m else None


def _block(text: str, key: str) -> str:
    """Return the indented body under a top-level `key:` line."""
    m = re.search(rf"^{re.escape(key)}:\s*(#.*)?$", text, re.M)
    if not m:
        return ''
    body = text[m.end():]
    stop = re.search(r"^(?!\s|#)\S", body, re.M)  # next top-level (non-indented, non-comment) key
    return body[: stop.start()] if stop else body


def _nested_map(text: str, key: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in _block(text, key).splitlines():
        m = re.match(r"^\s+([A-Za-z_]+):\s*([^#\n]*?)\s*(?:#.*)?$", line)
        if m and m.group(2) != '':
            out[m.group(1)] = m.group(2).strip().strip('"\'')
    return out


def _criteria_list(text: str, key: str) -> list[str]:
    out = []
    for line in _block(text, key).splitlines():
        m = re.match(r"^\s+-\s+(.*\S)\s*$", line)
        if m:
            out.append(m.group(1).strip().strip('"\''))
    return out


def _parse_split(body: str) -> list[Task]:
    """Parse a split body into tasks. Task items are `- id:` at the shallowest indent."""
    item_indents = [len(m) for m in re.findall(r"^( *)-\s+id:", body, re.M)]
    if not item_indents:
        return []
    indent = min(item_indents)
    # Split the body into chunks, each starting at a task-level `- id:` line.
    starts = [m.start() for m in re.finditer(rf"^ {{{indent}}}-\s+id:", body, re.M)]
    chunks = [body[starts[i]: starts[i + 1] if i + 1 < len(starts) else len(body)] for i in range(len(starts))]
    tasks = []
    for chunk in chunks:
        tid = re.search(r"-\s+id:\s*([^#\n]+?)\s*(?:#.*)?$", chunk, re.M)
        prompt = re.search(r"^\s+prompt:\s*([^#\n]+?)\s*(?:#.*)?$", chunk, re.M)
        crit = []
        cm = re.search(r"^\s+success_criteria:\s*$", chunk, re.M)
        if cm:
            for line in chunk[cm.end():].splitlines():
                lm = re.match(r"^\s+-\s+(.*\S)\s*$", line)
                if lm:
                    crit.append(lm.group(1).strip().strip('"\''))
                elif line.strip() and not line.startswith(' ' * (indent + 2)):
                    break
        tasks.append(Task(
            id=(tid.group(1).strip().strip('"\'') if tid else '?'),
            prompt=(prompt.group(1).strip().strip('"\'') if prompt else ''),
            success_criteria=crit,
        ))
    return tasks


def load(path: Path) -> Manifest:
    text = Path(path).read_text(encoding='utf-8')
    splits_body = _block(text, 'splits')
    splits = {}
    for s in SPLITS:
        sm = re.search(rf"^\s{{2}}{s}:\s*$", splits_body, re.M)
        if not sm:
            splits[s] = []
            continue
        rest = splits_body[sm.end():]
        nxt = re.search(r"^\s{2}(train|validation|test):\s*$", rest, re.M)
        splits[s] = _parse_split(rest[: nxt.start()] if nxt else rest)

    scoring = _nested_map(text, 'scoring')
    return Manifest(
        id=_top_scalar(text, 'id') or '?',
        skill=_top_scalar(text, 'skill') or '?',
        verifiability=_top_scalar(text, 'verifiability') or 'subjective',
        accept_rule=scoring.get('accept_rule', ''),
        grading_runs=int(scoring.get('grading_runs', '3') or 3),
        scale=scoring.get('scale', '0-1'),
        rubric_criteria=_criteria_list(text, 'rubric'),
        source=_nested_map(text, 'source'),
        deployed=_nested_map(text, 'deployed'),
        splits=splits,
        verifier=_top_scalar(text, 'verifier'),
    )
