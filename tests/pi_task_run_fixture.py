"""Disposable canonical ODD/SDD tasks and actual local regression evidence."""
import sys
from aikya.installation import portable
from aikya.services import checks,odd_workflow,task_binding
from aikya.workflows.sdd import engine
from aikya.routing import pi_usage


def prepare(root,methodology='odd',session='author'):
    profile=dict(backend='python',methodology=methodology,repository_layout='singlerepo',mode='new')
    portable.apply(root,portable.preview(root,profile,language='en'),approved=True)
    (root/'value.py').write_text('VALUE=0\n')
    (root/'test.py').write_text('from pathlib import Path\nok="VALUE=1" in Path("value.py").read_text()\nprint("TAP version 13\\n1..1")\nprint(("ok" if ok else "not ok")+" 1 - value")\nraise SystemExit(0 if ok else 1)\n')
    if methodology=='odd':
        raw=dict(title='Expected value',objective='Return the expected value',acceptance=['The value is one'],
            facts=dict(understood=False,contained_risk=True,resumable_from_request_diff=True),tasks=[dict(id='TASK-001',
            description='Return one',acceptance=['AC-01'],depends_on=[],files=['value.py','test.py'],checks=['tests'])])
        plan=odd_workflow.preview(root,'create',dict(feature_id='expected-value',input_data=raw),session_id=session)
        odd_workflow.apply(root,plan,approved=True)
        plan=odd_workflow.preview(root,'bind',dict(feature_id='expected-value',task_id='TASK-001'),session_id=session)
        bound=odd_workflow.apply(root,plan,approved=True)
    else:
        engine.initialize(root,dict(id='SPEC-001',title='Expected value',objective='Return the expected value',requirements=[
            dict(id='REQ-001',description='Return one',acceptance=['The value is one'])],questions=[]))
        engine.approve(root,'SPEC-001','spec','owner')
        engine.create_plan(root,'SPEC-001',dict(design='One local value module',decisions=['Preserve the public interface'],
            risks=['Verify current local source'],testing='Run the local regression'))
        engine.approve(root,'SPEC-001','plan','owner')
        engine.create_tasks(root,'SPEC-001',dict(tasks=[dict(id='TASK-001',description='Return one',requirements=['REQ-001'],depends_on=[])]))
        engine.approve(root,'SPEC-001','tasks','owner')
        bound=task_binding.bind(root,session,'SPEC-001','TASK-001',['value.py','test.py'],approved=True)
    definition=dict(name='tests',argv=[sys.executable,'-I','-B','test.py'],cwd='.',report_format='tap',timeout_seconds=3,max_output_bytes=65536)
    args=dict(change_id='task-proof',scope=['value.py','test.py'],session_id=session,objective='Return one',
        acceptance=['The value is one'],tdd_paths=['test.py'],definitions=[definition])
    checks.apply_snapshot(root,checks.preview_snapshot(root,**args),approved=True)
    pi_usage.configure(root,tokens=1000,calls=20,approved=True)
    return bound


def reviewed(root,decision='accept'):
    from aikya.review import admission
    from aikya.review.candidates import load_candidate
    red=checks.execute_iteration(root,checks.iteration_preview(root,'task-proof','tests','author','red'),approved=True)
    assert red['status']=='failed',red
    (root/'value.py').write_text('VALUE=1\n')
    green=checks.execute_iteration(root,checks.iteration_preview(root,'task-proof','tests','author','green'),approved=True)
    assert green['assessment']['status']=='review_required',green
    candidate=load_candidate(root,'task-proof');ticket=admission.request_review(root,'task-proof','reviewer',approved=True)
    pi_usage.admit(root,'review-fixture',dict(session='reviewer',role='reviewer',phase='review',provider='fixture',model='fixture',
        candidate=candidate['id'],change_id='task-proof'))
    pi_usage.record(root,'review-fixture',dict(input=10,output=2,cacheRead=0,cacheWrite=0))
    findings=[] if decision=='accept' else [dict(path='value.py',line=1,severity='low',summary='Preserve the public constant interface.')]
    admission.admit_review(root,'task-proof',ticket,dict(call_id='review-fixture',decision=decision,findings=findings))
    return candidate
