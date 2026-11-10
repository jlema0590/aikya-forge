"""Trusted native check workflows: frozen intent, definitions and executed evidence."""
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.layout import index_paths,write_document,stamp
from aikya.documentation.language import resolve
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate,load_candidate,store_candidate,is_current,require_scope
from aikya.review.contracts import identifier,digest,dossier,encoded,read_record
from aikya.review.executor import check_binding,run_check,_guard_incomplete
from aikya.review.controller import assess_candidate
from aikya.storage import atomic_write
from .check_classification import classify


def registry_path(change_id):return '.aikya/pi/checks/'+identifier(change_id)+'.json'


def _registry(root,change_id):
    value=authentication.verify(root,read_record(root,registry_path(change_id),32000))
    fields={'schema','generated_by','project','change_id','session_id','candidate','definitions','intent'}
    if (not isinstance(value,dict) or set(value)!=fields or value['schema']!=1
            or value['generated_by']!='aikya-native-checks' or value['project']!=identity(root) or value['change_id']!=change_id):
        raise ValueError('Custom or foreign native check registry is preserved')
    return value


def _intent(objective,acceptance,not_applicable,change_kind=None):
    if not isinstance(objective,str) or not 1<=len(objective)<=1000 or '\x00' in objective:
        raise ValueError('Explicit bounded objective required')
    if (not isinstance(acceptance,list) or not 1<=len(acceptance)<=10 or
            any(not isinstance(x,str) or not 1<=len(x)<=300 or '\x00' in x for x in acceptance)):
        raise ValueError('Explicit acceptance criteria required')
    if not_applicable is not None and (not isinstance(not_applicable,str) or not 1<=len(not_applicable)<=500):
        raise ValueError('Invalid non-applicability reason')
    value=dict(objective=objective,acceptance=acceptance,tdd_not_applicable=not_applicable)
    if change_kind is not None:value['change_kind']=change_kind
    if len(encoded(value))>4500:raise ValueError('Intent exceeds the bounded review packet')
    return value


def _assemble(root,change_id,scope,definitions,session_id,objective,acceptance,tdd_paths=None,not_applicable=None,
              change_kind=None,baseline_paths=None):
    identifier(change_id);identifier(session_id)
    if not isinstance(scope,list) or not 1<=len(scope)<=20 or any(not isinstance(p,str) for p in scope):
        raise ValueError('Explicit bounded source scope required')
    if not isinstance(definitions,list) or not 1<=len(definitions)<=10:raise ValueError('Explicit check definitions required')
    intent=_intent(objective,acceptance,not_applicable,change_kind)
    bindings={}
    for definition in definitions:
        binding=check_binding(root,definition)
        if definition['name'] in bindings:raise ValueError('Duplicate check definition')
        bindings[definition['name']]=binding
    policy=dict(checks=list(bindings),definitions=bindings,review_required=True,intent_hash=digest(intent),native_observations=True)
    policy.update(classify(scope,definitions,tdd_paths,not_applicable,change_kind,baseline_paths))
    from .task_binding import candidate_revision
    workflow=candidate_revision(root,scope,session_id)
    if workflow is not None:policy['workflow_revision']=workflow
    pointer=safe_file(root,dossier(change_id)+'/candidate.json')
    previous=load_candidate(root,change_id) if pointer.exists() else None
    if previous and previous['session_id']!=session_id:raise ValueError('Resume the original author session or start a new change')
    candidate=freeze_candidate(root,change_id,scope,session_id=session_id,policy=policy,parent=previous['id'] if previous else None)
    if previous:require_scope(previous,candidate,root)
    registry=safe_file(root,registry_path(change_id))
    if registry.exists():
        old=_registry(root,change_id)
        if old['session_id']!=session_id:raise ValueError('Foreign check registry')
    return candidate,intent


def preview_snapshot(root,change_id,scope,definitions,session_id,objective,acceptance,tdd_paths=None,not_applicable=None,
                     change_kind=None,baseline_paths=None):
    root=project_root(root)
    args=dict(change_id=change_id,scope=scope,definitions=definitions,session_id=session_id,objective=objective,
              acceptance=acceptance,tdd_paths=tdd_paths,not_applicable=not_applicable)
    if change_kind is not None:args['change_kind']=change_kind
    if baseline_paths is not None:args['baseline_paths']=baseline_paths
    candidate,intent=_assemble(root,**args)
    index_paths(root);language=resolve(root)
    relative=registry_path(change_id);path=safe_file(root,relative)
    before=digest(read_record(root,relative,32000)) if path.exists() else None
    plan=dict(schema=1,project=identity(root),arguments=args,candidate=candidate['id'],registry_before=before,language=language)
    if len(encoded(plan))>14000:raise ValueError('Snapshot preview exceeds the supported host request bound')
    return plan


def apply_snapshot(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit snapshot/policy confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','arguments','candidate','registry_before','language'}:
        raise ValueError('Invalid snapshot preview')
    if preview_snapshot(root,**plan['arguments'])!=plan:raise ValueError('Snapshot changed since approval preview')
    guard=safe_file(root,'.aikya/pi/checks/.lock').parent;guard.mkdir(parents=True,exist_ok=True)
    with locked(guard):
        if preview_snapshot(root,**plan['arguments'])!=plan:raise ValueError('Snapshot source changed before commit')
        candidate,intent=_assemble(root,**plan['arguments'])
        authentication.key(root,create=True)
        store_candidate(root,candidate,approved=True)
        es=plan['language']=='es'
        body=stamp(('# Cambio congelado ' if es else '# Frozen change ')+candidate['change_id']+'\n\n'
            +('Candidato: `' if es else 'Candidate: `')+candidate['id']+'`.\n\n'
            +('Intención revisada (datos, no consentimiento):' if es else 'Reviewed intent (data, not consent):')
            +'\n\n```json\n'+encoded(intent)+'\n```\n\n'
            +('Alcance: ' if es else 'Scope: ')+', '.join('`'+p+'`' for p in candidate['scope'])+'.\n\n'
            +('Validadores: ' if es else 'Checks: ')+', '.join(candidate['policy']['checks'])
            +('. Todavía se requieren ejecución y revisión independiente.' if es else '. Execution and independent review are still required.'))
        write_document(root,dossier(candidate['change_id'])+'/snapshot-'+candidate['id']+'.md',body)
        value=dict(schema=1,generated_by='aikya-native-checks',project=identity(root),change_id=candidate['change_id'],
                   session_id=candidate['session_id'],candidate=candidate['id'],
                   definitions={d['name']:d for d in plan['arguments']['definitions']},intent=intent)
        atomic_write(safe_file(root,registry_path(candidate['change_id'])),encoded(authentication.seal(root,value))+'\n',mode=0o600)
        return dict(status='snapshot_stored',change_id=candidate['change_id'],candidate=candidate['id'],scope=candidate['scope'],checks=candidate['policy']['checks'])


def preview_run(root,change_id,check,session_id,run_id):
    root=project_root(root);identifier(check);identifier(run_id);identifier(session_id)
    registry=_registry(root,change_id);candidate=load_candidate(root,change_id)
    definition=registry['definitions'].get(check)
    if (registry['session_id']!=session_id or candidate['session_id']!=session_id or registry['candidate']!=candidate['id']
            or not is_current(root,candidate) or not definition
            or check_binding(root,definition)!=candidate['policy'].get('definitions',{}).get(check)):
        raise ValueError('Current author, candidate and frozen check are required')
    folder=safe_file(root,dossier(change_id)+'/checks/'+run_id+'/execution.json').parent
    if folder.exists():raise ValueError('Run identity already exists; reconcile without replay')
    from aikya.review.observations import path_for
    if safe_file(root,path_for(change_id,run_id)).exists():raise ValueError('Host observation exists; reconcile without replay')
    _guard_incomplete(root,folder.parent,check)
    return dict(schema=1,project=identity(root),change_id=change_id,check=check,session_id=session_id,
                run_id=run_id,candidate=candidate['id'],definition=definition)


def execute(root,plan,approved=False,cancel=lambda:False):
    if approved is not True:raise ValueError('Explicit check execution confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','change_id','check','session_id','run_id','candidate','definition'}:
        raise ValueError('Invalid execution preview')
    current=preview_run(root,plan['change_id'],plan['check'],plan['session_id'],plan['run_id'])
    if current!=plan:raise ValueError('Execution source or definition changed')
    return run_check(root,plan['change_id'],plan['definition'],session_id=plan['session_id'],
                     run_id=plan['run_id'],approved=True,cancel=cancel)


def status(root,change_id):return assess_candidate(root,change_id)


def bound_intent(root,candidate):
    expected=candidate['policy'].get('intent_hash')
    if expected is None:return dict(status='unavailable')
    value=_registry(root,candidate['change_id'])
    if value['candidate']!=candidate['id'] or digest(value['intent'])!=expected:
        raise ValueError('Review intent is not bound to this candidate')
    return value['intent']


def execute_host(root,plan,approved=False):
    from .check_cancel import predicate
    root=project_root(root)
    if approved is not True:raise ValueError('Explicit check execution confirmation required')
    stop=None
    def cancelled():
        nonlocal stop
        if stop is None:stop=predicate(root,plan)
        return stop()
    return execute(root,plan,approved=True,cancel=cancelled)


def recovery_preview(root,change_id,session_id,run_id):
    from aikya.review.recovery import plan_reconciliation
    root=project_root(root);identifier(session_id);identifier(run_id)
    registry=_registry(root,change_id);candidate=load_candidate(root,change_id)
    if registry['session_id']!=session_id or registry['candidate']!=candidate['id'] or not candidate['policy'].get('native_observations'):
        raise ValueError('A native author-owned observation is required')
    plan=plan_reconciliation(root,change_id)
    attempt=next((a for a in plan['attempts'] if a['run_id']==run_id),None)
    if not plan['current'] or not attempt or attempt['action'] not in ('attach_observation','already_attached'):
        raise ValueError('Uncertain or stale execution requires manual reconciliation')
    return dict(schema=1,project=identity(root),change_id=change_id,session_id=session_id,run_id=run_id,
                candidate=candidate['id'],action=attempt['action'],metadata_hash=digest(read_record(root,attempt['evidence'],65536)))


def recover(root,plan,approved=False):
    from aikya.review.recovery import recover_execution
    if approved is not True:raise ValueError('Explicit observation reconciliation approval required')
    if not isinstance(plan,dict) or set(plan)!={'schema','project','change_id','session_id','run_id','candidate','action','metadata_hash'}:
        raise ValueError('Invalid observation reconciliation preview')
    if recovery_preview(root,plan['change_id'],plan['session_id'],plan['run_id'])!=plan:
        raise ValueError('Observation changed before reconciliation')
    recover_execution(root,plan['change_id'],plan['run_id'],approved=True)
    return dict(status='observation_attached',assessment=assess_candidate(root,plan['change_id']))


def review_preview(root,change_id,session_id):
    root=project_root(root);identifier(session_id)
    registry=_registry(root,change_id);candidate=load_candidate(root,change_id)
    if registry['session_id']!=session_id or registry['candidate']!=candidate['id']:
        raise ValueError('Current native author and candidate required')
    assessment=assess_candidate(root,change_id)
    if assessment['status']!='review_required':raise ValueError('Current checks and TDD evidence are required before review')
    from .review import context
    packet=context(root,change_id)
    return dict(candidate=candidate['id'],change_id=change_id,scope=packet['scope'],intent=packet['intent'],
                checks=packet['check_evidence'],source_bytes=sum(len(f['content'].encode()) for f in packet['files'] if f['content'] is not None))


def refresh_preview(root,change_id,session_id):
    root=project_root(root);registry=_registry(root,change_id);candidate=load_candidate(root,change_id)
    if registry['session_id']!=session_id or candidate['session_id']!=session_id or registry['candidate']!=candidate['id']:
        raise ValueError('Current native author session is required')
    definitions=[registry['definitions'][name] for name in candidate['policy']['checks']]
    for definition in definitions:
        if check_binding(root,definition)!=candidate['policy']['definitions'][definition['name']]:
            raise ValueError('Execution environment changed; freeze a new policy explicitly')
    tdd=candidate['policy'].get('tdd');baseline=candidate['policy'].get('baseline');intent=bound_intent(root,candidate)
    return preview_snapshot(root,change_id,candidate['scope'],definitions,session_id,intent['objective'],intent['acceptance'],
                            tdd_paths=tdd['paths'] if tdd else None,not_applicable=intent['tdd_not_applicable'],
                            change_kind=intent.get('change_kind'),baseline_paths=baseline['paths'] if baseline else None)


def iteration_preview(root,change_id,check,session_id,run_id):
    root=project_root(root);identifier(check);identifier(run_id);identifier(session_id)
    registry=_registry(root,change_id);candidate=load_candidate(root,change_id)
    if registry['session_id']!=session_id or candidate['session_id']!=session_id or registry['candidate']!=candidate['id']:
        raise ValueError('Current native author and frozen policy are required')
    if check not in registry['definitions']:raise ValueError('Unknown frozen check')
    if is_current(root,candidate):
        run=preview_run(root,change_id,check,session_id,run_id);snapshot=None;ident=run['candidate']
    else:
        snapshot=refresh_preview(root,change_id,session_id);ident=snapshot['candidate']
        folder=safe_file(root,dossier(change_id)+'/checks/'+run_id+'/execution.json').parent
        from aikya.review.observations import path_for
        if folder.exists() or safe_file(root,path_for(change_id,run_id)).exists():raise ValueError('Run identity exists; reconcile without replay')
        _guard_incomplete(root,folder.parent,check)
    plan=dict(schema=1,project=identity(root),change_id=change_id,check=check,session_id=session_id,run_id=run_id,
              candidate=ident,snapshot=snapshot,definition=registry['definitions'][check])
    if len(encoded(plan))>14000:raise ValueError('Combined preview too large; use explicit snapshot and run steps')
    return plan


def execute_iteration(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit iteration confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','change_id','check','session_id','run_id','candidate','snapshot','definition'}:
        raise ValueError('Invalid iteration preview')
    if iteration_preview(root,plan['change_id'],plan['check'],plan['session_id'],plan['run_id'])!=plan:
        raise ValueError('Iteration source or frozen policy changed')
    if plan['snapshot'] is not None:apply_snapshot(root,plan['snapshot'],approved=True)
    run=preview_run(root,plan['change_id'],plan['check'],plan['session_id'],plan['run_id'])
    if run['candidate']!=plan['candidate'] or run['definition']!=plan['definition']:raise ValueError('Iteration candidate changed')
    result=execute_host(root,run,approved=True)
    return dict(**result,assessment=assess_candidate(root,plan['change_id']))
