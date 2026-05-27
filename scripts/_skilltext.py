#!/usr/bin/env python3
"""Skill-text helpers shared by the runner: hashing and the protected region."""
from __future__ import annotations

import hashlib
import re

SLOW_UPDATE_RE = re.compile(r"(^##\s*Slow-update[^\n]*\n)(.*?)(?=^##\s|\Z)", re.M | re.S)


def skill_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def slow_update_body(text: str) -> str:
    m = SLOW_UPDATE_RE.search(text)
    return m.group(2) if m else ''


def append_slow_update_note(text: str, note: str) -> str:
    """Append one note line into the protected region (creating it if absent)."""
    note = '- ' + note.lstrip('- ').rstrip()
    m = SLOW_UPDATE_RE.search(text)
    if not m:
        header = '\n## Slow-update (do not overwrite in single-pass edits)\n\n'
        return text.rstrip() + '\n' + header + note + '\n'
    body = m.group(2).rstrip()
    new_body = (body + '\n' if body else '') + note + '\n'
    return text[: m.start(2)] + new_body + text[m.end(2):]
