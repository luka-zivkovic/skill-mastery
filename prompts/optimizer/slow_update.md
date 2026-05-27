# Slow Update

Write durable optimizer lessons into the skill's protected `## Slow-update` region.
This region is the highest-blast-radius part of the skill — get it wrong and you can erase
hard-won behavior. Only consolidate lessons that repeated across the epoch.

## Format every note must follow (the linter enforces this)

Each note is one bullet that:

1. **Carries a date** in `YYYY-MM-DD` form.
2. **Cites ≥ 2 validation examples** that motivated it — use the IDs from the manifest
   (e.g. `val-003`, `val-007`). Naming the examples keeps the note auditable and prunable.
3. States a **durable, generalizable** lesson — not a task-specific answer, not a bulky
   example, not a restatement of the model's defaults.

Example:

```
- 2026-06-01: Always end with the explicit self-check line — its absence caused misses on
  val-002 and val-006 (answer drifted from the stated objective).
```

`summarize_skill_history.py --skill <dir>` flags any note that is undated or cites fewer
than two examples as a prune candidate. Do not overwrite existing dated notes in a
single-pass edit; only the epoch-end consolidation writes here.
