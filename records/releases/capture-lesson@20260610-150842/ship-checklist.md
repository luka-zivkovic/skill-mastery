# Ship checklist — capture-lesson

- [x] `after.md` contains only the deployed skill content; no run logs or optimizer scratch notes.
- [x] Patch is bounded (broad revision justified by structural review finding; full before/after included) and reviewable.
- [x] Smoke tests or validation evidence are recorded in `validation-summary.md`.
- [x] Rejected alternatives, if any, are recorded (declined recommendations listed in validation-summary.md) in `records/rejected/`.
- [x] Slow-update notes are dated (region empty/untouched) and cite at least two validation examples when present.
- [x] Deployed skill path/hash has been synced (workshop == claude-skills, 2026-06-10) (`scripts/sync_skill.py`).
- [x] Owner accepted the caveats and shipped the patch (fix round approved 2026-06-10; shipped to claude-skills/).
