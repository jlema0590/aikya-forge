"""Bound one selected task to persistent project accounting and unchanged run limits."""
import time
import uuid
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.language import resolve
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate,require_scope
from aikya.review.contracts import digest,encoded,identifier
from aikya.routing import pi_usage
from aikya.storage import atomic_write
from . import task_run_inputs as inputs,task_run_records as records


def _model(provider,model):
    for value in (provider,model):
        if not isinstance(value,str) or not 1<=len(value)<=160 or any(ord(c)<32 for c in value):
            raise ValueError('Explicit bounded provider/model selection required')


def preview(root,change_id,session_id,provider,model,limits=None,security=None):
    root=project_root(root);identifier(change_id);identifier(session_id);_model(provider,model)
    if records.active(root) is not None:raise ValueError('Another native task run owns this project')
    candidate,selection=inputs.current(root,change_id,session_id)
    cap=inputs.limits(limits);policy=inputs.security(security,candidate['policy']['checks']);budget=pi_usage.status(root)
    if budget['status']!='available':raise ValueError('An available known project budget is required')
    arguments=dict(change_id=change_id,session_id=session_id,provider=provider,model=model,limits=cap,security=policy)
    plan=dict(schema=1,project=identity(root),arguments=arguments,candidate=candidate['id'],base=candidate['base'],
              policy_hash=digest(candidate['policy']),selection=selection,limits=cap,security=policy,language=resolve(root),
              budget=dict(calls=budget['calls'],tokens=budget['recorded_tokens'],limits=budget['limits']))
    if len(encoded(plan))>14000:raise ValueError('Split the selected task before run confirmation')
    return plan


def start(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit bounded task-run confirmation required')
    root=project_root(root)
    fields={'schema','project','arguments','candidate','base','policy_hash','selection','limits','security','language','budget'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid task-run preview')
    def fresh():
        if preview(root,**plan['arguments'])!=plan:raise ValueError('Task-run source, selection or budget changed')
    fresh();folder=safe_file(root,records.ACTIVE).parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        fresh();authentication.key(root,create=True);now=time.time_ns();run_id=uuid.uuid4().hex
        state=dict(schema=1,project=identity(root),run_id=run_id,**{k:plan['arguments'][k] for k in ('session_id','provider','model','change_id')},
            **{k:plan[k] for k in ('candidate','base','policy_hash','selection','limits','security','language')},status='running',phase='explore',
            calls_start=plan['budget']['calls'],tokens_start=plan['budget']['tokens'],started_ns=now,updated_ns=now,
            deadline_ns=now+plan['limits']['seconds']*1_000_000_000,corrections_used=0,events=[])
        records.save(root,state)
        atomic_write(safe_file(root,records.ACTIVE),encoded(authentication.seal(root,dict(schema=1,project=identity(root),run_id=run_id)))+'\n',mode=0o600)
        return dict(status='running',run_id=run_id,phase=state['phase'],deadline_ns=str(state['deadline_ns']),limits=state['limits'])


def _usage(root,state):
    budget=pi_usage.status(root)
    calls=budget['calls']-state['calls_start'];tokens=(budget.get('recorded_tokens') or 0)-state['tokens_start']
    status='available'
    now=time.time_ns()
    if calls<0 or tokens<0:status='accounting_changed'
    elif budget['status']!='available':status=budget['status']
    elif calls>=state['limits']['calls']:status='calls_exhausted'
    elif now>state['deadline_ns']:status='deadline_exceeded'
    elif now<state['updated_ns']:status='clock_changed'
    return dict(status=status,calls_spent=calls,tokens_spent=tokens,phase=state['phase'],deadline_ns=str(state['deadline_ns']),run_id=state['run_id'])


def guard(root,run_id,session_id):
    root=project_root(root);state=records.load(root,run_id,session_id);result=_usage(root,state)
    if state['status']!='running' or records.active(root)!=run_id:return {**result,'status':'needs_host_action'}
    if result['status']!='available':return result
    completion=records.BASE+'completions/'+run_id+'.json'
    if safe_file(root,completion).exists():return {**result,'status':'uncertain_effect'}
    return {**result,'status':source_status(root,state)}


def source_status(root,state):
    try:
        source_snapshot(root,state)
    except (ValueError,OSError):return 'source_changed'
    return 'available'


def source_snapshot(root,state):
    candidate,selection=inputs.current(root,state['change_id'],state['session_id'],require_current=False)
    if (selection!=state['selection'] or digest(candidate['policy'])!=state['policy_hash']
            or candidate['base']!=state['base'] or resolve(root)!=state['language']):raise ValueError('Task run selection/policy changed')
    fresh=freeze_candidate(root,candidate['change_id'],candidate['scope'],session_id=state['session_id'],
                           policy=candidate['policy'],parent=candidate['parent'])
    require_scope(candidate,fresh,root)
    return fresh['id']


def status(root,session_id,run_id=None):
    root=project_root(root);identifier(session_id);selected=run_id or records.active(root)
    if selected is None:return dict(status='no_active_run')
    state=records.load(root,selected,session_id)
    result=guard(root,selected,session_id)
    from .task_run_reviews import current as reviewed_here
    return dict(**result,state=state['status'],change_id=state['change_id'],selection=state['selection'],limits=state['limits'],
                security=state['security'],corrections_used=state['corrections_used'],pre_checks=_pre_checks(root,state),completion_ready=reviewed_here(root,state))


def advance(root,run_id,session_id,phase):
    from .task_run_lifecycle import advance as transition
    return transition(root,run_id,session_id,phase)


def halt(root,run_id,session_id,reason):
    from .task_run_lifecycle import halt as transition
    return transition(root,run_id,session_id,reason)


def resume_preview(root,run_id,session_id,provider,model):
    from .task_run_lifecycle import resume_preview as transition
    return transition(root,run_id,session_id,provider,model)


def resume(root,plan,approved=False):
    from .task_run_lifecycle import resume as transition
    return transition(root,plan,approved)


def correct(root,run_id,session_id):
    from .task_run_lifecycle import correct as transition
    return transition(root,run_id,session_id)


def completion_preview(root,run_id,session_id):
    from .task_run_completion import preview as transition
    return transition(root,run_id,session_id)


def complete(root,plan,approved=False):
    from .task_run_completion import apply
    return apply(root,plan,approved)


def completion_recovery_preview(root,run_id,session_id):
    from .task_run_completion import recovery_preview
    return recovery_preview(root,run_id,session_id)


def recover_completion(root,plan,approved=False):
    from .task_run_completion import recover
    return recover(root,plan,approved)


def inference_guard(root,session_id,role,provider,model,review_change=None,review_candidate=None):
    """Gate every host-controlled stream, including a separate reviewer and compaction."""
    root=project_root(root);identifier(session_id);_model(provider,model)
    if role not in ('author','reviewer'):raise ValueError('Unknown inference role')
    run_id=records.active(root)
    if run_id is None:return dict(status='available')
    owner=authentication_owner(root,run_id)
    state=records.load(root,run_id,owner)
    if state['provider']!=provider or state['model']!=model:return dict(status='model_changed')
    if role=='author' and session_id!=owner:return dict(status='foreign_run')
    if role=='reviewer':
        from aikya.review.candidates import load_candidate
        if (session_id==owner or state['phase']!='review' or review_change!=state['change_id']
                or load_candidate(root,state['change_id'])['id']!=review_candidate):return dict(status='foreign_review')
    result=guard(root,run_id,owner)
    if result['status']=='available':result['task']=dict(run_id=run_id,change_id=state['change_id'],intent=state['selection']['intent'],
        files=state['selection']['files'],checks=state['selection']['checks'],security=state['security'])
    return result


def authentication_owner(root,run_id):
    from aikya.review import authentication
    from aikya.review.contracts import read_record
    value=authentication.verify(root,read_record(root,records.path(run_id),65536))
    identifier(value.get('session_id'))
    return value['session_id']



def _pre_checks(root,state):
    from aikya.review.candidates import load_candidate
    from aikya.review.controller import _lineage_ready,_qualifying_test
    from aikya.review.receipts import _read
    candidate=load_candidate(root,state['change_id']);rows=_read(root,state['change_id']);pending=[]
    for field,expected in (('tdd','failed'),('baseline','completed')):
        rule=candidate['policy'].get(field)
        if rule is None:continue
        current=any(_qualifying_test(r['payload'],candidate['id'],rule['check'],field) for r in rows)
        if not current and not _lineage_ready(root,candidate,rows,field):pending.append(dict(check=rule['check'],expected=expected))
    return pending



def remember_review(root,run_id,session_id):
    from .task_run_reviews import remember
    return remember(root,run_id,session_id)
