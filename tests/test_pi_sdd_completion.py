"""Native SDD task recording requires matching intent and current independent acceptance."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.services import task_binding,checks
from aikya.workflows.sdd import engine
from pi_task_run_fixture import prepare,reviewed


class SddCompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.bound=prepare(self.root,'sdd')

    def service(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.sdd_completion'),'Native SDD completion is absent')
        return importlib.import_module('aikya.services.sdd_completion')

    def preview(self):return self.service().preview(self.root,'SPEC-001','TASK-001','task-proof','author')

    def test_binding_exposes_canonical_task_intent_without_an_execution_claim(self):
        self.assertEqual(self.bound.get('intent'),dict(objective='Return one',acceptance=['The value is one']))
        self.assertEqual(self.bound['status'],'task_bound')

    def test_unexecuted_or_unreviewed_task_cannot_be_recorded_done(self):
        with self.assertRaises(ValueError):self.preview()
        self.assertEqual(engine.load(self.root,'SPEC-001')[1]['tasks'][0]['status'],'todo')

    def test_current_admitted_acceptance_can_record_only_the_selected_task(self):
        reviewed(self.root);plan=self.preview();service=self.service()
        with self.assertRaises(ValueError):service.apply(self.root,plan)
        result=service.apply(self.root,plan,approved=True)
        self.assertEqual(result['status'],'task_recorded');self.assertFalse(result['delivery_authorized'])
        data=engine.load(self.root,'SPEC-001')[1]
        self.assertEqual(data['tasks'][0]['status'],'done');self.assertIsNone(data['verification'])
        with self.assertRaises(ValueError):service.apply(self.root,plan,approved=True)

    def test_changed_source_after_preview_cannot_record_a_done_task(self):
        reviewed(self.root);plan=self.preview();(self.root/'value.py').write_text('VALUE=2\n')
        with self.assertRaises(ValueError):self.service().apply(self.root,plan,approved=True)
        self.assertEqual(engine.load(self.root,'SPEC-001')[1]['tasks'][0]['status'],'todo')

    def test_other_author_or_changed_selection_cannot_use_the_same_acceptance(self):
        reviewed(self.root)
        with self.assertRaises(ValueError):self.service().preview(self.root,'SPEC-001','TASK-001','task-proof','other')
        plan=self.preview();task_binding.bind(self.root,'author','SPEC-001','TASK-001',['value.py'],approved=True)
        with self.assertRaises(ValueError):self.service().apply(self.root,plan,approved=True)

    def test_identical_sdd_reselection_revokes_an_older_write_grant(self):
        from aikya.services import authorization
        key=b'x'*32;intent=dict(path='value.py',content='VALUE=1\n')
        token=authorization.issue(self.root,'author',intent,key)
        task_binding.bind(self.root,'author','SPEC-001','TASK-001',['value.py','test.py'],approved=True)
        with self.assertRaises(ValueError):authorization.apply_write(self.root,'author',intent,token,key)

    def test_changed_review_during_recording_cannot_leave_the_task_done(self):
        reviewed(self.root);plan=self.preview();original=engine.progress
        def changed(*args,**kwargs):
            (self.root/'aikya/docs/validation/task-proof/review.md').write_text('Changed evidence\n')
            return original(*args,**kwargs)
        with patch.object(engine,'progress',side_effect=changed):
            with self.assertRaises(ValueError):self.service().apply(self.root,plan,approved=True)
        self.assertNotEqual(engine.load(self.root,'SPEC-001')[1]['tasks'][0]['status'],'done')

    def test_uncertain_completion_cannot_replay_or_invent_an_outcome(self):
        reviewed(self.root);plan=self.preview()
        with patch.object(engine,'progress',side_effect=OSError('Interrupted before metadata commit')):
            with self.assertRaises(OSError):self.service().apply(self.root,plan,approved=True)
        with self.assertRaises(ValueError):self.preview()
        self.assertEqual(engine.load(self.root,'SPEC-001')[1]['tasks'][0]['status'],'todo')


if __name__=='__main__':unittest.main()
