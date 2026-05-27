#!/usr/bin/env python3
"""Stdlib unittest suite for the skill-mastery toolkit.

Covers the invariants the feedback flagged as documented-but-unenforced: atomic +
slow-update-protected patching, the validation-only gate, NaN rejection, tier-scoped
accept rules, the manifest parser, sync-hash stability, the rejected-edit summary, and
a full deterministic runner epoch. Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import apply_skill_patch as patch  # noqa: E402
import record_eval_result as recorder  # noqa: E402
import _manifest as manifest  # noqa: E402
import _skilltext as skilltext  # noqa: E402
import summarize_skill_history as summarize  # noqa: E402
import sync_skill as syncmod  # noqa: E402
import skillopt_run as runner  # noqa: E402
import skillopt_adapters as adapters  # noqa: E402
import validate_skill as vskill  # noqa: E402
import audit_skills as audit  # noqa: E402
import lite_improve  # noqa: E402
import package_release  # noqa: E402
import start  # noqa: E402
import create_skill  # noqa: E402

# A real-world n8n-style skill: folded block-scalar description, plugin-namespaced
# name with a colon, allowed-tools, and a nested compatibility map. The old parser
# rejected all of these as "invalid frontmatter".
N8N_STYLE = """---
name: n8n:create-issue
description: >-
  Create Linear tickets or GitHub issues following n8n conventions. Use when the
  user asks to create a ticket, file a bug, or says /create-issue.
argument-hint: "[linear|github] <description>"
allowed-tools: Bash(gh:*), Read, Grep
compatibility:
  requires:
    - mcp: linear
      description: Required for Linear tickets
---

# Create issue

## Workflow
1. do it
"""

SKILL = """---
name: s
description: a skill long enough to satisfy the description length requirement here.
---

# S

## Constraints
- Do not include unrelated background.

## Slow-update (do not overwrite in single-pass edits)
- 2026-06-01: durable note citing val-001 and val-002.
"""


def write_skill(d: Path, text=SKILL) -> Path:
    (d / 'SKILL.md').write_text(text, encoding='utf-8')
    return d


class TestPatcher(unittest.TestCase):
    def test_atomic_rolls_back_on_later_failure(self):
        with tempfile.TemporaryDirectory() as d:
            sk = write_skill(Path(d))
            patches = [{'op': 'append', 'path': 'SKILL.md', 'text': 'ADDED'},
                       {'op': 'replace', 'path': 'SKILL.md', 'old': 'NOPE', 'new': 'x'}]
            with self.assertRaises(ValueError):
                patch.plan(sk, patches, allow_slow_update=False)
            self.assertNotIn('ADDED', (sk / 'SKILL.md').read_text())

    def test_slow_update_protected(self):
        with tempfile.TemporaryDirectory() as d:
            sk = write_skill(Path(d))
            edit = [{'op': 'replace', 'path': 'SKILL.md', 'old': 'durable note', 'new': 'HACKED'}]
            with self.assertRaises(ValueError):
                patch.plan(sk, edit, allow_slow_update=False)
            # allowed when the dedicated flow opts in
            patch.plan(sk, edit, allow_slow_update=True)

    def test_missing_target_refused(self):
        with tempfile.TemporaryDirectory() as d:
            sk = write_skill(Path(d))
            with self.assertRaises(ValueError):
                patch.plan(sk, [{'op': 'append', 'path': 'new.md', 'text': 'x'}], allow_slow_update=False)


class TestRecorder(unittest.TestCase):
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            recorder.parse_runs('nan 0.5 0.5')

    def test_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            recorder.parse_runs('1.5')

    def test_test_split_is_report_only(self):
        d, _ = recorder.decide('objective', [0.9, 0.9, 0.9], [0.1, 0.1, 0.1], 'test')
        self.assertEqual(d, 'report-only')

    def test_objective_regression_run_rejected(self):
        d, _ = recorder.decide('objective', [0.9, 0.6, 0.95], [0.7, 0.7, 0.7], 'validation')
        self.assertEqual(d, 'reject')

    def test_rubric_majority_every_run(self):
        self.assertEqual(recorder.decide('rubric', [0.75, 0.625, 0.9], None, 'validation')[0], 'accept')
        self.assertEqual(recorder.decide('rubric', [0.75, 0.5, 0.9], None, 'validation')[0], 'reject')


class TestManifest(unittest.TestCase):
    def test_parses_toy(self):
        m = manifest.load(ROOT / 'examples/toy-evals/eval-manifest.yaml')
        self.assertEqual(m.verifiability, 'rubric')
        self.assertEqual(len(m.splits['validation']), 8)
        self.assertEqual(m.splits['validation'][0].id, 'val-001')
        self.assertTrue(m.splits['validation'][0].success_criteria)

    def test_criterion_id_does_not_count_as_task(self):
        text = ("id: x\nskill: x\nverifiability: objective\n"
                "scoring:\n  accept_rule: validation_score_must_strictly_improve\n  grading_runs: 3\n"
                "source:\n  path: none\n  hash: none\ndeployed:\n  path: none\n  hash: none\n"
                "splits:\n  train:\n    - id: t1\n      prompt: p\n      success_criteria:\n        - ok\n"
                "  validation:\n    - id: v1\n      prompt: p\n      success_criteria:\n"
                "        - id: must be present\n  test:\n    - id: te1\n      prompt: p\n"
                "      success_criteria:\n        - ok\n")
        with tempfile.TemporaryDirectory() as d:
            mp = Path(d) / 'm.yaml'
            mp.write_text(text, encoding='utf-8')
            m = manifest.load(mp)
            self.assertEqual(len(m.splits['validation']), 1)


class TestSkillText(unittest.TestCase):
    def test_hash_stable(self):
        self.assertEqual(skilltext.skill_hash('abc'), skilltext.skill_hash('abc'))
        self.assertNotEqual(skilltext.skill_hash('abc'), skilltext.skill_hash('abd'))

    def test_append_note_into_region(self):
        out = skilltext.append_slow_update_note(SKILL, '2026-06-02: another note, val-003 and val-004.')
        self.assertIn('another note', skilltext.slow_update_body(out))


class TestSummary(unittest.TestCase):
    def test_rejection_reason_extracted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'r.json'
            p.write_text(json.dumps({'op': 'x', '_rejection': {'reason': 'too specific'}}), encoding='utf-8')
            self.assertEqual(summarize.rejection_reason(p), 'too specific')


class TestSyncHash(unittest.TestCase):
    def test_hash_ignores_records(self):
        with tempfile.TemporaryDirectory() as d:
            sk = write_skill(Path(d))
            h1 = syncmod.skill_hash(sk)
            (sk / 'records').mkdir()
            (sk / 'records' / 'x.txt').write_text('noise', encoding='utf-8')
            self.assertEqual(h1, syncmod.skill_hash(sk))


class TestSkillSpec(unittest.TestCase):
    def test_parses_block_scalar_and_namespaced_name(self):
        fm, body = vskill.parse_frontmatter(N8N_STYLE)
        self.assertEqual(fm['name'], 'n8n:create-issue')
        self.assertIn('Create Linear tickets', fm['description'])
        self.assertIn('Bash(gh:*)', fm['allowed-tools'])
        self.assertIn('Workflow', body)

    def test_real_spec_skill_has_no_errors(self):
        with tempfile.TemporaryDirectory() as d:
            sk = Path(d) / 'create-issue'
            sk.mkdir()
            (sk / 'SKILL.md').write_text(N8N_STYLE, encoding='utf-8')
            errors, _ = vskill.validate(sk, 500, 20000)
            self.assertEqual(errors, [], f'spec-valid skill should not error: {errors}')

    def test_name_is_optional(self):
        text = "---\ndescription: " + ("x" * 60) + "\n---\n\n# Body\ntext\n"
        with tempfile.TemporaryDirectory() as d:
            sk = Path(d) / 's'
            sk.mkdir()
            (sk / 'SKILL.md').write_text(text, encoding='utf-8')
            errors, _ = vskill.validate(sk, 500, 20000)
            self.assertEqual(errors, [])

    def test_length_is_warning_not_error(self):
        text = "---\nname: big\ndescription: " + ("x" * 60) + "\n---\n\n# B\n" + ("line\n" * 600)
        with tempfile.TemporaryDirectory() as d:
            sk = Path(d) / 'big'
            sk.mkdir()
            (sk / 'SKILL.md').write_text(text, encoding='utf-8')
            errors, warnings = vskill.validate(sk, 500, 20000)
            self.assertEqual(errors, [])
            self.assertTrue(any('line' in w or 'lines' in w for w in warnings))


class TestDiscover(unittest.TestCase):
    def test_dedupes_symlinks_and_prunes_node_modules(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            real = root / '.claude' / 'plugins' / 'p' / 'skills' / 'a'
            real.mkdir(parents=True)
            (real / 'SKILL.md').write_text(N8N_STYLE, encoding='utf-8')
            (root / '.claude' / 'skills').symlink_to('plugins/p/skills')  # n8n-style alias
            nm = root / 'node_modules' / 'dep' / 'skills' / 'x'
            nm.mkdir(parents=True)
            (nm / 'SKILL.md').write_text(N8N_STYLE, encoding='utf-8')
            found = audit.discover(root)
            self.assertEqual(len(found), 1, f'expected 1 skill, got {found}')


class TestOnboardingFlow(unittest.TestCase):
    def test_create_skill_scaffolds_new_skill_helpers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            shutil.copytree(ROOT / 'templates', root / 'templates')
            out = create_skill.create(
                'PR Reviewer',
                'Review pull requests against repo conventions. Use when a user asks for PR review help.',
                kind='codex',
                resources='references,scripts',
                root=root,
            )
            skill_dir = out['skill_dir']
            self.assertEqual(skill_dir.name, 'pr-reviewer')
            self.assertIn('name: pr-reviewer', (skill_dir / 'SKILL.md').read_text())
            self.assertTrue((skill_dir / 'agents' / 'openai.yaml').exists())
            self.assertTrue((skill_dir / 'references').is_dir())
            self.assertTrue((skill_dir / 'scripts').is_dir())
            self.assertTrue(out['smoke_tests'].exists())
            self.assertTrue(out['creation_brief'].exists())
            self.assertEqual(out['validation_errors'], [])

    def test_audit_includes_actionable_recommendation(self):
        with tempfile.TemporaryDirectory() as d:
            sk = Path(d) / 'thin'
            sk.mkdir()
            (sk / 'SKILL.md').write_text(N8N_STYLE, encoding='utf-8')
            result = audit.audit_one(sk / 'SKILL.md')
            self.assertIn(result['verdict'], {'keep', 'revise', 'split', 'retire'})
            self.assertIn('next_command', result)
            self.assertIn('suggested_patch_type', result)

    def test_start_chooses_revise_before_keep(self):
        results = [
            {'path': 'b/SKILL.md', 'grade': 'PASS', 'verdict': 'keep'},
            {'path': 'a/SKILL.md', 'grade': 'WARN', 'verdict': 'revise'},
        ]
        self.assertEqual(start.choose_next(results)['path'], 'a/SKILL.md')

    def test_lite_improve_scaffolds_workshop_copy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / 'source-skill'
            source.mkdir()
            write_skill(source)
            out = lite_improve.scaffold(source, root=root)
            self.assertTrue((out['skill_copy'] / 'SKILL.md').exists())
            self.assertTrue(out['smoke_tests'].exists())
            self.assertTrue(out['checklist'].exists())
            self.assertIn('Lite improvement checklist', out['checklist'].read_text())

    def test_package_release_writes_review_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            before = root / 'before'
            after = root / 'after'
            records = root / 'records'
            before.mkdir()
            after.mkdir()
            records.mkdir()
            write_skill(before, SKILL.replace('Do not include unrelated background.', 'Original rule.'))
            write_skill(after)
            release = package_release.package(after, before=before, records=records, version='test')
            self.assertTrue((release / 'before.md').exists())
            self.assertTrue((release / 'after.md').exists())
            self.assertTrue((release / 'validation-summary.md').exists())
            self.assertTrue((release / 'ship-checklist.md').exists())


class TestRunner(unittest.TestCase):
    def test_full_epoch_accepts_and_exports(self):
        with tempfile.TemporaryDirectory() as d:
            skdir = Path(d) / 'skill'
            skdir.mkdir()
            write_skill(skdir)
            out = runner.run(skdir,
                             ROOT / 'examples/toy-evals/eval-manifest.yaml',
                             adapters.MockAdapter(), epochs=3, out_dir=Path(d) / 'out')
            best = Path(out['best_path']).read_text()
            self.assertIn('Known failure modes', best)
            self.assertIn(adapters.MockAdapter.MARKER, best)

    def test_edit_budget_decays(self):
        self.assertEqual(runner.edit_budget(0, 4), 4)
        self.assertEqual(runner.edit_budget(3, 4), 2)

    def _run(self, tmp, **kw):
        skdir = Path(tmp) / 'skill'
        skdir.mkdir()
        write_skill(skdir)
        return runner.run(skdir, ROOT / 'examples/toy-evals/eval-manifest.yaml',
                          adapters.MockAdapter(), epochs=3, out_dir=Path(tmp) / 'out', **kw)

    def test_paper_pipeline_converges_same_as_single_pass(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            single = Path(self._run(a)['best_path']).read_text()
            piped = Path(self._run(b, paper_pipeline=True)['best_path']).read_text()
            self.assertIn(adapters.MockAdapter.MARKER, single)
            self.assertEqual(single, piped)  # both paths produce the identical best skill

    def test_empty_merge_does_not_starve_the_budget(self):
        # A broken merge that drops every edit must not stop the loop converging:
        # the runner's fallback re-applies the failure edits.
        class BrokenMerge(adapters.MockAdapter):
            def merge_and_rank(self, skill_text, failure_edits, success_edits, budget, rejected):
                return []
        with tempfile.TemporaryDirectory() as d:
            skdir = Path(d) / 'skill'
            skdir.mkdir()
            write_skill(skdir)
            out = runner.run(skdir, ROOT / 'examples/toy-evals/eval-manifest.yaml',
                             BrokenMerge(), epochs=3, out_dir=Path(d) / 'out', paper_pipeline=True)
            self.assertIn(adapters.MockAdapter.MARKER, Path(out['best_path']).read_text())

    def test_consolidation_note_is_appended_and_cited(self):
        with tempfile.TemporaryDirectory() as d:
            best = Path(self._run(d)['best_path']).read_text()
            region = skilltext.slow_update_body(best)
            self.assertIn('consolidation', region)
            self.assertIn('val-001', region)  # cites validation examples

    def test_call_budget_constant_bounds_pipeline(self):
        self.assertLessEqual(3, runner.MAX_OPTIMIZER_CALLS_PER_EPOCH)

    def test_merge_dedups_and_clips(self):
        m = adapters.MockAdapter()
        dup = {'op': 'append', 'path': 'SKILL.md', 'text': 'x'}
        out = m.merge_and_rank('s', [dup, dict(dup)], [], budget=1, rejected=[])
        self.assertEqual(len(out), 1)  # deduped + clipped to budget


if __name__ == '__main__':
    unittest.main()
