"""Finish or reconcile a run using the canonical native task receipt, never replay it."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.review import authentication
from aikya.review.admission import admitted_decision
from aikya.review.candidates import load_candidate
from aikya.review.contracts import digest,encoded,read_record
from aikya.storage import atomic_write
from aikya.workflows import odd
from aikya.workflows.sdd import engine
from . import task_runs as runs,task_run_records as records,odd_workflow,sdd_completion
from .task_run_lifecycle import _owned,_event,_folder


def path(run_id):
    records.path(run_id)
    return records.BASE+'completions/'+run_id+'.json'


def preview(root,run_id,session_id):
    root=project_root(root);state=_owned(root,run_id,session_id)
    if state['phase']!='review' or runs.source_status(root,state)!='available':raise ValueError('Current reviewed task source required')
    if safe_file(root,path(run_id)).exists():raise ValueError('Uncertain completion must be reconciled without replay')
    selected=state['selection'];method=selected['methodology']
    if method=='odd':
        args=dict(feature_id=selected['feature_id'],task_id=selected['task_id'],change_id=state['change_id'])
        inner=odd_workflow.preview(root,'complete',args,session_id=session_id)
    else:inner=sdd_completion.preview(root,selected['spec_id'],selected['task_id'],state['change_id'],session_id)
    plan=dict(schema=1,project=identity(root),run_id=run_id,session_id=session_id,state_hash=digest(state),method=method,workflow_plan=inner)
    if len(encoded(plan))>15000:raise ValueError('Task completion exceeds the bounded host plan')
    return plan


def _receipt(root,plan):
    inner=plan['workflow_plan'];method=plan['method'];proof=inner['detail'] if method=='odd' else inner['proof']
    value=authentication.verify(root,read_record(root,proof['record'],65536))
    if value.get('status')!='recorded' or value.get('project')!=identity(root):raise ValueError('Native task completion remains uncertain')
    state=records.load(root,plan['run_id'],plan['session_id']);candidate=load_candidate(root,state['change_id'])
    if candidate['id']!=proof['candidate'] or admitted_decision(root,state['change_id'],candidate)!='accept':
        raise ValueError('Recorded independent task acceptance changed')
    if method=='odd':
        args=inner['arguments'];data=odd.load(root,args['feature_id']);selected=next(t for t in data['tasks'] if t['id']==args['task_id'])
        if (value.get('feature_id')!=args['feature_id'] or value.get('task_id')!=args['task_id']
                or value.get('candidate')!=candidate['id'] or value.get('workflow_revision')!=proof['workflow_revision']
                or value.get('task_hash')!=digest(selected) or value.get('state_hash')!=digest(data)
                or not odd_workflow._recorded_matches(root,args,proof,candidate,selected)):
            raise ValueError('Recorded ODD task effects differ')
    else:
        _,data=engine.load(root,inner['spec_id'])
        if (value.get('plan')!=inner or value.get('state_hash')!=digest(data)
                or not sdd_completion._projection_matches(root,inner,candidate,data)):
            raise ValueError('Recorded SDD task effects differ')
    return dict(path=proof['record'],sha256=digest(value),candidate=candidate['id'])


def finalize(root,state,reservation,result):
    plan=reservation['plan'];receipt=_receipt(root,plan)
    if state['status']=='recorded':
        if not any(e.get('completion')==digest(plan) for e in state['events']):raise ValueError('Unknown recorded task-run outcome')
    elif digest(state)!=plan['state_hash']:raise ValueError('Run checkpoint changed while recording')
    else:
        state['status']='recorded';_event(state,'task_recorded',completion=digest(plan),receipt=receipt)
        records.save(root,state)
    complete={**reservation,'status':'recorded','result':result,'receipt':receipt}
    atomic_write(safe_file(root,path(state['run_id'])),encoded(authentication.seal(root,complete))+'\n',mode=0o600)
    if records.active(root)==state['run_id']:safe_file(root,records.ACTIVE).unlink()
    return dict(status='recorded',run_id=state['run_id'],task=result,receipt=receipt,
                usage=runs._usage(root,state),review='accepted_at_recording',delivery_authorized=False)


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit current task completion confirmation required')
    root=project_root(root)
    fields={'schema','project','run_id','session_id','state_hash','method','workflow_plan'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid task-run completion preview')
    def fresh():
        if preview(root,plan['run_id'],plan['session_id'])!=plan:raise ValueError('Task-run completion source changed')
    fresh()
    with locked(_folder(root)):
        fresh();state=records.load(root,plan['run_id'],plan['session_id'])
        reservation=dict(schema=1,project=identity(root),status='pending',plan=plan)
        atomic_write(safe_file(root,path(plan['run_id'])),encoded(authentication.seal(root,reservation))+'\n',mode=0o600)
        service=odd_workflow if plan['method']=='odd' else sdd_completion
        result=service.apply(root,plan['workflow_plan'],approved=True)
        if result.get('status')!='task_recorded':raise ValueError('Native task recording returned no known outcome')
        return finalize(root,state,reservation,result)


def recovery_preview(root,run_id,session_id):
    root=project_root(root);state=records.load(root,run_id,session_id)
    reservation=authentication.verify(root,read_record(root,path(run_id),65536))
    if (reservation.get('project')!=identity(root) or reservation.get('schema')!=1
            or reservation.get('plan',{}).get('run_id')!=run_id
            or reservation['plan'].get('session_id')!=session_id):raise ValueError('Foreign task completion is preserved')
    compatible=(digest(state)==reservation['plan'].get('state_hash') or (state['status']=='recorded'
        and any(e.get('completion')==digest(reservation['plan']) for e in state['events'])))
    if not compatible:return dict(status='manual_reconciliation',plan=None)
    try:receipt=_receipt(root,reservation['plan'])
    except (ValueError,OSError,KeyError):return dict(status='manual_reconciliation',plan=None)
    plan=dict(schema=1,project=identity(root),run_id=run_id,session_id=session_id,
              state_hash=digest(state),reservation_hash=digest(reservation),receipt=receipt)
    return dict(status='reconciliation_ready',plan=plan,review=dict(receipt=receipt,effects='record known completion without replay',delivery_authorized=False))


def recover(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit task completion reconciliation confirmation required')
    root=project_root(root)
    fields={'schema','project','run_id','session_id','state_hash','reservation_hash','receipt'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid task completion reconciliation')
    def fresh():
        if recovery_preview(root,plan['run_id'],plan['session_id']).get('plan')!=plan:raise ValueError('Recorded task outcome changed')
    fresh()
    with locked(_folder(root)):
        fresh();state=records.load(root,plan['run_id'],plan['session_id'])
        reservation=authentication.verify(root,read_record(root,path(plan['run_id']),65536))
        result=dict(status='task_recorded',reconciled=True,delivery_authorized=False)
        return finalize(root,state,reservation,result)
