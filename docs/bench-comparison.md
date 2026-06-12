# Skill-library head-to-head — claude-skills vs codex-skills

**Experiment:** same harness (both runners = Claude `general-purpose` subagents, same model),
identical task prompt, only the skill library + worktree differ. Each ran the full chain
clarify → audit → roadmap → pick → build → self-review → verify on **coeval** and chose its
own bounded item. Base commit `489753d` (main), baseline green (typecheck clean, 170 tests).

**You judge.** Below is everything assembled for a fast manual call: what each picked, the
actual diffs, independent re-verification, and an observation table. Verdict column is yours.

---

## TL;DR

| | **claude-skills** (branch `bench/claude-run`) | **codex-skills** (branch `bench/codex-run`) |
|---|---|---|
| Item picked | Correctness bug: duplicate skill-version strings in `DemoRepository.createSkillVersion` | Security bug: CSV formula injection (CWE-1236) in verdict export |
| File(s) changed | `apps/api/src/repository.ts` + 1 test | `apps/api/src/app.ts` + 2 tests |
| Net code | ~6 LOC fix + 1 regression test | ~25 LOC fix + 2 regression tests |
| Tests after | **171** passed / 13 skipped (+1) | **172** passed / 13 skipped (+2) |
| Typecheck | clean (independently re-run) | clean (independently re-run) |
| Tree ends green | ✅ | ✅ |
| Runner cost | 133.8k tokens, 61 tool calls, 462s | 81.8k tokens, 54 tool calls, 464s |
| Skills used | sharpen-request → audit-app → roadmap → simplest-thing → review-code → prove-it | app-clarifier → app-audit (+app-map) → roadmap-from-audit → vertical-slice-builder → change-reviewer → verify-change |

Both runs are correct, surgical, tested, and verified green. This was **not** a case of one
library failing — it's a quality/style comparison between two strong results.

---

## The biggest structural difference

**codex-skills carry machinery the claude-skills don't:**
- `app-audit` ran an executable helper (`app-map/scripts/repo_inventory.py`) for a first-pass
  inventory, and scored against a checked-in rubric (`references/audit-rubric.md`) → produced
  a **1–5 scorecard across 8 dimensions** (product fit, architecture, code quality, UX, tests,
  security, perf, devex).
- `roadmap-from-audit` used `references/roadmap-template.md` → **themed milestones (M1/M2/M3)**
  with exit criteria.

**claude-skills are leaner / "one bane each":** no scripts, no rubric files; output is tighter
(Map → Top risks → Triage → Next). It did the same evidence-gathering by hand (grep/find/read).

Trade-off visible in the numbers: codex produced more structured output for **40% fewer tokens**
(81.8k vs 133.8k). The claude run spent more doing the inventory work by hand that codex got
from a script.

---

## What each found (both are real bugs)

**claude-skills → correctness.** `createSkillVersion` always bumped the *seed* version
(`nextPatchVersion(demoSkill.currentVersion.version)`), so two consecutive skill edits both
produced `1.2.1` — corrupting the PR #60 version-history audit trail. Fix derives the next
version from the latest stored version. Found by reading the area the audit flagged "investigate
next." Severity: medium (data-integrity in a shipped feature).

**codex-skills → security.** The verdict CSV export RFC-4180-quoted cells but didn't neutralize
formula-injection (CWE-1236): a reviewer's `rationale` like `=HYPERLINK("http://evil","x")`
would execute when an operator opens the export in Excel/Sheets — and the export is explicitly
marketed for "audits / offline analysis." Fix adds per-column formula neutralization. Severity:
arguably higher (code-exec trust-boundary in a security-positioned product).

Both independently flagged the same top *non-code* risk: **`docs/07-phase-1-5-fix-list.md` is
stale** — every "must land" item already shipped. Good cross-validation that the audits were real.

---

## Self-review: did the review skill earn its place?

- **codex `change-reviewer`** caught a genuine **over-neutralization bug in its own first draft**
  (it had quoted numeric columns, which would turn a legit `-0.5` into text), fixed it with
  per-column tagging, and added a second regression test — *before* verify. The review changed
  the code. Strong signal the skill does real work, not rubber-stamping.
- **claude `review-code`** found no blocking issue but **traced a shared-state interaction**
  (`priorVersionId` now resolving to the seed id) and grep-proved it behavior-preserving rather
  than hand-waving. Non-rubber-stamp, but it confirmed rather than corrected.

Edge to codex here purely because its review *caught and fixed* a defect; claude's had less to
catch given the smaller change.

---

## Observation table (you fill the Verdict)

| Axis | claude-skills | codex-skills | Verdict |
|---|---|---|---|
| Clarify quality | 5-field spec, assumptions marked `(assumed)` | objective/scope/non-goals/acceptance + discovered fix-list stale | ☐ |
| Audit depth | hand-built map+risks+triage, explicit sample disclosure | scripted inventory + 8-dim rubric scorecard + evidence | ☐ |
| Roadmap quality | 5 ROI-ranked slices, honest "addendum" pivot to a better find | themed M1–M3 milestones w/ exit criteria | ☐ |
| Pick judgment | medium correctness bug, cleanest code slice | higher-severity security bug | ☐ |
| Code simplicity | ~6 LOC, reuses existing pattern, no new abstraction | ~25 LOC, introduces a per-cell `{value,text}` tag | ☐ |
| Test quality | 1 regression test (before/after proof) | 2 tests (attack + over-escaping guard) | ☐ |
| Self-review value | traced + cleared an interaction | **caught + fixed a real bug in own diff** | ☐ |
| Verification rigor | falsifiable claims, before/after on buggy vs fixed | baseline-vs-treatment table, caveats noted | ☐ |
| Faithfulness to skills | followed each SKILL.md workflow + output format | same, + actually used scripts/references | ☐ |
| Efficiency | 133.8k tok | **81.8k tok** | ☐ |

---

## Read the full artifacts

Each worktree has a `_run/` folder with the per-phase output:

- claude: `_bench/coeval-claude/_run/{00-clarify,01-audit,02-roadmap,03-build-notes,04-review,05-verify,skill-log}.md`
- codex:  `_bench/coeval-codex/_run/{…same…}.md`

Diffs:
```
git -C /Users/makina/startups/coeval log --oneline bench/claude-run -1
git -C /Users/makina/startups/coeval log --oneline bench/codex-run  -1
git -C /Users/makina/startups/skill-mastery/_bench/coeval-claude diff HEAD~1 -- . ':(exclude)_run'
git -C /Users/makina/startups/skill-mastery/_bench/coeval-codex  diff HEAD~1 -- . ':(exclude)_run'
```

---

## My read (non-binding — you decide)

It's close and both are strong. **codex-skills** edged ahead on this run: higher-severity find,
more structured audit/roadmap output, a self-review that *changed the code*, and ~40% fewer
tokens — largely because its skills ship executable scripts + rubric references that the
claude-skills replicate by hand. **claude-skills** produced a tighter, lower-LOC fix and a more
honest roadmap narrative (it openly pivoted its pick when build prep surfaced a better bug),
which some teams will value more. If you want a cleaner apples-to-apples on the *code* (same
target item for both), re-run with a fixed pick — say so and I'll set it up.

---

## Cleanup when done

```
git -C /Users/makina/startups/coeval worktree remove _bench/coeval-claude
git -C /Users/makina/startups/coeval worktree remove _bench/coeval-codex
git -C /Users/makina/startups/coeval branch -D bench/claude-run bench/codex-run
```
(Or keep them and cherry-pick either fix onto main — both are merge-ready.)
