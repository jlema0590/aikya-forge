"""Host phase checkpoints, stopped-run resumption and one evidence-bound correction."""
import time
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.review import authentication
from aikya.review.candidates import load_candidate
from aikya.review.controller import assess_candidate
from aikya.review.contracts import digest,encoded,dossier,read_record
from aikya.storage import atomic_write
from . import task_runs as runs,task_run_records as records

PHASES=('explore','plan','implement','validate','security','review')
REASONS=('user_stop','declined','needs_host_action','unknown_usage','checks_failed','review_failed',
         'timeout','source_changed','uncertain_effect','limit_exceeded','completed_model_turn')


def _folder(root):return safe_file(root,records.ACTIVE).parent


def _owned(root,run_id,session_id):
    state=records.load(root,run_id,session_id)
    if state['status']!='running' or records.active(root)!=run_id:raise ValueError('A current running author-owned task is required')
    return state


def _event(state,kind,**detail):
    if len(state['events'])>=64:raise ValueError('Task event bound exhausted; preserve the checkpoint')
    now=time.time_ns()
    if now<state['updated_ns']:raise ValueError('Task checkpoint clock moved backwards')
    state['updated_ns']=now;state['events'].append(dict(event=kind,phase=state['phase'],at_ns=now,**detail))


def advance(root,run_id,session_id,phase):
    root=project_root(root)
    if phase not in PHASES:raise ValueError('Choose an English engineering phase')
    with locked(_folder(root)):
        state=_owned(root,run_id,session_id)
        if runs.source_status(root,state)!='available':raise ValueError('Task source or selection changed')
        if state['phase']!=phase:
            state['phase']=phase;_event(state,'phase_selected');records.save(root,state)
    return dict(status='phase_selected',phase=phase,run_id=run_id,execution_attested=False)


def halt(root,run_id,session_id,reason):
    root=project_root(root)
    if reason not in REASONS:raise ValueError('Unknown task stopping reason')
    with locked(_folder(root)):
        state=records.load(root,run_id,session_id)
        if state['status']=='recorded':return dict(status='recorded',run_id=run_id)
        if state['status']!='stopped':
            state['status']='stopped';_event(state,'stopped',reason=reason);records.save(root,state)
        pending=safe_file(root,records.BASE+'completions/'+run_id+'.json').exists()
        if records.active(root)==run_id and not pending:safe_file(root,records.ACTIVE).unlink()
    return dict(status='stopped',run_id=run_id,reason=reason,delivery_authorized=False)


def resume_preview(root,run_id,session_id,provider,model):
    root=project_root(root);state=records.load(root,run_id,session_id)
    if state['status']!='stopped' or records.active(root) not in (None,run_id):raise ValueError('A stopped run without another owner is required')
    if provider!=state['provider'] or model!=state['model']:raise ValueError('Resume the original provider/model policy')
    if safe_file(root,records.BASE+'completions/'+run_id+'.json').exists():raise ValueError('Reconcile uncertain task completion without replay')
    from .task_run_reviews import current as reviewed_here
    local_completion=reviewed_here(root,state)
    now=time.time_ns()
    if now>state['deadline_ns'] or now<state['updated_ns']:raise ValueError('Original run clock/deadline cannot be renewed')
    result=runs._usage(root,state)
    if result['status']!='available' and not (local_completion and result['status'] in ('exhausted','calls_exhausted')):
        raise ValueError('Original run caps, source and known accounting are required; no limits are reset')
    source_revision=runs.source_snapshot(root,state)
    candidate=load_candidate(root,state['change_id'])
    return dict(schema=1,project=identity(root),run_id=run_id,session_id=session_id,provider=provider,model=model,
        state_hash=digest(state),candidate=candidate['id'],calls_spent=result['calls_spent'],
        tokens_spent=result['tokens_spent'],deadline_ns=str(state['deadline_ns']),source_revision=source_revision,
        continuation='record_completion' if local_completion else 'author')


def resume(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native run resumption confirmation required')
    root=project_root(root)
    fields={'schema','project','run_id','session_id','provider','model','state_hash','candidate','calls_spent','tokens_spent','deadline_ns','source_revision','continuation'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid run resumption preview')
    def fresh():
        if resume_preview(root,plan['run_id'],plan['session_id'],plan['provider'],plan['model'])!=plan:
            raise ValueError('Run checkpoint changed before resumption')
    fresh()
    with locked(_folder(root)):
        fresh();state=records.load(root,plan['run_id'],plan['session_id']);state['status']='running'
        _event(state,'resumed');records.save(root,state)
        atomic_write(safe_file(root,records.ACTIVE),encoded(authentication.seal(root,dict(schema=1,project=identity(root),run_id=plan['run_id'])))+'\n',mode=0o600)
    return dict(status='running',run_id=plan['run_id'],phase=state['phase'],deadline_ns=str(state['deadline_ns']),limits=state['limits'])


def correct(root,run_id,session_id):
    root=project_root(root)
    with locked(_folder(root)):
        state=_owned(root,run_id,session_id)
        if (state['phase']!='review' or runs.guard(root,run_id,session_id)['status']!='available'
                or state['corrections_used']>=state['limits']['corrections']):raise ValueError('No correction remains under this current run policy')
        candidate=load_candidate(root,state['change_id']);assessment=assess_candidate(root,state['change_id'])
        if assessment['status']!='changes_requested':raise ValueError('Current independent changes_requested evidence required')
        record=read_record(root,dossier(state['change_id'])+'/review.json',65536);value=authentication.verify(root,record)
        findings=value['event']['findings']
        if not findings or len(encoded(findings))>5000 or any(f['path'] not in candidate['scope'] for f in findings):
            raise ValueError('Correction requires bounded actionable findings within the source scope')
        state['corrections_used']+=1;state['phase']='implement'
        _event(state,'correction_reserved',candidate=candidate['id'],review_hash=digest(record));records.save(root,state)
    return dict(status='correction_ready',run_id=run_id,findings=findings,corrections_used=state['corrections_used'])
