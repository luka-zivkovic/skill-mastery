# Skill Audit (qualitative + smoke tests)

`audit_skills.py` covers the mechanical layer. This prompt is the judgment layer: read
one skill and assess what a static check can't, then produce smoke tests. Run it per
skill, in a fresh context. Do NOT edit the skill here — audit only.

## Inputs

- The full `SKILL.md` (and any `references/`, `scripts/`, `assets/`).
- The static audit findings for this skill (paste the relevant section).

## Part A — qualitative audit

Assess and report concretely (quote the offending lines):

1. **Clarity & routing.** Would another agent know exactly when to invoke this and what to
   do? Flag ambiguous rules, undefined terms, and steps that assume missing context.
2. **Dead / redundant instruction.** Lines that restate the model's defaults, duplicate
   each other, or never change behavior. These are token cost with no payoff.
3. **Over-specification.** Rules hardcoded to one example that won't generalize (the
   SkillOpt anti-pattern). Name them.
4. **Tool-policy gaps.** Missing "use X, never Y" guidance where the task has a house
   convention or a footgun.
5. **Failure modes.** What recurring mistake is this skill silent about? Propose the
   missing guardrail (as a finding, not an edit).
6. **Coherence.** Is the skill trying to cover heterogeneous domains that should be split?

Output a short list of findings, each tagged `clarity | dead | overspec | tool | failure |
coherence` with the quoted line and a one-sentence fix. Do not rewrite the skill.

## Part B — smoke tests (the lite-path artifact)

Draft **3** smoke-test prompts that exercise the skill's core path and at least one edge it
claims to handle. For each: the prompt, the observable pass criterion, and which finding
from Part A it would catch if regressed. Keep criteria checkable, not vibes.

Write them into a `smoke-tests.md` next to the skill (or into `workshop/evals/<name>.md`).
These are the cheapest possible regression net — most skills need nothing more.

## Part C — verdict

One line: **keep / revise / split / retire**, and **lite-path or full loop** (apply the
`docs/when-to-optimize.md` gate). If full loop, name the verifiability tier and why.
