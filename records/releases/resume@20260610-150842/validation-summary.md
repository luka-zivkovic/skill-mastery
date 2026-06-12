# Validation summary — resume

Before snapshot included: yes
Eval result rows found: 0

## Change provenance — independent review round (2026-06-10)

Revision driven by 3 independent subagent reviews (two adversarial design reviewers,
one checking Anthropic's documented Agent Skills guidance) plus 6 edge-case probes.
Broad revision rather than bounded ops, justified per CLAUDE.md rule 7: the review
found a structural routing flaw (see below). Before/after in this package shows the
full diff. Slow-update region untouched.

Review recommendations adopted and declined are listed below; smoke evidence follows.

Adopted: honest triggers (removed the impossible "fires at session start when
.ai/handoff.md exists" claim — skills route off message text); gone-sha fallback
(`git log --since=<stamp date>`, State marked unverified); branch-mismatch +
dirty-tree checks; unrelated-new-task carve-out (lessons load, one-line handoff
mention, no ceremony); stamp format quoted identically to handoff's; missing-section
fallback; lessons-over-cap + lessons-outrank-handoff rules; "~15 lines" instead of
"half a screen"; skill-chaining phrased as behavior with names parenthetical;
résumé/CV negative trigger; bane narration and duplicate Known-failure-modes section
removed per docs guidance ("state what to do rather than narrating how or why");
SessionStart hook companion added (references/session-start-hook.md) as the
documented mechanism for true session-start auto-load.

Declined: stripping the `## Slow-update` region from the deployed copy (it is this
repo's lifecycle contract, hard rule 8, and the patcher protects it).

## Smoke-test evidence (lite path, subjective tier)

Run 2026-06-10, fresh-context subagents, 5/5 PASS including two new edge rows
(smoke-004 rewritten history → prescribed fallback used verbatim; smoke-005
unrelated new task → no ceremony, lessons applied). Full log:
workshop/evals/resume-smoke-tests.md.

## Human review notes

- Reviewer: independent subagent review round + Claude (Fable 5) session 2026-06-10; fix round approved by Luka Zivkovic.
- Decision: ship (5/5 smoke tests pass)
- Caveats: subjective tier — no scored gate. Auto-load at session start requires installing the SessionStart hook (references/session-start-hook.md); the skill alone fires only on verbal triggers.
