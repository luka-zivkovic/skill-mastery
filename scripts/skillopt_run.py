#!/usr/bin/env python3
"""SkillOpt runner — the paper's loop, made runnable (you supply the verifier).

A frozen target model executes tasks with the current skill; an optimizer model turns
the failures into BOUNDED edits; a held-out validation gate accepts only edits that
improve the tier's score; rejected edits become negative feedback; an epoch-end
slow-update note consolidates durable lessons; the best skill is exported.

What is real here vs. the paper: epochs, rollout, minibatch reflection, the cosine
edit-budget schedule, the tiered held-out gate, score cache, rejected-edit buffer, an
epoch-end slow/meta consolidation, and best_skill.md export are implemented. The paper's
3-stage merge/rank hierarchy (separate failure + success analysis, then a failure-
prioritized merge) is available behind --paper-pipeline (default is one optimizer call).
The slow-update consolidation is append-only and non-blocking rather than strict-gated —
a strict-greater re-gate on advisory longitudinal prose would systematically discard good
notes on the small splits we run. What the paper had and we cannot manufacture is an
automatic objective verifier over benchmark datasets — so scoring comes from YOUR verifier
(objective tier) or a blind pairwise judge (rubric tier). The mechanism is faithful; the
headline numbers are not transferable.

  # offline, deterministic demo (no model calls):
  python3 scripts/skillopt_run.py examples/toy-skill examples/toy-evals/eval-manifest.yaml \
      --adapter mock --epochs 2 --out workshop/runs

  # real models via CLIs (different model for the optimizer/judge is recommended):
  python3 scripts/skillopt_run.py <skill_dir> <manifest> --adapter command \
      --target-cmd "claude -p" --optimizer-cmd "claude -p --model claude-haiku-4-5"
"""
from __future__ import annotations

import argparse
import json
import math
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _manifest  # noqa: E402
from _skilltext import skill_hash, append_slow_update_note  # noqa: E402
from apply_skill_patch import plan as plan_patches  # noqa: E402
from skillopt_adapters import MockAdapter, CommandAdapter  # noqa: E402

PASS = 0.5  # score >= PASS counts as a success when finding failures
MAX_OPTIMIZER_CALLS_PER_EPOCH = 3  # single-pass=1; --paper-pipeline=3 (fail/success/merge). Bounds cost.


def edit_budget(epoch: int, epochs: int, hi: int = 4, lo: int = 2) -> int:
    """Cosine-decayed bounded edit budget: starts at hi, floors at lo."""
    if epochs <= 1:
        return hi
    frac = epoch / (epochs - 1)
    return max(lo, round(lo + (hi - lo) * 0.5 * (1 + math.cos(math.pi * frac))))


def apply_edits(skill_text: str, edits: list[dict], tmp: Path) -> str:
    """Apply bounded edits atomically to an isolated copy; return new skill text."""
    sk = tmp / 'SKILL.md'
    sk.write_text(skill_text, encoding='utf-8')
    result = plan_patches(tmp, edits, allow_slow_update=False)  # raises on bad anchor / slow-update touch
    return result.get(sk.resolve(), (skill_text, skill_text))[1]


def score_output(adapter, manifest, task, output: str) -> float:
    return adapter.grade(task.success_criteria or manifest.rubric_criteria, task.prompt, output)


def gate_objective(adapter, manifest, cur_text, cand_text, val_tasks):
    """Return (ok, detail, buckets). buckets reuses these same rollouts for the
    epoch-end slow-update note — no extra model calls."""
    improved = regressed = 0
    cur_sum = cand_sum = 0.0
    for t in val_tasks:
        cs = score_output(adapter, manifest, t, adapter.rollout(cur_text, t.prompt))
        ds = score_output(adapter, manifest, t, adapter.rollout(cand_text, t.prompt))
        cur_sum += cs
        cand_sum += ds
        if ds >= PASS > cs:
            improved += 1
        elif cs >= PASS > ds:
            regressed += 1
    cur, cand = cur_sum / len(val_tasks), cand_sum / len(val_tasks)
    return cand > cur, f'objective: candidate {cand:.3f} vs current {cur:.3f}', \
        {'improved': improved, 'regressed': regressed}


def gate_rubric(adapter, manifest, cur_text, cand_text, val_tasks, runs: int):
    """Blind pairwise NEW vs OLD over the validation split, n runs. Accept iff NEW is a
    majority win in EVERY run (re-randomizing A/B order each run). Returns
    (ok, detail, buckets); buckets is counted once for the slow-update note."""
    win_rates = []
    improved = regressed = 0
    for r in range(runs):
        wins = 0
        for i, t in enumerate(val_tasks):
            old = adapter.rollout(cur_text, t.prompt)
            new = adapter.rollout(cand_text, t.prompt)
            swap = (r + i) % 2 == 1  # deterministic order-randomization without RNG
            a, b = (old, new) if swap else (new, old)
            verdict = adapter.judge_pairwise(t.success_criteria or manifest.rubric_criteria, t.prompt, a, b)
            new_label = 'B' if swap else 'A'
            won = verdict == new_label
            wins += int(won)
            if r == 0:
                if won:
                    improved += 1
                elif verdict != 'tie':
                    regressed += 1
        win_rates.append(wins / len(val_tasks))
    ok = all(w > 0.5 for w in win_rates)
    return ok, f'rubric: win-rates {[round(w, 3) for w in win_rates]} (accept iff all > 0.5)', \
        {'improved': improved, 'regressed': regressed}


def run(skill_dir: Path, manifest_path: Path, adapter, epochs: int, out_dir: Path,
        paper_pipeline: bool = False) -> dict:
    manifest = _manifest.load(manifest_path)
    skill_text = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
    train, val = manifest.splits['train'], manifest.splits['validation']
    if not val:
        raise SystemExit('manifest has no validation tasks — cannot gate')

    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f'skillopt-{manifest.skill}.log.jsonl'
    cache: dict[str, bool] = {}
    rejected: list[str] = []
    best_text, best_marker = skill_text, 'baseline'
    tmp = out_dir / '_tmp'
    tmp.mkdir(exist_ok=True)

    def log(event: dict):
        event['ts'] = datetime.now(timezone.utc).isoformat()
        with log_path.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(event, sort_keys=True) + '\n')
        print(f"[{event['event']}] " + event.get('msg', ''))

    log({'event': 'start',
         'msg': f'{manifest.skill} tier={manifest.verifiability} epochs={epochs} '
                f'pipeline={"paper" if paper_pipeline else "single-pass"}',
         'skill_hash': skill_hash(skill_text)})

    for epoch in range(epochs):
        budget = edit_budget(epoch, epochs)
        # 1. Rollout on train; find the recurring failure.
        failures, successes = [], []
        for t in train:
            out = adapter.rollout(skill_text, t.prompt)
            (successes if score_output(adapter, manifest, t, out) >= PASS else failures).append((t, out))
        log({'event': 'rollout', 'msg': f'epoch {epoch}: {len(failures)} fail / {len(successes)} pass, budget={budget}'})
        if not failures:
            log({'event': 'converged', 'msg': f'epoch {epoch}: no training failures left'})
            break

        # 2. Reflect over the failing minibatch -> bounded edits (rejected buffer fed back).
        #    Default: one optimizer call. --paper-pipeline: the 3-stage hierarchy
        #    (analyze failures, analyze successes/preservation, merge+rank+clip).
        if paper_pipeline:
            fe = adapter.analyze_failures(skill_text, failures[:8])
            se = adapter.analyze_successes(skill_text, successes[:8])
            edits = adapter.merge_and_rank(skill_text, fe, se, budget, rejected)
            if fe and not edits:  # a merge bug must never starve the budget when a fix exists
                edits = fe[:budget]
            calls = 3
        else:
            edits = adapter.propose_edits(skill_text, failures[:8], successes[:8], budget, rejected)
            calls = 1
        assert calls <= MAX_OPTIMIZER_CALLS_PER_EPOCH
        if not edits:
            log({'event': 'no-edits', 'msg': f'epoch {epoch}: optimizer proposed nothing'})
            break

        # 3. Apply atomically to a candidate copy (skips the protected slow-update region).
        try:
            candidate = apply_edits(skill_text, edits, tmp)
        except ValueError as exc:
            rejected.append(f'unappliable: {exc}')
            log({'event': 'reject', 'msg': f'epoch {epoch}: edits did not apply atomically: {exc}'})
            continue

        h = skill_hash(candidate)
        if h in cache:
            log({'event': 'cache', 'msg': f'epoch {epoch}: candidate {h} already evaluated -> {cache[h]}'})
            if not cache[h]:
                continue

        # 4. Tiered gate on the held-out validation split (buckets reused for the note).
        if manifest.verifiability == 'objective':
            ok, detail, buckets = gate_objective(adapter, manifest, skill_text, candidate, val)
        elif manifest.verifiability == 'rubric':
            ok, detail, buckets = gate_rubric(adapter, manifest, skill_text, candidate, val, manifest.grading_runs)
        else:
            raise SystemExit('subjective tier has no scored gate; use the lite path, not the runner')
        cache[h] = ok

        if not ok:
            for e in edits:
                rejected.append(e.get('rationale') or json.dumps(e))
            (out_dir / 'rejected').mkdir(exist_ok=True)
            (out_dir / 'rejected' / f'epoch{epoch}.json').write_text(json.dumps(edits, indent=2), encoding='utf-8')
            log({'event': 'reject', 'msg': f'epoch {epoch}: {detail}'})
            continue

        # 5. Accept the bounded edit (step-level edits never touch the protected region).
        skill_text = candidate
        (out_dir / 'accepted').mkdir(exist_ok=True)
        (out_dir / 'accepted' / f'epoch{epoch}.json').write_text(json.dumps(edits, indent=2), encoding='utf-8')
        log({'event': 'accept', 'msg': f'epoch {epoch}: {detail}', 'skill_hash': skill_hash(skill_text)})

        # 6. Epoch-end slow/meta consolidation: compare prev-vs-current on validation
        #    (buckets from the gate — zero extra calls) and append ONE dated, cited note to
        #    the protected region. Append-only and NON-BLOCKING: the motivating edit already
        #    passed the gate, and a strict-greater re-gate on advisory longitudinal prose
        #    (which ties) would systematically discard good notes on small splits.
        cited = ' and '.join(t.id for t in val[:2]) or 'the validation split'
        date = datetime.now(timezone.utc).date().isoformat()
        note = (f'{date}: epoch-{epoch} consolidation — {buckets["improved"]} validation example(s) '
                f'improved, {buckets["regressed"]} regressed; confirmed on {cited}.')
        skill_text = append_slow_update_note(skill_text, note)
        best_text, best_marker = skill_text, f'epoch{epoch}'

    best_path = out_dir / 'best_skill.md'
    best_path.write_text(best_text, encoding='utf-8')
    for leftover in tmp.glob('*'):  # don't leak scratch files into run artifacts
        leftover.unlink()
    tmp.rmdir()
    log({'event': 'done', 'msg': f'best={best_marker} -> {best_path}', 'skill_hash': skill_hash(best_text)})
    return {'best_marker': best_marker, 'best_path': str(best_path), 'rejected': rejected}


def build_adapter(args) -> object:
    if args.adapter == 'mock':
        return MockAdapter()
    if args.adapter == 'command':
        if not args.target_cmd:
            raise SystemExit('--adapter command requires --target-cmd')
        opt = shlex.split(args.optimizer_cmd) if args.optimizer_cmd else None
        return CommandAdapter(shlex.split(args.target_cmd), opt)
    raise SystemExit(f'unknown adapter {args.adapter}')


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('skill_dir', type=Path)
    p.add_argument('manifest', type=Path)
    p.add_argument('--adapter', choices=['mock', 'command'], default='mock')
    p.add_argument('--target-cmd', default='')
    p.add_argument('--optimizer-cmd', default='')
    p.add_argument('--epochs', type=int, default=4)
    p.add_argument('--out', type=Path, default=Path('workshop/runs'))
    p.add_argument('--paper-pipeline', action='store_true',
                   help="use the paper's 3-stage merge/rank (failure+success analysis -> merge) "
                        "instead of one optimizer call; ~3x the optimizer cost")
    args = p.parse_args()

    result = run(args.skill_dir, args.manifest, build_adapter(args), args.epochs, args.out,
                 paper_pipeline=args.paper_pipeline)
    print(f"\nbest skill: {result['best_path']} (from {result['best_marker']})")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
