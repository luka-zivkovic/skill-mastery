#!/usr/bin/env python3
"""One command to check the toolkit is healthy: `make check` / `python3 scripts/doctor.py`.

Runs the validators against the shipped skills/manifests, the unit tests, and a
deterministic mock run of the full loop. Exits non-zero if anything fails — wire it
into CI or a pre-commit hook.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def step(name: str, cmd: list[str]) -> bool:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    ok = proc.returncode == 0
    print(f'{"✓" if ok else "✗"} {name}')
    if not ok:
        print((proc.stdout + proc.stderr).strip()[:800])
    return ok


def main() -> int:
    checks = [
        ('skills validate', [PY, 'scripts/validate_skill.py', 'examples/toy-skill']),
        ('claude template validates', [PY, 'scripts/validate_skill.py', 'templates/claude-skill']),
        ('codex template validates', [PY, 'scripts/validate_skill.py', 'templates/codex-skill']),
        ('toy manifest validates', [PY, 'scripts/validate_eval_manifest.py', 'examples/toy-evals/eval-manifest.yaml']),
        ('create skill help', [PY, 'scripts/create_skill.py', '--help']),
        ('guided start help', [PY, 'scripts/start.py', '--help']),
        ('lite improve help', [PY, 'scripts/lite_improve.py', '--help']),
        ('release package help', [PY, 'scripts/package_release.py', '--help']),
        ('unit tests', [PY, '-m', 'unittest', 'discover', '-s', 'tests']),
        ('mock loop runs', [PY, 'scripts/skillopt_run.py', 'examples/toy-skill',
                            'examples/toy-evals/eval-manifest.yaml', '--adapter', 'mock',
                            '--epochs', '2', '--out', '/tmp/skillopt-doctor']),
    ]
    results = [step(name, cmd) for name, cmd in checks]
    print()
    if all(results):
        print('doctor: all checks passed')
        return 0
    print(f'doctor: {results.count(False)} of {len(results)} checks FAILED')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
