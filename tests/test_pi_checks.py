"""Native frozen-check workflows must observe Red/Green and explicit host execution."""
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
try:checks=importlib.import_module('aikya.services.checks')
except ModuleNotFoundError:checks=None


class PiChecksTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(checks,'Native check workflow host boundary is absent')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        (self.root/'value.txt').write_text('wrong')
        (self.root/'check.py').write_text('from pathlib import Path\nok=Path("value.txt").read_text()=="correct"\nprint("TAP version 13")\nprint("1..1")\nprint(("ok" if ok else "not ok")+" 1 - expected value")\nraise SystemExit(0 if ok else 1)\n')
        self.definition=dict(name='tests',argv=[sys.executable,'-I','-B','check.py'],cwd='.',report_format='tap',timeout_seconds=3,max_output_bytes=65536)
        self.args=dict(change_id='native-check',session_id='author',scope=['value.txt','check.py'],definitions=[self.definition],
                       objective='Return the expected value',acceptance=['The value is correct'],tdd_paths=['check.py'])

    def snapshot(self):
        plan=checks.preview_snapshot(self.root,**self.args)
        with self.assertRaises(ValueError):checks.apply_snapshot(self.root,plan)
        return checks.apply_snapshot(self.root,plan,approved=True)

    def run_check(self,run_id):
        plan=checks.preview_run(self.root,'native-check','tests','author',run_id)
        with self.assertRaises(ValueError):checks.execute(self.root,plan)
        return checks.execute(self.root,plan,approved=True)

    def test_complete_red_green_keeps_delivery_separate_and_binds_review_intent(self):
        first=self.snapshot();self.assertEqual(self.run_check('red')['status'],'failed')
        (self.root/'value.txt').write_text('correct')
        second=self.snapshot();self.assertNotEqual(first['candidate'],second['candidate'])
        self.assertEqual(self.run_check('green')['status'],'completed')
        result=checks.status(self.root,'native-check')
        self.assertEqual(result['status'],'review_required');self.assertFalse(result['can_close'])
        self.assertFalse(result['delivery_authorized'])
        from aikya.services.review import context
        packet=context(self.root,'native-check')
        self.assertEqual(packet['intent']['objective'],self.args['objective'])
        self.assertEqual(packet['checks']['tests']['status'],'passed')

    def test_no_approval_stale_preview_replay_or_definition_edit_can_launch(self):
        plan=checks.preview_snapshot(self.root,**self.args)
        self.assertFalse((self.root/'.aikya').exists())
        (self.root/'value.txt').write_text('correct')
        with self.assertRaises(ValueError):checks.apply_snapshot(self.root,plan,approved=True)
        self.assertFalse((self.root/'.aikya').exists())
        self.snapshot();plan=checks.preview_run(self.root,'native-check','tests','author','run-1')
        self.assertEqual(checks.execute(self.root,plan,approved=True)['status'],'completed')
        with self.assertRaises(ValueError):checks.execute(self.root,plan,approved=True)
        with self.assertRaises(ValueError):checks.preview_run(self.root,'native-check','tests','other-author','run-2')

    def test_native_cancel_stops_a_running_owned_check_without_replaying(self):
        from concurrent.futures import ThreadPoolExecutor
        import time
        from aikya.services import check_cancel
        (self.root/'check.py').write_text('import os,time\nfrom pathlib import Path\nPath(os.environ["AIKYA_TEST_REPORT"]).with_name("started").write_text("yes")\ntime.sleep(3)\nprint("TAP version 13")\nprint("1..1")\nprint("ok 1 - completed")\n')
        self.snapshot();plan=checks.preview_run(self.root,'native-check','tests','author','cancel-1')
        started=self.root/'aikya/docs/validation/native-check/checks/cancel-1/started'
        with ThreadPoolExecutor(1) as pool:
            future=pool.submit(checks.execute_host,self.root,plan,approved=True)
            deadline=time.monotonic()+3
            while not started.exists() and time.monotonic()<deadline:time.sleep(.02)
            self.assertTrue(started.exists())
            check_cancel.request(self.root,'native-check','author','cancel-1',plan['candidate'])
            self.assertEqual(future.result(timeout=6)['status'],'cancelled')
        with self.assertRaises(ValueError):checks.execute_host(self.root,plan,approved=True)

    def test_native_recovery_requires_the_private_host_observation_not_only_public_json(self):
        from aikya.review.recovery import plan_reconciliation,recover_execution
        (self.root/'value.txt').write_text('correct');self.snapshot();self.run_check('known-run')
        journal=self.root/'aikya/docs/validation/native-check/receipts.jsonl';journal.unlink()
        self.assertEqual(plan_reconciliation(self.root,'native-check')['attempts'][0]['action'],'attach_observation')
        recover_execution(self.root,'native-check','known-run',approved=True)
        journal.unlink()
        proof=self.root/'.aikya/pi/check-observations/native-check/known-run.json';proof.unlink(missing_ok=True)
        self.assertEqual(plan_reconciliation(self.root,'native-check')['attempts'][0]['action'],'manual_reconciliation')
        with self.assertRaises(ValueError):recover_execution(self.root,'native-check','known-run',approved=True)

    def test_iteration_refreshes_only_the_frozen_scope_and_executes_after_one_host_confirmation(self):
        self.snapshot();self.run_check('red')
        (self.root/'value.txt').write_text('correct')
        plan=checks.iteration_preview(self.root,'native-check','tests','author','green-iteration')
        self.assertIsNotNone(plan['snapshot'])
        with self.assertRaises(ValueError):checks.execute_iteration(self.root,plan)
        result=checks.execute_iteration(self.root,plan,approved=True)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(result['assessment']['status'],'review_required')
        self.assertFalse(result['assessment']['delivery_authorized'])

    def test_iteration_cancel_before_new_snapshot_prevents_process_launch(self):
        from aikya.services import check_cancel
        self.snapshot();(self.root/'value.txt').write_text('correct')
        plan=checks.iteration_preview(self.root,'native-check','tests','author','cancel-before-launch')
        check_cancel.request(self.root,'native-check','author','cancel-before-launch',plan['candidate'])
        result=checks.execute_iteration(self.root,plan,approved=True)
        self.assertEqual(result['status'],'cancelled')
        self.assertIsNone(result['counts'])

    def test_refresh_preserves_check_order_and_the_selected_regression_check(self):
        self.args['definitions'].append({**self.definition,'name':'lint'})
        self.snapshot();(self.root/'value.txt').write_text('correct')
        plan=checks.refresh_preview(self.root,'native-check','author')
        checks.apply_snapshot(self.root,plan,approved=True)
        from aikya.review.candidates import load_candidate
        candidate=load_candidate(self.root,'native-check')
        self.assertEqual(candidate['policy']['checks'],['tests','lint'])
        self.assertEqual(candidate['policy']['tdd']['check'],'tests')

    def test_snapshot_uses_project_language_and_refuses_a_changed_language_preview(self):
        from aikya.documentation.language import write_approved
        import json
        write_approved(self.root,'es')
        plan=checks.preview_snapshot(self.root,**self.args)
        (self.root/'.aikya/docs-policy.json').write_text(json.dumps(dict(schema_version=1,language='en')))
        with self.assertRaises(ValueError):checks.apply_snapshot(self.root,plan,approved=True)
        self.assertFalse((self.root/'aikya/docs/validation/native-check').exists())
        (self.root/'.aikya/docs-policy.json').write_text(json.dumps(dict(schema_version=1,language='es')))
        checks.apply_snapshot(self.root,plan,approved=True)
        report=self.root/('aikya/docs/validation/native-check/snapshot-'+plan['candidate']+'.md')
        self.assertTrue(report.read_text().startswith('# Cambio congelado'))
        self.assertEqual(report.read_text().count('GENERATED BY AIKYA FORGE'),1)

    def test_code_requires_tdd_and_unknown_check_registry_is_preserved(self):
        args={**self.args,'tdd_paths':None,'not_applicable':'Skip testing'}
        with self.assertRaises(ValueError):checks.preview_snapshot(self.root,**args)
        self.snapshot()
        path=self.root/'.aikya/pi/checks/native-check.json';path.write_text('{"custom":true}')
        with self.assertRaises(ValueError):checks.preview_run(self.root,'native-check','tests','author','unknown')
        self.assertEqual(path.read_text(),'{"custom":true}')


if __name__=='__main__':unittest.main()
