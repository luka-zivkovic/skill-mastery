# The SkillOpt Runner

`scripts/skillopt_run.py` implements the paper's loop end to end. This doc covers the
architecture, the adapter interface, and — honestly — what is and isn't reproducible.

## The loop (Algorithm 1, made runnable)

Per epoch, against a frozen target model:

1. **Rollout** on the train split → the target produces an output per task; score each to
   split successes from failures.
2. **Reflect** over the failing minibatch (≤8) → the optimizer model proposes **bounded**
   edits (`replace/append/prepend/insert_after/delete`) as a strict JSON contract. The
   rejected-edit buffer is fed in so known-bad edits aren't re-proposed.
3. **Apply** the edits atomically to a candidate copy (the protected `## Slow-update`
   region is never touched by step edits).
4. **Gate** on the held-out validation split, by tier:
   - `objective`: accept iff the candidate's mean strictly beats the current skill.
   - `rubric`: blind pairwise NEW-vs-OLD over the split, `grading_runs` times with
     re-randomized A/B order; accept iff NEW is a majority win in **every** run.
5. **Cache** by candidate skill hash so identical candidates aren't re-evaluated.
6. **Accept** → adopt the candidate, append a dated, validation-cited note to the
   slow-update region, and update `best_skill.md`. **Reject** → the edits go to the buffer.
7. Repeat until the edit budget (cosine-decayed from 4→2) and epochs are exhausted, or
   training failures hit zero.

Artifacts land in the `--out` dir: `best_skill.md`, `accepted/`, `rejected/`, and a
`skillopt-<skill>.log.jsonl` trace.

## Adapters (the only thing that calls a model)

`scripts/skillopt_adapters.py` defines `rollout`, `grade`, `propose_edits`, and
`judge_pairwise`. Two implementations ship:

- **`MockAdapter`** — deterministic, no model calls. Powers the tests, CI, and the offline
  demo. It encodes one learnable behavior so the loop provably converges.
- **`CommandAdapter`** — shells each prompt to a CLI (`claude`, `codex`, anything that
  reads a prompt on stdin and writes text on stdout). Pass a different `--optimizer-cmd`
  than `--target-cmd` so the editor never grades its own edit.

To add a harness (HTTP API, SDK, another CLI), subclass `Adapter` and implement its
methods. The orchestrator is harness-agnostic.

## The merge/rank pipeline (`--paper-pipeline`)

By default the runner makes **one** optimizer call per epoch (`propose_edits`). With
`--paper-pipeline` it runs the paper's 3-stage hierarchy: `analyze_failures` (corrective
edits) + `analyze_successes` (preservation edits, often none) → `merge_and_rank` (dedup
contradictory/task-specific edits, prioritize failures, rank, clip to the budget). That is
~3× the optimizer cost, so it's opt-in; `MAX_OPTIMIZER_CALLS_PER_EPOCH` bounds and asserts
it, and a guard guarantees a merge bug can never starve the budget when a fix exists.

## The slow/meta consolidation

At epoch end, after an accept, the runner compares prev-vs-current on validation (reusing
the gate's rollouts — **zero extra model calls**) and appends ONE dated, validation-cited
note to the protected region summarizing improved/regressed counts. It is **append-only and
non-blocking**: the motivating edit already passed the gate, and the paper's strict-greater
re-gate on advisory longitudinal prose (which ties) would systematically discard good notes
on the small splits we run. This is a deliberate, documented divergence from the paper.

## Paper-component coverage

| SkillOpt component | Status |
|---|---|
| Skill as trainable external state | ✅ skill text is the optimized artifact |
| Train / validation / test splits | ✅ parsed + enforced (`_manifest.py`, validator) |
| Scored rollouts | ✅ `rollout` + tier scoring |
| Failure minibatch reflection | ✅ over ≤8 failures |
| Success/preservation analysis | ⚠️ via `--paper-pipeline` (`analyze_successes`) |
| Merge/rank hierarchy (failure-prioritized) | ⚠️ via `--paper-pipeline` (`merge_and_rank`) |
| Bounded patch application | ✅ atomic, slow-update-protected (`apply_skill_patch.py`) |
| Edit-budget schedule | ✅ cosine decay 4→2 (`edit_budget`) |
| Held-out validation gate | ✅ tier-scoped (`gate_objective` / `gate_rubric`) |
| Score cache | ✅ by candidate hash |
| Rejected-edit buffer | ✅ fed back into reflection |
| Slow / meta update | ⚠️ epoch-end, append-only, **non-blocking** (relaxed from strict-gate — see above) |
| Harness adapters | ✅ mock + command; extensible |
| Export `best_skill.md` | ✅ |
| Reproduce the paper's benchmark gains | ❌ needs an automatic objective verifier + the paper's datasets |

## What is NOT reproducible (read this)

The headline results (avg +17.6 pts; −22.5 on a slow-update ablation) came from an
**automatic objective verifier** over benchmarks with crisp answers, run at scale. This
repo supplies the *mechanism*, not those datasets or that verifier. On your own tasks:

- `objective` tier is as trustworthy as your verifier.
- `rubric` tier is bounded by judge reliability — an LLM judge's errors correlate across
  runs, so "3 runs" are not statistically independent. Use a different judge model for any
  shipped accept; treat a same-model fresh-context judge as provisional.
- `subjective` work has no scored gate — use the lite path, not the runner.
