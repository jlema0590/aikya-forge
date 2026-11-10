"""One durable native task run retains caps, owner and accounting across restarts."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.routing import pi_usage
from aikya.services import checks
from pi_task_run_fixture import prepare,reviewed


class TaskRunTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.task_runs'),'Bounded native task runs are absent')
        self.runs=importlib.import_module('aikya.services.task_runs')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        prepare(self.root)
        self.args=dict(change_id='task-proof',session_id='author',provider='fixture',model='fixture',
            limits=dict(calls=6,seconds=300,corrections=1),security=dict(checks=[],not_applicable='No security behavior changes; independently review this bounded constant change.'))

    def preview(self,**extra):return self.runs.preview(self.root,**{**self.args,**extra})

    def start(self,**extra):
        plan=self.preview(**extra)
        with self.assertRaises(ValueError):self.runs.start(self.root,plan)
        return self.runs.start(self.root,plan,approved=True)

    def record_call(self,call='author-call'):
        pi_usage.admit(self.root,call,dict(session='author',role='author',phase='implement',provider='fixture',model='fixture'))
        pi_usage.record(self.root,call,dict(input=5,output=3,cacheRead=0,cacheWrite=0))

    def test_read_only_preview_has_current_intent_scope_and_no_run_effect(self):
        value=self.preview()
        self.assertEqual(value['selection']['intent'],dict(objective='Return one',acceptance=['The value is one']))
        self.assertEqual(value['selection']['files'],['test.py','value.py'])
        self.assertEqual(value['limits'],dict(calls=6,seconds=300,corrections=1))
        self.assertFalse((self.root/'.aikya/pi/task-runs').exists())

    def test_start_is_confirmed_and_another_run_cannot_own_the_project(self):
        result=self.start();self.assertEqual(result['status'],'running');self.assertEqual(result['phase'],'explore')
        with self.assertRaises(ValueError):self.preview()
        with self.assertRaises(ValueError):self.runs.guard(self.root,result['run_id'],'another-author')
        self.assertEqual(self.runs.guard(self.root,result['run_id'],'author')['status'],'available')

    def test_missing_selection_or_foreign_intent_cannot_start(self):
        (self.root/'.aikya/pi/odd-workflow.json').unlink()
        with self.assertRaises(ValueError):self.preview()
        self.assertFalse((self.root/'.aikya/pi/task-runs').exists())

    def test_frozen_intent_must_match_the_selected_task(self):
        plan=checks.refresh_preview(self.root,'task-proof','author');plan['arguments']['objective']='Another objective'
        updated=checks.preview_snapshot(self.root,**plan['arguments']);checks.apply_snapshot(self.root,updated,approved=True)
        with self.assertRaises(ValueError):self.preview()

    def test_invalid_limits_or_unreviewed_security_applicability_is_refused(self):
        for limits in (dict(calls=21,seconds=300,corrections=1),dict(calls=6,seconds=601,corrections=1),dict(calls=6,seconds=300,corrections=2)):
            with self.subTest(limits=limits),self.assertRaises(ValueError):self.preview(limits=limits)
        for security in (dict(checks=[]),dict(checks=['unknown'],not_applicable=None),dict(checks=['tests'],not_applicable='Skip')):
            with self.subTest(security=security),self.assertRaises(ValueError):self.preview(security=security)

    def test_calls_cap_survives_service_recreation_and_budget_adjustment(self):
        result=self.start(limits=dict(calls=1,seconds=300,corrections=1));self.record_call()
        pi_usage.adjust(self.root,tokens=2000,calls=30,approved=True)
        state=self.runs.guard(self.root,result['run_id'],'author')
        self.assertEqual(state['status'],'calls_exhausted');self.assertEqual(state['calls_spent'],1)
        again=importlib.import_module('aikya.services.task_runs')
        self.assertEqual(again.guard(self.root,result['run_id'],'author')['calls_spent'],1)

    def test_unknown_usage_stops_further_task_inference(self):
        result=self.start()
        pi_usage.admit(self.root,'uncertain-call',dict(session='author',role='author',phase='implement',provider='fixture',model='fixture'))
        self.assertEqual(self.runs.guard(self.root,result['run_id'],'author')['status'],'unknown_usage')

    def test_deadline_cannot_be_extended_by_restarting_or_resuming(self):
        result=self.start();deadline=int(result['deadline_ns'])
        with patch('aikya.services.task_runs.time.time_ns',return_value=deadline+1):
            state=self.runs.guard(self.root,result['run_id'],'author')
            self.assertEqual(state['status'],'deadline_exceeded')
        self.assertEqual(self.runs.status(self.root,'author')['deadline_ns'],str(deadline))

    def test_manual_source_outside_the_frozen_scope_stops_the_task(self):
        result=self.start();(self.root/'unreviewed.py').write_text('UNREVIEWED = True\n')
        self.assertEqual(self.runs.guard(self.root,result['run_id'],'author')['status'],'source_changed')
        self.assertEqual(self.runs.status(self.root,'author')['status'],'source_changed')

    def test_in_scope_write_keeps_task_selection_without_reselecting_it(self):
        result=self.start();(self.root/'value.py').write_text('VALUE=1\n')
        self.assertEqual(self.runs.guard(self.root,result['run_id'],'author')['status'],'available')

    def test_changed_task_policy_or_corrupted_record_is_preserved_and_refused(self):
        result=self.start();state=self.root/'.aikya/pi/task-runs'/ (result['run_id']+'.json')
        value=json.loads(state.read_text());value['mac']='0'*64;state.write_text(json.dumps(value))
        with self.assertRaises(ValueError):self.runs.guard(self.root,result['run_id'],'author')
        self.assertEqual(json.loads(state.read_text())['mac'],'0'*64)

    def test_current_approved_sdd_task_uses_the_same_run_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();prepare(root,'sdd')
            plan=self.runs.preview(root,**self.args)
            self.assertEqual(plan['selection']['methodology'],'sdd')
            self.assertEqual(plan['selection']['intent'],dict(objective='Return one',acceptance=['The value is one']))
            result=self.runs.start(root,plan,approved=True)
            self.assertEqual(self.runs.guard(root,result['run_id'],'author')['status'],'available')

    def test_explicit_stop_and_confirmed_resume_keep_original_caps_and_spend(self):
        result=self.start();run_id=result['run_id'];self.record_call()
        self.assertTrue(callable(getattr(self.runs,'halt',None)),'Native task stop is absent')
        self.runs.halt(self.root,run_id,'author','user_stop')
        self.assertEqual(self.runs.guard(self.root,run_id,'author')['status'],'needs_host_action')
        plan=self.runs.resume_preview(self.root,run_id,'author','fixture','fixture')
        with self.assertRaises(ValueError):self.runs.resume(self.root,plan)
        resumed=self.runs.resume(self.root,plan,approved=True)
        self.assertEqual(resumed['run_id'],run_id);self.assertEqual(resumed['deadline_ns'],result['deadline_ns'])
        self.assertEqual(self.runs.guard(self.root,run_id,'author')['calls_spent'],1)

    def test_expired_run_cannot_resume_with_a_fresh_deadline(self):
        result=self.start();run_id=result['run_id']
        self.assertTrue(callable(getattr(self.runs,'halt',None)),'Native task stop is absent')
        self.runs.halt(self.root,run_id,'author','user_stop')
        with patch('aikya.services.task_runs.time.time_ns',return_value=int(result['deadline_ns'])+1):
            with self.assertRaises(ValueError):self.runs.resume_preview(self.root,run_id,'author','fixture','fixture')

    def test_resume_confirmation_binds_current_in_scope_source_bytes(self):
        result=self.start();run_id=result['run_id']
        self.runs.halt(self.root,run_id,'author','user_stop')
        plan=self.runs.resume_preview(self.root,run_id,'author','fixture','fixture')
        (self.root/'value.py').write_text('VALUE=1\n')
        with self.assertRaises(ValueError):self.runs.resume(self.root,plan,approved=True)

    def test_phase_labels_do_not_create_acceptance_or_allow_fake_corrections(self):
        result=self.start();run_id=result['run_id']
        self.assertTrue(callable(getattr(self.runs,'advance',None)),'Native task phase progression is absent')
        self.runs.advance(self.root,run_id,'author','review')
        with self.assertRaises(ValueError):self.runs.correct(self.root,run_id,'author')
        self.assertFalse(checks.status(self.root,'task-proof')['can_close'])

    def test_only_one_correction_can_use_actual_current_independent_findings(self):
        result=self.start();run_id=result['run_id'];reviewed(self.root,decision='changes_requested')
        self.assertTrue(callable(getattr(self.runs,'advance',None)),'Native task phase progression is absent')
        self.runs.advance(self.root,run_id,'author','review')
        value=self.runs.correct(self.root,run_id,'author')
        self.assertEqual(value['status'],'correction_ready')
        self.assertEqual(value['findings'][0]['path'],'value.py')
        self.assertEqual(self.runs.status(self.root,'author')['corrections_used'],1)
        self.runs.advance(self.root,run_id,'author','review')
        with self.assertRaises(ValueError):self.runs.correct(self.root,run_id,'author')

    def test_run_can_record_only_current_independently_accepted_odd_work(self):
        from aikya.workflows import odd
        result=self.start();run_id=result['run_id']
        self.assertTrue(callable(getattr(self.runs,'completion_preview',None)),'Native run completion is absent')
        with self.assertRaises(ValueError):self.runs.completion_preview(self.root,run_id,'author')
        reviewed(self.root);self.runs.advance(self.root,run_id,'author','review')
        plan=self.runs.completion_preview(self.root,run_id,'author')
        with self.assertRaises(ValueError):self.runs.complete(self.root,plan)
        value=self.runs.complete(self.root,plan,approved=True)
        self.assertEqual(value['status'],'recorded');self.assertFalse(value['delivery_authorized'])
        self.assertEqual(odd.load(self.root,'expected-value')['tasks'][0]['status'],'done')
        self.assertEqual(self.runs.status(self.root,'author',run_id)['state'],'recorded')
        self.assertEqual(self.runs.status(self.root,'author')['status'],'no_active_run')
        with self.assertRaises(ValueError):self.runs.complete(self.root,plan,approved=True)

    def test_run_can_record_current_sdd_acceptance_without_approving_the_whole_spec(self):
        from aikya.workflows.sdd import engine
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();prepare(root,'sdd');plan=self.runs.preview(root,**self.args)
            result=self.runs.start(root,plan,approved=True);run_id=result['run_id'];reviewed(root)
            self.assertTrue(callable(getattr(self.runs,'completion_preview',None)),'Native run completion is absent')
            self.runs.advance(root,run_id,'author','review')
            plan=self.runs.completion_preview(root,run_id,'author');value=self.runs.complete(root,plan,approved=True)
            self.assertEqual(value['status'],'recorded')
            self.assertIsNone(engine.load(root,'SPEC-001')[1]['verification'])

    def test_known_task_recording_can_be_reconciled_without_repeating_it(self):
        from aikya.services import odd_workflow
        result=self.start();run_id=result['run_id'];reviewed(self.root)
        self.assertTrue(callable(getattr(self.runs,'completion_preview',None)),'Native run completion is absent')
        self.runs.advance(self.root,run_id,'author','review');plan=self.runs.completion_preview(self.root,run_id,'author')
        completion=importlib.import_module('aikya.services.task_run_completion')
        with patch.object(completion,'finalize',side_effect=OSError('Interrupted after native task recording')):
            with self.assertRaises(OSError):self.runs.complete(self.root,plan,approved=True)
        value=self.runs.completion_recovery_preview(self.root,run_id,'author')
        self.assertEqual(value['status'],'reconciliation_ready')
        with patch.object(odd_workflow,'apply',side_effect=AssertionError('Do not replay task recording')):
            recovered=self.runs.recover_completion(self.root,value['plan'],approved=True)
        self.assertEqual(recovered['status'],'recorded')

    def test_changed_run_checkpoint_does_not_offer_completion_recovery(self):
        result=self.start();run_id=result['run_id'];reviewed(self.root)
        self.runs.advance(self.root,run_id,'author','review');plan=self.runs.completion_preview(self.root,run_id,'author')
        completion=importlib.import_module('aikya.services.task_run_completion')
        with patch.object(completion,'finalize',side_effect=OSError('Interrupted after native task recording')):
            with self.assertRaises(OSError):self.runs.complete(self.root,plan,approved=True)
        self.runs.halt(self.root,run_id,'author','user_stop')
        value=self.runs.completion_recovery_preview(self.root,run_id,'author')
        self.assertEqual(value['status'],'manual_reconciliation')
        self.assertIsNone(value['plan'])

    def test_inference_guard_binds_author_and_independent_current_reviewer_to_run_caps(self):
        self.assertTrue(callable(getattr(self.runs,'inference_guard',None)),'Per-call native task guard is absent')
        self.assertEqual(self.runs.inference_guard(self.root,'author','author','fixture','fixture')['status'],'available')
        value=self.start();run_id=value['run_id']
        self.assertEqual(self.runs.inference_guard(self.root,'other','author','fixture','fixture')['status'],'foreign_run')
        self.assertEqual(self.runs.inference_guard(self.root,'author','author','other','fixture')['status'],'model_changed')
        self.assertEqual(self.runs.inference_guard(self.root,'reviewer','reviewer','fixture','fixture','task-proof','unknown')['status'],'foreign_review')
        reviewed(self.root);self.runs.advance(self.root,run_id,'author','review')
        from aikya.review.candidates import load_candidate
        candidate=load_candidate(self.root,'task-proof')['id']
        actual=self.runs.inference_guard(self.root,'independent','reviewer','fixture','fixture','task-proof',candidate)
        self.assertEqual(actual['status'],'available')
        self.assertEqual(actual['run_id'],run_id)

    def test_preimplementation_checks_require_actual_red_without_replaying_existing_evidence(self):
        result=self.start()
        before=self.runs.status(self.root,'author')
        self.assertEqual(before.get('pre_checks'),[dict(check='tests',expected='failed')])
        reviewed(self.root)
        self.assertEqual(self.runs.status(self.root,'author').get('pre_checks'),[])

    def test_uncertain_native_completion_blocks_inference_even_before_metadata_effects(self):
        from aikya.services import odd_workflow
        result=self.start();run_id=result['run_id'];reviewed(self.root)
        self.runs.advance(self.root,run_id,'author','review');plan=self.runs.completion_preview(self.root,run_id,'author')
        with patch.object(odd_workflow,'apply',side_effect=OSError('Host interrupted before known completion')):
            with self.assertRaises(OSError):self.runs.complete(self.root,plan,approved=True)
        guard=self.runs.inference_guard(self.root,'author','author','fixture','fixture')
        self.assertEqual(guard['status'],'uncertain_effect')
        self.runs.halt(self.root,run_id,'author','user_stop')
        with self.assertRaises(ValueError):self.preview()
        value=self.runs.completion_recovery_preview(self.root,run_id,'author')
        self.assertEqual(value['status'],'manual_reconciliation')

    def test_only_a_checkpoint_of_this_current_run_review_can_skip_resumed_inference(self):
        result=self.start();run_id=result['run_id'];reviewed(self.root)
        self.assertTrue(callable(getattr(self.runs,'remember_review',None)),'Durable run review checkpoint is absent')
        self.runs.advance(self.root,run_id,'author','review')
        self.assertFalse(self.runs.status(self.root,'author')['completion_ready'])
        self.runs.remember_review(self.root,run_id,'author')
        self.assertTrue(self.runs.status(self.root,'author')['completion_ready'])
        self.runs.halt(self.root,run_id,'author','declined')
        plan=self.runs.resume_preview(self.root,run_id,'author','fixture','fixture')
        self.assertEqual(plan['continuation'],'record_completion')
        (self.root/'value.py').write_text('VALUE=2\n')
        self.assertFalse(self.runs.status(self.root,'author',run_id)['completion_ready'])
        with self.assertRaises(ValueError):self.runs.resume(self.root,plan,approved=True)
        self.assertEqual(self.runs.resume_preview(self.root,run_id,'author','fixture','fixture')['continuation'],'author')

    def test_resumed_local_recording_needs_no_new_model_capacity(self):
        result=self.start(limits=dict(calls=1,seconds=300,corrections=1));run_id=result['run_id'];reviewed(self.root)
        self.runs.advance(self.root,run_id,'author','review');self.runs.remember_review(self.root,run_id,'author')
        self.runs.halt(self.root,run_id,'author','declined')
        plan=self.runs.resume_preview(self.root,run_id,'author','fixture','fixture')
        self.assertEqual(plan['continuation'],'record_completion')
        self.runs.resume(self.root,plan,approved=True)
        self.assertEqual(self.runs.guard(self.root,run_id,'author')['status'],'calls_exhausted')
        final=self.runs.completion_preview(self.root,run_id,'author')
        recorded=self.runs.complete(self.root,final,approved=True)
        self.assertEqual(recorded['status'],'recorded');self.assertEqual(recorded['usage']['calls_spent'],1)


if __name__=='__main__':unittest.main()
