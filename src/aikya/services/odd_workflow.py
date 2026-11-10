"""Native ODD facade over canonical worklists and independently reviewed receipts."""
import hashlib
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.layout import index_paths
from aikya.documentation.language import resolve
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate,load_candidate,is_current
from aikya.review.controller import assess_candidate
from aikya.review.contracts import encoded,digest,dossier,identifier,read_record
from aikya.storage import atomic_write
from aikya.workflows import odd
from . import odd_binding

FIELDS={'create':{'feature_id','input_data'},'bind':{'feature_id','task_id'},'release':set(),
        'complete':{'feature_id','task_id','change_id'},'reconcile':{'feature_id','revision'}}


def _creation(root,args):
    root,doc,state=odd.paths(root,args['feature_id']);raw=args['input_data']
    if not isinstance(raw,dict):raise ValueError('Explicit ODD input required')
    classification=odd.classify_work(raw.get('facts',{}))
    if classification['size']=='substantial':
        data=odd.normalized(root,raw)
        if len(data['tasks'])>20:raise ValueError('Split substantial work into bounded features')
        if doc.exists() or state.exists():raise ValueError('Existing feature is preserved; resume it')
    return classification


def _proof(root,args,session):
    value,version=odd_binding.current(root,session)
    if value['feature_id']!=args['feature_id'] or value['task_id']!=args['task_id']:
        raise ValueError('Select this current task before completion')
    data,selected,intent=odd_binding.task(root,args['feature_id'],args['task_id'])
    candidate=load_candidate(root,args['change_id']);assessment=assess_candidate(root,args['change_id'])
    if (candidate['session_id']!=session or candidate['scope']!=value['files']
            or candidate['policy'].get('workflow_revision')!=version or assessment['status']!='reviewed'
            or not assessment['can_close'] or set(candidate['policy']['checks'])!=set(value['checks'])):
        raise ValueError('Current selected-task checks and independent acceptance are required')
    from .checks import bound_intent
    actual=bound_intent(root,candidate)
    if actual['objective']!=intent['objective'] or actual['acceptance']!=intent['acceptance']:
        raise ValueError('Reviewed intent does not match this ODD task')
    evidence=dossier(args['change_id'])+'/review.md'
    before=hashlib.sha256(read_source(root,evidence,65536)).hexdigest()
    record='.aikya/pi/odd-completions/'+args['feature_id']+'/'+args['task_id']+'-'+str(data['revision'])+'.json'
    if safe_file(root,record).exists():raise ValueError('Completion identity exists; reconcile without replay')
    return dict(candidate=candidate['id'],workflow_revision=version,revision=data['revision'],intent=intent,
                evidence=evidence,evidence_hash=before,record=record)


def preview(root,action,arguments,session_id):
    root=project_root(root);identifier(session_id);profile=odd.authorize(root)
    selection=odd_binding.existing(root)
    if action not in FIELDS or not isinstance(arguments,dict) or set(arguments)!=FIELDS[action] or len(encoded(arguments))>12000:
        raise ValueError('Invalid bounded ODD transition')
    index_paths(root);language=resolve(root)
    detail={}
    if action=='create':
        classification=_creation(root,arguments)
        _,doc,state=odd.paths(root,arguments['feature_id'])
        paths=[doc.relative_to(root).as_posix(),state.relative_to(root).as_posix(),'aikya/docs/indice.md'] if classification['size']=='substantial' else []
        detail=dict(classification=classification,paths=paths)
    elif action=='bind':
        data,selected,intent=odd_binding.task(root,arguments['feature_id'],arguments['task_id'])
        odd_binding.existing(root)
        detail=dict(revision=data['revision'],files=sorted(selected['files']),checks=selected['checks'],intent=intent)
    elif action=='release':
        old=odd_binding.existing(root)
        if old is None:raise ValueError('No native ODD selection to release')
        detail=dict(binding_hash=digest(old),previous=authentication.verify(root,old))
    elif action=='complete':detail=_proof(root,arguments,session_id)
    else:
        data=odd.load(root,arguments['feature_id'],verify_outcomes=False)
        if type(arguments['revision']) is not int or data['revision']!=arguments['revision']:raise ValueError('ODD revision changed')
        detail=dict(revision=data['revision'])
    source=freeze_candidate(root,'pi-odd-workflow',['aikya/docs/overview.md'],session_id=session_id)['id']
    plan=dict(schema=1,project=identity(root),action=action,arguments=arguments,session_id=session_id,
              source_revision=source,language=language,detail=detail,profile_hash=digest(profile),
              selection_before=digest(selection) if selection is not None else None)
    if len(encoded(plan))>14000:raise ValueError('ODD preview exceeds the host request bound')
    return plan


def _recorded_matches(root,args,proof,candidate,selected):
    try:
        fresh=freeze_candidate(root,candidate['change_id'],candidate['scope'],session_id=candidate['session_id'],
                               policy=candidate['policy'],parent=candidate['parent'])
        changed={p for p in candidate['files'].keys()|fresh['files'].keys() if candidate['files'].get(p)!=fresh['files'].get(p)}
        own='aikya/docs/features/'+args['feature_id']+'/'
        if changed-{own+'spec.md',own+'state.json'} or fresh['base']!=candidate['base']:return False
        if any(selected['file_fingerprints'].get(p)!=candidate['files'].get(p) for p in candidate['scope']):return False
        expected=proof['evidence_hash']
        return selected['fingerprints'].get(proof['evidence'])==expected and odd.digest(odd.relative(root,proof['evidence']))==expected
    except (ValueError,OSError):return False


def _complete(root,plan):
    args=plan['arguments'];proof=plan['detail'];candidate=load_candidate(root,args['change_id'])
    path=safe_file(root,proof['record']);authentication.key(root,create=True)
    pending=dict(schema=1,project=identity(root),feature_id=args['feature_id'],task_id=args['task_id'],
                 candidate=proof['candidate'],workflow_revision=proof['workflow_revision'],status='pending')
    atomic_write(path,encoded(authentication.seal(root,pending))+'\n',mode=0o600)
    if not is_current(root,candidate):raise ValueError('Source changed before task recording; inspect pending completion')
    result=odd.advance_task(root,args['feature_id'],args['task_id'],'done',[proof['evidence']],proof['revision'])
    selected=next(t for t in result['tasks'] if t['id']==args['task_id'])
    if not _recorded_matches(root,args,proof,candidate,selected):
        try:odd.advance_task(root,args['feature_id'],args['task_id'],'blocked',[],result['revision'])
        except ValueError:odd.reconcile_feature(root,args['feature_id'],result['revision'],approved=True)
        raise ValueError('Task source or review changed while recording; inspect pending completion')
    committed={**pending,'status':'recorded','task_hash':digest(selected),'state_hash':digest(odd.load(root,args['feature_id'])),'revision':result['revision']}
    atomic_write(path,encoded(authentication.seal(root,committed))+'\n',mode=0o600)
    return dict(status='task_recorded',feature_id=args['feature_id'],task_id=args['task_id'],revision=result['revision'],
                evidence=proof['evidence'],review='accepted_at_recording',delivery_authorized=False)


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit ODD transition confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','action','arguments','session_id','source_revision','language','detail','profile_hash','selection_before'}:
        raise ValueError('Invalid ODD preview')
    def fresh():
        if preview(root,plan['action'],plan['arguments'],plan['session_id'])!=plan:raise ValueError('ODD preview is stale')
    fresh();folder=safe_file(root,'.aikya/pi/odd-lock/.lock').parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        fresh();args=plan['arguments'];action=plan['action']
        if action=='create':
            result=odd.prepare_feature(root,args['feature_id'],args['input_data'],approved=True)
            if result.get('tracking')=='request':return result
            return dict(status='feature_prepared',feature_id=args['feature_id'],revision=result['revision'],
                        tasks=len(result['tasks']),delivery_authorized=False)
        if action=='bind':return odd_binding.bind(root,plan['session_id'],**args,approved=True)
        if action=='release':
            safe_file(root,odd_binding.PATH).unlink()
            return dict(status='task_released')
        if action=='complete':return _complete(root,plan)
        result=odd.reconcile_feature(root,args['feature_id'],args['revision'],approved=True)
        return dict(status='outcomes_reconciled',revision=result['revision'],delivery_authorized=False)


def status(root,feature_id,offset=0):
    root=project_root(root)
    if type(offset) is not int or not 0<=offset<=100:raise ValueError('Invalid ODD task offset')
    data=odd.load(root,feature_id)
    tasks=[dict(id=t['id'],status=t['status'],depends_on=t['depends_on']) for t in data['tasks']]
    return dict(feature_id=feature_id,revision=data['revision'],tasks=tasks[offset:offset+20],
                next_offset=offset+20 if offset+20<len(tasks) else None,recorded_only=True,delivery_authorized=False)
