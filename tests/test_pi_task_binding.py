"""SDD approval is necessary but never authorizes an unrelated session or path."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from aikya.services import authorization as auth
from aikya.workflows.sdd import engine as sdd


class TaskBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        (self.root/'.harness').mkdir()
        (self.root/'.harness/project-profile.json').write_text(json.dumps({'decisions':{'project_type':'development','methodology':'sdd'}}))
        (self.root/'value.py').write_text('VALUE=1\n')
        fixture=Path(__file__).resolve().parents[1]/'examples/sdd/development/order-api'
        self.inputs={k:json.loads((fixture/(k+'.json')).read_text()) for k in ('spec','clarify','plan','tasks')}
        self.intent={'path':'value.py','content':'VALUE=2\n'};self.key=os.urandom(32)

    def ready(self):
        sdd.initialize(self.root,self.inputs['spec']);sdd.clarify(self.root,'SPEC-001',self.inputs['clarify'])
        sdd.approve(self.root,'SPEC-001','spec','owner');sdd.create_plan(self.root,'SPEC-001',self.inputs['plan'])
        sdd.approve(self.root,'SPEC-001','plan','owner');sdd.create_tasks(self.root,'SPEC-001',self.inputs['tasks'])
        sdd.approve(self.root,'SPEC-001','tasks','owner')

    def bind(self,**kw):
        from aikya.services.task_binding import bind
        return bind(self.root,'session-a','SPEC-001','TASK-001',['value.py'],**kw)

    def test_no_binding_or_unapproved_stage_cannot_write(self):
        with self.assertRaises(ValueError):auth.issue(self.root,'session-a',self.intent,self.key)
        sdd.initialize(self.root,self.inputs['spec'])
        with self.assertRaises(ValueError):self.bind(approved=True)
        self.assertEqual((self.root/'value.py').read_text(),'VALUE=1\n')

    def test_explicit_binding_limits_session_and_files_and_revokes_changed_state(self):
        self.ready()
        with self.assertRaises(ValueError):self.bind()
        self.bind(approved=True)
        with self.assertRaises(ValueError):auth.issue(self.root,'session-b',self.intent,self.key)
        with self.assertRaises(ValueError):auth.issue(self.root,'session-a',dict(path='other.py',content='x'),self.key)
        token=auth.issue(self.root,'session-a',self.intent,self.key)
        path=self.root/'aikya/docs/specs/development/SPEC-001/state.json'
        data=json.loads(path.read_text());data['tasks'][0]['description']='Changed task'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):auth.apply_write(self.root,'session-a',self.intent,token,self.key)
        self.assertEqual((self.root/'value.py').read_text(),'VALUE=1\n')

    def test_signed_binding_and_grant_are_rechecked_at_effect(self):
        self.ready();self.bind(approved=True)
        token=auth.issue(self.root,'session-a',self.intent,self.key)
        auth.apply_write(self.root,'session-a',self.intent,token,self.key)
        self.assertEqual((self.root/'value.py').read_text(),'VALUE=2\n')
        path=self.root/'.aikya/pi/workflow.json'
        data=json.loads(path.read_text());data['payload']['files'].append('other.py');path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):auth.issue(self.root,'session-a',dict(path='other.py',content='x'),self.key)


if __name__=='__main__':unittest.main()
