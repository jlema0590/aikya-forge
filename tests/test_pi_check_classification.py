"""Executed process checks and positive refactor baselines cannot masquerade as TDD."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from aikya.services import checks
from aikya.services.review import context
from aikya.review.candidates import load_candidate
from aikya.review.receipts import load_receipts


class CheckClassificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        (self.root/'main.tf').write_text('resource "local_file" "example" {}\n')
        self.definition=dict(name='validate',argv=[sys.executable,'-I','-B','-c','print("validated")'],
                             cwd='.',report_format='process',timeout_seconds=3,max_output_bytes=65536)
        self.args=dict(change_id='classified',session_id='author',scope=['main.tf'],definitions=[self.definition],
                       objective='Validate local infrastructure',acceptance=['Configuration validates'],
                       change_kind='infrastructure',not_applicable='No application behavior; run the local validator')

    def snapshot(self):
        plan=checks.preview_snapshot(self.root,**self.args)
        checks.apply_snapshot(self.root,plan,approved=True)
        return plan

    def execute_check(self,run_id):
        plan=checks.preview_run(self.root,'classified',self.args['definitions'][0]['name'],'author',run_id)
        return checks.execute(self.root,plan,approved=True)

    def test_process_success_has_no_test_counts_and_still_requires_review(self):
        self.snapshot();result=self.execute_check('valid')
        self.assertEqual(result['status'],'completed');self.assertIsNone(result['counts'])
        row=load_receipts(self.root,'classified')[0]['payload']
        self.assertIsNone(row['executed']);self.assertIsNone(row['failed']);self.assertIsNone(row['skipped'])
        assessment=checks.status(self.root,'classified')
        self.assertEqual(assessment['status'],'review_required');self.assertFalse(assessment['can_close'])
        self.assertFalse(assessment['delivery_authorized'])
        packet=context(self.root,'classified')
        self.assertEqual(packet['check_evidence']['validate']['check_type'],'process')
        self.assertEqual(packet['intent']['change_kind'],'infrastructure')

    def test_process_nonzero_and_test_like_stdout_cannot_be_test_evidence(self):
        self.args['definitions']=[{**self.definition,'argv':[sys.executable,'-I','-B','-c',
            'print("TAP version 13\\n1..1\\nnot ok 1 - failure");raise SystemExit(1)']}]
        self.snapshot();result=self.execute_check('invalid')
        self.assertEqual(result['status'],'failed');self.assertIsNone(result['counts'])
        self.assertEqual(checks.status(self.root,'classified')['status'],'failed')

    def test_cancelled_process_is_not_positive_evidence(self):
        self.snapshot();plan=checks.preview_run(self.root,'classified','validate','author','cancel')
        result=checks.execute(self.root,plan,approved=True,cancel=lambda:True)
        self.assertEqual(result['status'],'cancelled');self.assertIsNone(result['counts'])
        self.assertEqual(checks.status(self.root,'classified')['status'],'failed')

    def test_process_output_limit_is_not_positive_evidence(self):
        self.args['definitions']=[{**self.definition,'argv':[sys.executable,'-I','-B','-c','print("x"*4000)'],
                                  'max_output_bytes':1024}]
        self.snapshot();self.assertEqual(self.execute_check('overflow')['status'],'output_limit')
        self.assertEqual(checks.status(self.root,'classified')['status'],'failed')

    def test_code_cannot_hide_behind_nonbehavior_classification(self):
        (self.root/'app.py').write_text('print("changed behavior")\n')
        for kind in ('documentation','configuration','infrastructure'):
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                checks.preview_snapshot(self.root,**{**self.args,'scope':['app.py'],'change_kind':kind})
        self.assertFalse((self.root/'.aikya').exists())

    def test_missing_reason_unknown_kind_or_mixed_tdd_is_rejected(self):
        for extra in ({'not_applicable':None},{'change_kind':'skip'}, {'tdd_paths':['main.tf']},
                      {'baseline_paths':['main.tf']},{'change_kind':'behavior'}):
            with self.subTest(extra=extra),self.assertRaises(ValueError):
                checks.preview_snapshot(self.root,**{**self.args,**extra})

    def test_process_cannot_supply_the_required_regression_or_baseline(self):
        for extra in ({'change_kind':'behavior','not_applicable':None,'tdd_paths':['main.tf']},
                      {'change_kind':'refactor','baseline_paths':['main.tf']}):
            with self.subTest(extra=extra),self.assertRaises(ValueError):
                checks.preview_snapshot(self.root,**{**self.args,**extra})

    def test_refresh_keeps_classification_and_process_policy(self):
        self.snapshot();self.execute_check('before')
        (self.root/'main.tf').write_text('# changed declaration\n')
        plan=checks.refresh_preview(self.root,'classified','author')
        checks.apply_snapshot(self.root,plan,approved=True);self.execute_check('after')
        candidate=load_candidate(self.root,'classified')
        self.assertEqual(candidate['policy']['check_types'],{'validate':'process'})
        self.assertEqual(checks.bound_intent(self.root,candidate)['change_kind'],'infrastructure')
        self.assertEqual(checks.status(self.root,'classified')['status'],'review_required')

    def refactor(self):
        (self.root/'app.py').write_text('value = 1\n')
        (self.root/'test.py').write_text('import app\nassert app.value == 1\nprint("TAP version 13\\n1..1\\nok 1 - value")\n')
        definition={**self.definition,'name':'tests','report_format':'tap','argv':[sys.executable,'-B','test.py']}
        self.args.update(scope=['app.py','test.py'],definitions=[definition],change_kind='refactor',
                         baseline_paths=['test.py'],not_applicable='Preserve behavior using an executed positive baseline')

    def test_refactor_requires_unchanged_positive_ancestor_then_current_checks(self):
        self.refactor();self.snapshot();self.assertEqual(self.execute_check('baseline')['status'],'completed')
        self.assertEqual(checks.status(self.root,'classified')['status'],'baseline_required')
        (self.root/'app.py').write_text('value = int("1")\n')
        refresh=checks.refresh_preview(self.root,'classified','author')
        self.assertEqual(refresh['arguments']['baseline_paths'],['test.py'])
        checks.apply_snapshot(self.root,refresh,approved=True)
        self.assertEqual(self.execute_check('refactored')['status'],'completed')
        self.assertEqual(checks.status(self.root,'classified')['status'],'review_required')

    def test_changed_tests_restart_refactor_baseline(self):
        self.refactor();self.snapshot();self.execute_check('baseline')
        (self.root/'test.py').write_text((self.root/'test.py').read_text()+'# changed test\n')
        self.snapshot();self.execute_check('changed-tests')
        self.assertEqual(checks.status(self.root,'classified')['status'],'baseline_required')

    def test_no_positive_ancestor_cannot_claim_refactor_validation(self):
        self.refactor();self.snapshot()
        (self.root/'app.py').write_text('value = int("1")\n')
        self.snapshot();self.execute_check('current-only')
        self.assertEqual(checks.status(self.root,'classified')['status'],'baseline_required')

    def test_recovery_attaches_known_process_observation_without_replay(self):
        self.snapshot();self.execute_check('observed')
        journal=self.root/'aikya/docs/validation/classified/receipts.jsonl';journal.unlink()
        plan=checks.recovery_preview(self.root,'classified','author','observed')
        result=checks.recover(self.root,plan,approved=True)
        self.assertEqual(result['assessment']['status'],'review_required')
        with self.assertRaises(ValueError):checks.preview_run(self.root,'classified','validate','author','observed')

    def test_forged_test_counts_on_process_observation_are_rejected(self):
        self.snapshot();result=self.execute_check('observed')
        path=self.root/result['evidence'];value=json.loads(path.read_text())
        value['counts']=dict(executed=1,failed=0,skipped=0);path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):checks.status(self.root,'classified')

    def test_documentation_and_configuration_validate_with_explicit_nonapplicability(self):
        for kind,path,content in (('documentation','guide.md','# Guide\n\nGENERATED BY AIKYA FORGE\n'),
                                  ('configuration','settings.toml','enabled = true\n')):
            with self.subTest(kind=kind):
                (self.root/path).write_text(content)
                args={**self.args,'change_id':kind,'scope':[path],'change_kind':kind}
                plan=checks.preview_snapshot(self.root,**args);checks.apply_snapshot(self.root,plan,approved=True)
                execution=checks.preview_run(self.root,kind,'validate','author',kind)
                self.assertIsNone(checks.execute(self.root,execution,approved=True)['counts'])
                self.assertEqual(checks.status(self.root,kind)['status'],'review_required')

    def test_failed_baseline_does_not_validate_refactor(self):
        self.refactor();(self.root/'app.py').write_text('value = 2\n')
        self.snapshot();self.assertEqual(self.execute_check('failed-baseline')['status'],'failed')
        (self.root/'app.py').write_text('value = 1\n')
        self.snapshot();self.execute_check('current-positive')
        self.assertEqual(checks.status(self.root,'classified')['status'],'baseline_required')

    def test_legacy_snapshot_does_not_acquire_new_policy_or_intent_fields(self):
        self.refactor();self.args.pop('baseline_paths');self.args.pop('change_kind')
        self.args.update(tdd_paths=['test.py'],not_applicable=None)
        self.snapshot();candidate=load_candidate(self.root,'classified')
        self.assertNotIn('check_types',candidate['policy'])
        self.assertNotIn('change_kind',checks.bound_intent(self.root,candidate))
        refreshed=checks.refresh_preview(self.root,'classified','author')
        self.assertNotIn('change_kind',refreshed['arguments'])

    def test_behavior_green_cannot_borrow_failed_process_as_red(self):
        self.refactor();self.args.pop('baseline_paths')
        self.args.update(change_kind='behavior',tdd_paths=['test.py'],not_applicable=None)
        (self.root/'app.py').write_text('value = 2\n')
        process={**self.definition,'argv':[sys.executable,'-B','-c','import app;raise SystemExit(0 if app.value==1 else 1)']}
        self.args['definitions'].append(process)
        self.snapshot()
        plan=checks.preview_run(self.root,'classified','validate','author','failed-process')
        self.assertEqual(checks.execute(self.root,plan,approved=True)['status'],'failed')
        (self.root/'app.py').write_text('value = int("1")\n')
        self.snapshot();self.execute_check('green')
        plan=checks.preview_run(self.root,'classified','validate','author','positive-process')
        checks.execute(self.root,plan,approved=True)
        self.assertEqual(checks.status(self.root,'classified')['status'],'tdd_red_required')


if __name__=='__main__':unittest.main()
