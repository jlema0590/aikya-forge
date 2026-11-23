"""Record selected SDD task acceptance over canonical metadata after current native review."""
import copy
import json
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.layout import stamp,index_paths
from aikya.documentation.language import resolve
from aikya.review import authentication
from aikya.review.admission import admitted_decision
from aikya.review.candidates import load_candidate,freeze_candidate,is_current
from aikya.review.controller import assess_candidate
from aikya.review.contracts import digest,encoded,dossier,identifier
from aikya.review.document_transitions import digest_bytes
from aikya.storage import atomic_write
from aikya.workflows.sdd import engine
from . import task_binding,checks


def _proof(root,spec_id,task_id,change_id,session_id):
    value,version=task_binding.current(root,session_id)
    if value['spec_id']!=spec_id or value['task_id']!=task_id:raise ValueError('Select this current SDD task first')
    candidate=load_candidate(root,change_id);assessment=assess_candidate(root,change_id)
    if (candidate['session_id']!=session_id or candidate['scope']!=value['files']
            or candidate['policy'].get('workflow_revision')!=version or assessment['status']!='reviewed'
            or not assessment['can_close']):raise ValueError('Current selected SDD task checks and independent acceptance required')
    actual=checks.bound_intent(root,candidate);expected=task_binding.intent(root,spec_id,task_id)
    if actual['objective']!=expected['objective'] or actual['acceptance']!=expected['acceptance']:
        raise ValueError('Reviewed intent differs from the selected SDD task')
    folder,data=engine.load(root,spec_id);selected=next(t for t in data['tasks'] if t['id']==task_id)
    if selected['status']=='done':raise ValueError('Task is already recorded')
    report=dossier(change_id)+'/review.md';report_hash=digest_bytes(read_source(root,report,65536))
    record='.aikya/pi/sdd-completions/'+spec_id+'/'+task_id+'-'+version+'.json'
    if safe_file(root,record).exists():raise ValueError('Uncertain or recorded SDD completion cannot replay')
    return dict(candidate=candidate['id'],workflow_revision=version,state_hash=digest(data),
                evidence=report,evidence_hash=report_hash,record=record,intent=expected)


def preview(root,spec_id,task_id,change_id,session_id):
    root=project_root(root);identifier(session_id);identifier(change_id);identifier(spec_id);identifier(task_id)
    index_paths(root);proof=_proof(root,spec_id,task_id,change_id,session_id)
    return dict(schema=1,project=identity(root),spec_id=spec_id,task_id=task_id,change_id=change_id,
                session_id=session_id,language=resolve(root),proof=proof)


def _matches(root,plan,candidate,before):
    expected=copy.deepcopy(before);selected=next(t for t in expected['tasks'] if t['id']==plan['task_id'])
    selected['status']='done';selected['evidence']=sorted(set([*selected['evidence'],plan['proof']['evidence']]))
    expected['verification']=None
    return _projection_matches(root,plan,candidate,expected)


def _projection_matches(root,plan,candidate,expected):
    folder,actual=engine.load(root,plan['spec_id'])
    if actual!=expected:return False
    relative=folder.relative_to(root).as_posix()
    fresh=freeze_candidate(root,candidate['change_id'],candidate['scope'],session_id=candidate['session_id'],
                           policy=candidate['policy'],parent=candidate['parent'])
    changed={p for p in candidate['files'].keys()|fresh['files'].keys() if candidate['files'].get(p)!=fresh['files'].get(p)}
    allowed={relative+'/'+name for name in ('state.json','tasks.md','verification.md','evidence.md')}
    if changed-allowed or fresh['base']!=candidate['base'] or admitted_decision(root,plan['change_id'],candidate)!='accept':return False
    tasks=engine.render_tasks(expected)
    if expected.get('docs_language')=='es':
        from aikya.workflows.sdd.localization import localize_sdd
        tasks=localize_sdd(tasks)
    if read_source(root,relative+'/tasks.md',1000000).decode()!=stamp(tasks):return False
    if read_source(root,relative+'/state.json',1000000).decode()!=json.dumps(expected,indent=2,ensure_ascii=False)+'\n':return False
    from aikya.workflows.sdd.state import invalidated_verification
    for name in ('verification.md','evidence.md'):
        path=relative+'/'+name
        if path in changed and read_source(root,path,1000000).decode()!=invalidated_verification(expected):return False
    return True


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native SDD task completion confirmation required')
    root=project_root(root)
    fields={'schema','project','spec_id','task_id','change_id','session_id','language','proof'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid SDD completion preview')
    def fresh():
        if preview(root,plan['spec_id'],plan['task_id'],plan['change_id'],plan['session_id'])!=plan:
            raise ValueError('SDD completion preview changed')
    fresh();folder=safe_file(root,'.aikya/pi/sdd-completions/.lock').parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        fresh();candidate=load_candidate(root,plan['change_id']);_,before=engine.load(root,plan['spec_id'])
        pending=dict(schema=1,project=identity(root),status='pending',plan=plan)
        path=safe_file(root,plan['proof']['record']);authentication.key(root,create=True)
        atomic_write(path,encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        if not is_current(root,candidate):raise ValueError('Source changed before SDD completion; pending state preserved')
        result=engine.progress(root,plan['spec_id'],plan['task_id'],'done',plan['proof']['evidence'])
        if not _matches(root,plan,candidate,before):
            try:engine.progress(root,plan['spec_id'],plan['task_id'],'in_progress','')
            except (ValueError,OSError):pass
            raise ValueError('SDD source/evidence changed while recording; pending state preserved')
        value={**pending,'status':'recorded','state_hash':digest(engine.load(root,plan['spec_id'])[1])}
        atomic_write(path,encoded(authentication.seal(root,value))+'\n',mode=0o600)
    return dict(status='task_recorded',spec_id=plan['spec_id'],task_id=plan['task_id'],
                evidence=plan['proof']['evidence'],review='accepted_at_recording',delivery_authorized=False)
