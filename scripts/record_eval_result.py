#!/usr/bin/env python3
"""Append a tiered, multi-run skill evaluation result to records/eval_results.jsonl.

Anti-noise by design: you record N independent grading runs (not one float), and
the accept decision is computed tier-aware so a single lucky run can't flip a gate.

  objective : accept iff mean(candidate) > mean(baseline) AND no candidate run
              dips below the baseline mean (no regression).
  rubric    : runs are pairwise win-rates of NEW vs OLD; accept iff every run is a
              majority win (> 0.5). Use --judge-model and --judge-blind to record
              that grading was independent (different model, blind pairwise).
  subjective: no scored gate — the result is recorded as qualitative review only.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

SCORED_TIERS = ('objective', 'rubric')


def parse_runs(raw: str) -> list[float]:
    """Parse a whitespace/comma-separated list of scores in [0, 1].

    Rejects non-finite (NaN/Inf) and out-of-range values: a NaN run would slip
    through every < / <= comparison in decide() and be silently accepted, and a
    non-finite score serializes to invalid JSON in eval_results.jsonl.
    """
    values = []
    for tok in raw.replace(',', ' ').split():
        try:
            x = float(tok)
        except ValueError as exc:
            raise ValueError(f'invalid score {tok!r}: not a number') from exc
        if not math.isfinite(x):
            raise ValueError(f'invalid score {tok!r}: must be finite')
        if not 0.0 <= x <= 1.0:
            raise ValueError(f'invalid score {tok!r}: must be within [0, 1]')
        values.append(x)
    return values


def decide(tier: str, runs: list[float], baseline: list[float] | None, split: str) -> tuple[str, str]:
    """Return (decision, rationale).

    The accept/reject GATE is validation-only. Train rollouts are observations and
    the test split is for periodic unbiased reporting — neither may flip a gate, or
    you are tuning on data you swore not to peek at.
    """
    if split != 'validation':
        return 'report-only', f'{split} split is not a gate; recorded for observation/reporting only'
    if tier == 'subjective':
        return 'qualitative-no-gate', 'subjective tier: no scored gate; recorded for review only'
    if not runs:
        return 'incomplete', 'no candidate runs provided'

    mean_c = sum(runs) / len(runs)
    if tier == 'rubric':
        if min(runs) > 0.5:
            return 'accept', f'every run a majority win (min={min(runs):.2f}, mean={mean_c:.2f})'
        return 'reject', f'not a majority win in every run (min={min(runs):.2f}, mean={mean_c:.2f})'

    # objective
    if baseline is None:
        return 'incomplete', 'objective tier requires --baseline-runs to decide'
    mean_b = sum(baseline) / len(baseline)
    if mean_c <= mean_b:
        return 'reject', f'mean did not strictly improve (cand={mean_c:.3f} <= base={mean_b:.3f})'
    if min(runs) < mean_b:
        return 'reject', f'regression: a run ({min(runs):.3f}) dipped below baseline mean ({mean_b:.3f})'
    return 'accept', f'mean improved ({mean_c:.3f} > {mean_b:.3f}) with no run below baseline'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('records_dir', type=Path)
    parser.add_argument('--skill', required=True)
    parser.add_argument('--split', required=True, choices=['train', 'validation', 'test'])
    parser.add_argument('--tier', required=True, choices=['objective', 'rubric', 'subjective'])
    parser.add_argument('--runs', required=True, help='candidate per-run scores, e.g. "0.8 0.9 0.85"')
    parser.add_argument('--baseline-runs', default='', help='baseline per-run scores (objective tier)')
    parser.add_argument('--version', default='unknown')
    parser.add_argument('--judge-model', default='', help='model used to grade (rubric tier)')
    parser.add_argument('--judge-blind', action='store_true', help='set when grading was blind + pairwise')
    parser.add_argument('--evidence', default='', help='pasted failing output / diff anchoring the score')
    parser.add_argument('--notes', default='')
    args = parser.parse_args()

    try:
        runs = parse_runs(args.runs)
        baseline = parse_runs(args.baseline_runs) if args.baseline_runs.strip() else None
    except ValueError as exc:
        print(f'ERROR: {exc}', flush=True)
        return 1

    if args.tier in SCORED_TIERS and len(runs) < 3:
        print(f'ERROR: {args.tier} tier needs >= 3 grading runs; got {len(runs)}', flush=True)
        return 1
    if args.tier == 'rubric' and not (args.judge_blind and args.judge_model):
        print('ERROR: rubric tier requires --judge-blind and --judge-model '
              '(blind pairwise, different model if possible)', flush=True)
        return 1

    decision, rationale = decide(args.tier, runs, baseline, args.split)

    args.records_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'skill': args.skill,
        'version': args.version,
        'split': args.split,
        'tier': args.tier,
        'runs': runs,
        'mean': round(sum(runs) / len(runs), 4) if runs else None,
        'baseline_runs': baseline,
        'baseline_mean': round(sum(baseline) / len(baseline), 4) if baseline else None,
        'judge_model': args.judge_model,
        'judge_blind': args.judge_blind,
        'decision': decision,
        'rationale': rationale,
        'evidence': args.evidence,
        'notes': args.notes,
    }
    output = args.records_dir / 'eval_results.jsonl'
    with output.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, sort_keys=True, allow_nan=False) + '\n')
    print(f'WROTE: {output}')
    print(f'DECISION: {decision} — {rationale}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
