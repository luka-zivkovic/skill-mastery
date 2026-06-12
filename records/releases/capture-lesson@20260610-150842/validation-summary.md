# Validation summary — capture-lesson

Before snapshot included: yes
Eval result rows found: 0

## Change provenance — independent review round (2026-06-10)

Revision driven by 3 independent subagent reviews (two adversarial design reviewers,
one checking Anthropic's documented Agent Skills guidance) plus 6 edge-case probes.
Broad revision rather than bounded ops, justified per CLAUDE.md rule 7: the review
found a structural routing flaw (see below). Before/after in this package shows the
full diff. Slow-update region untouched.

Review recommendations adopted and declined are listed below; smoke evidence follows.

Adopted: explicit user asks ("remember this") now always get a response — the bar
gates agent-initiated captures only; day-scoped facts route to working context/handoff
with an explanation, never silently dropped; contradiction-replace with supersede note
and CLAUDE.md-retraction proposal; cap prune is consent-gated (show before → after,
get a yes; appends and strengthens stay automatic); `scope: project|all-tasks`
replaces the ambiguous `claude-md` enum, with `· promoted: YYYY-MM-DD` appended when
the user applies a CLAUDE.md line; one lesson per distinct root cause (post-mortems
may yield ~3); evidence compression on strengthen ("3x since 2026-04"); procedure
route never exits with nothing recorded; format stated once; bane narration and
duplicate Known-failure-modes section removed per docs guidance.

Declined: dropping the evidence field entirely (kept, but compressible); renaming the
skill (reviewer found capture-lesson fine).

## Smoke-test evidence (lite path, subjective tier)

Run 2026-06-10, fresh-context subagents, 6/6 PASS including three new edge rows
(smoke-004 explicit ask on day-scoped fact → routed + explained; smoke-005
contradiction → replaced with supersede; smoke-006 20-entry cap → nothing deleted
without a yes). Full log: workshop/evals/capture-lesson-smoke-tests.md.

## Human review notes

- Reviewer: independent subagent review round + Claude (Fable 5) session 2026-06-10; fix round approved by Luka Zivkovic.
- Decision: ship (6/6 smoke tests pass)
- Caveats: subjective tier — no scored gate. Existing lessons files written by the previous version use `scope: claude-md`; the revised skill reads them fine and writes `all-tasks` going forward.
