# Workshop

Where the loop actually runs. Iterate on **copies** here, never on deployed skills.

```
workshop/
├── skills/   # local copies of skills under iteration (new drafts or copies of existing)
├── evals/    # eval manifests per skill (one per skill, tiered)
└── runs/     # per-run logs: rollouts, proposed edits, gate decisions
```

## One iteration, end to end

0. **Decide it's worth it.** Full loop only if reuse ≥ ~10×, a verifier exists, and the
   skill failed ≥2× for real. Otherwise use the lite path (`docs/when-to-optimize.md`).
1. **Create or copy in.** For a brand-new draft, run
   `python3 scripts/create_skill.py <name> --description "Do X. Use when..."`; it creates
   the workshop copy, creation brief, smoke-test worksheet, and records folders. For an
   existing deployed skill, prefer `python3 scripts/lite_improve.py /path/to/skill`; it
   creates the workshop copy, smoke-test worksheet, and checklist. If doing it manually, put
   the skill in `workshop/skills/<name>/`. If it's a deployed skill, run
   `python3 scripts/sync_skill.py check workshop/skills/<name> workshop/evals/<name>.yaml`
   first — it refuses to start if the copy drifted from what's deployed.
2. **Pick the tier.** Set `verifiability` in the manifest: `objective`, `rubric`, or
   `subjective`. This decides how the gate works. Validate it:
   `python3 scripts/validate_eval_manifest.py workshop/evals/<name>.yaml`.
3. **Rollout.** Run the skill on the **train** split. Record what failed and why. For a
   minibatch (~8 cases) look for the *recurring* failure, not one-off anecdotes.
4. **Reflect → bounded edits.** Use `prompts/optimizer/failure_analysis.md`. Propose
   `replace/append/prepend/insert_after/delete` edits. Generalize; don't hardcode task
   values. Paste the `rejected edits to avoid` block from `summarize_skill_history.py` so
   you don't re-propose a known-bad edit. Apply to the copy with `apply_skill_patch.py`.
5. **Gate on validation, by tier:**
   - `objective`: run the verifier; accept iff mean improves and no run regresses.
   - `rubric`: grade old-vs-new **blind, pairwise, randomized order**, with a **different
     model if available** (`prompts/optimizer/rubric_judge.md`); accept iff NEW wins a
     majority every run (≥3 runs).
   - `subjective`: no scored gate — review qualitatively and note it as such.
   Record it: `python3 scripts/record_eval_result.py records --skill <name> --split validation
   --tier <tier> --runs "..." [--baseline-runs "..."] --judge-model <m> --judge-blind --evidence "..."`.
6. **Buffer rejections.** Rejected edits land in `records/rejected/` and feed step 4 next pass.
7. **Snapshot + slow-update.** Snapshot the accepted skill into `records/snapshots/`. At
   epoch end, consolidate durable lessons into the skill's protected `## Slow-update`
   region — each note citing ≥2 validation examples and dated.
8. **Test + package + ship.** Periodically check the **test** split (don't tune on it). On
   real improvement, package the review artifact with
   `python3 scripts/package_release.py workshop/skills/<name> --before /path/to/deployed/skill`,
   then sync/copy the accepted patch back to the deployed location and record whether it
   shipped.
