#!/usr/bin/env python3
"""Harness adapters for the SkillOpt runner.

An adapter is the ONLY thing that talks to a model. The runner orchestrates; the
adapter executes. Three responsibilities:

  rollout(skill, prompt)                 -> the target model's output for a task
  grade(criteria, prompt, output)        -> 0..1 single-output score (find failures)
  propose_edits(skill, fails, ...)       -> bounded edits as a strict JSON contract
  judge_pairwise(criteria, p, a, b)      -> 'A' | 'B' | 'tie' (blind, for the rubric gate)

Two implementations ship:
  - MockAdapter   : deterministic, no model calls — powers tests, CI, and an offline demo.
  - CommandAdapter: shells each prompt to a CLI (claude/codex/anything) via stdin->stdout.

The optimizer (propose_edits / judge) should run a DIFFERENT model than the target when
possible — never let the editor grade its own edit.
"""
from __future__ import annotations

import json
import re
import subprocess

EDIT_CONTRACT = (
    'Return ONLY strict JSON: {"edits":[{"op":"replace|append|prepend|insert_after|delete",'
    '"path":"SKILL.md","old":"...","new":"...","anchor":"...","text":"...","rationale":"..."}]}. '
    'Use only the keys each op needs (replace: old,new; delete: old; insert_after: anchor,text; '
    'append/prepend: text). Edits must generalize, never hardcode task-specific values, and never '
    'touch the "## Slow-update" region.'
)
JUDGE_CONTRACT = 'Return ONLY strict JSON: {"winner":"A|B|tie","reason":"one sentence"}.'


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f'no JSON object in model output: {text[:200]!r}')
    return json.loads(m.group(0))


class Adapter:
    name = 'abstract'

    def rollout(self, skill_text: str, prompt: str) -> str:
        raise NotImplementedError

    def grade(self, criteria: list[str], prompt: str, output: str) -> float:
        raise NotImplementedError

    def propose_edits(self, skill_text, failures, successes, budget, rejected):
        raise NotImplementedError

    def judge_pairwise(self, criteria: list[str], prompt: str, a: str, b: str) -> str:
        raise NotImplementedError

    # --- multi-stage merge/rank (the paper's hierarchy; used with --paper-pipeline) ---
    def analyze_failures(self, skill_text, failures) -> list:
        """Corrective edits from the failing minibatch."""
        raise NotImplementedError

    def analyze_successes(self, skill_text, successes) -> list:
        """Preservation edits/rules from the succeeding minibatch (may be empty)."""
        raise NotImplementedError

    def merge_and_rank(self, skill_text, failure_edits, success_edits, budget, rejected) -> list:
        """Dedup contradictory/task-specific edits, prioritize failures, rank, clip to budget."""
        raise NotImplementedError


class MockAdapter(Adapter):
    """Deterministic stand-in. Encodes one learnable behavior so the loop converges:

    the target only emits a 'self-check:' line when the skill contains a
    'Known failure modes' section. The optimizer proposes exactly that section.
    This lets the full loop demonstrate a real accept without any model call.
    """
    name = 'mock'
    MARKER = 'Known failure modes'

    def rollout(self, skill_text: str, prompt: str) -> str:
        steps = 'step 1; step 2; step 3'
        if self.MARKER in skill_text:
            return f'objective: {prompt}\n{steps}\nself-check: matches the objective.'
        return f'objective: {prompt}\n{steps}'

    def grade(self, criteria, prompt, output) -> float:
        return 1.0 if 'self-check:' in output else 0.0

    def propose_edits(self, skill_text, failures, successes, budget, rejected):
        if self.MARKER in skill_text:
            return []  # nothing to fix
        return [{
            'op': 'insert_after',
            'path': 'SKILL.md',
            'anchor': '- Do not include unrelated background.',
            'text': '\n## Known failure modes\n\n- Always emit the self-check line.',
            'rationale': 'Recurring failure: self-check omitted under pressure.',
        }][:budget]

    def judge_pairwise(self, criteria, prompt, a, b) -> str:
        a_ok, b_ok = 'self-check:' in a, 'self-check:' in b
        if a_ok and not b_ok:
            return 'A'
        if b_ok and not a_ok:
            return 'B'
        return 'tie'

    def analyze_failures(self, skill_text, failures) -> list:
        # Same single learnable edit as propose_edits, but unclipped (merge clips).
        return self.propose_edits(skill_text, failures, [], 999, [])

    def analyze_successes(self, skill_text, successes) -> list:
        return []  # the toy needs no explicit preservation edit

    def merge_and_rank(self, skill_text, failure_edits, success_edits, budget, rejected) -> list:
        seen, out = set(), []
        for e in list(failure_edits) + list(success_edits):  # failures first
            key = (e.get('op'), e.get('anchor'), e.get('old'), e.get('text'))
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
        return out[:budget]


class CommandAdapter(Adapter):
    """Run a real model by shelling a prompt to a CLI command (stdin -> stdout).

    cmd is a list, e.g. ['claude', '-p'] or ['codex', 'exec', '-']. The prompt is
    written to stdin; the model's text is read from stdout. Set a different cmd for
    the optimizer/judge than the target to keep grading independent.
    """
    name = 'command'

    def __init__(self, target_cmd: list[str], optimizer_cmd: list[str] | None = None, timeout: int = 120):
        self.target_cmd = target_cmd
        self.optimizer_cmd = optimizer_cmd or target_cmd
        self.timeout = timeout

    def _call(self, cmd: list[str], prompt: str) -> str:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=self.timeout)
        if proc.returncode != 0:
            raise RuntimeError(f'{cmd[0]} exited {proc.returncode}: {proc.stderr[:200]}')
        return proc.stdout.strip()

    def rollout(self, skill_text, prompt) -> str:
        return self._call(self.target_cmd, f'{skill_text}\n\n---\nTask: {prompt}')

    def grade(self, criteria, prompt, output) -> float:
        crit = '\n'.join(f'- {c}' for c in criteria)
        p = (f'Score the OUTPUT against the criteria from 0 to 1.\nCriteria:\n{crit}\n\n'
             f'Task: {prompt}\nOutput:\n{output}\n\nReturn ONLY strict JSON: {{"score":0..1}}.')
        return float(_extract_json(self._call(self.optimizer_cmd, p)).get('score', 0.0))

    def propose_edits(self, skill_text, failures, successes, budget, rejected):
        fails = '\n\n'.join(f'[{t.id}] {t.prompt}\n-> {out}' for t, out in failures)
        rej = '\n'.join(f'- {r}' for r in rejected) or '(none)'
        p = (f'You are optimizing a skill. Propose at most {budget} bounded edits that fix the '
             f'COMMON failure pattern.\n\nCurrent SKILL.md:\n{skill_text}\n\nFailures:\n{fails}\n\n'
             f'Do NOT re-propose these rejected edits:\n{rej}\n\n{EDIT_CONTRACT}')
        return _extract_json(self._call(self.optimizer_cmd, p)).get('edits', [])[:budget]

    def judge_pairwise(self, criteria, prompt, a, b) -> str:
        crit = '\n'.join(f'- {c}' for c in criteria)
        p = (f'Two outputs, A and B, for the same task. Decide which better satisfies the criteria. '
             f'Do not reward length or formatting unless a criterion asks.\nCriteria:\n{crit}\n\n'
             f'Task: {prompt}\n\nOutput A:\n{a}\n\nOutput B:\n{b}\n\n{JUDGE_CONTRACT}')
        w = str(_extract_json(self._call(self.optimizer_cmd, p)).get('winner', 'tie')).strip().lower()
        return 'A' if w == 'a' else 'B' if w == 'b' else 'tie'

    def analyze_failures(self, skill_text, failures) -> list:
        fails = '\n\n'.join(f'[{t.id}] {t.prompt}\n-> {out}' for t, out in failures)
        p = (f'Analyze these FAILURES and propose corrective bounded edits for the COMMON pattern.\n\n'
             f'SKILL.md:\n{skill_text}\n\nFailures:\n{fails}\n\n{EDIT_CONTRACT}')
        return _extract_json(self._call(self.optimizer_cmd, p)).get('edits', [])

    def analyze_successes(self, skill_text, successes) -> list:
        succ = '\n\n'.join(f'[{t.id}] {t.prompt}\n-> {out}' for t, out in successes)
        p = (f'Identify behaviors that already WORK and must be preserved. Propose only edits that '
             f'protect them (often none).\n\nSKILL.md:\n{skill_text}\n\nSuccesses:\n{succ}\n\n{EDIT_CONTRACT}')
        return _extract_json(self._call(self.optimizer_cmd, p)).get('edits', [])

    def merge_and_rank(self, skill_text, failure_edits, success_edits, budget, rejected) -> list:
        rej = '\n'.join(f'- {r}' for r in rejected) or '(none)'
        p = (f'Merge these edit proposals into at most {budget}. Drop duplicates, contradictions, and '
             f'task-specific edits; prioritize failure corrections over success-preservation; rank by '
             f'expected validation gain vs regression risk.\n\n'
             f'Failure edits:\n{json.dumps(failure_edits)}\n\nSuccess/preservation edits:\n'
             f'{json.dumps(success_edits)}\n\nDo NOT re-propose rejected edits:\n{rej}\n\n{EDIT_CONTRACT}')
        return _extract_json(self._call(self.optimizer_cmd, p)).get('edits', [])[:budget]
