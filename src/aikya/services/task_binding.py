"""Host-selected SDD task scope; historical stage approvals are not a write grant."""
import re
import uuid
from aikya.code_index.policy import project_root, read_source
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.review import authentication
from aikya.review.contracts import identifier, digest, encoded, parse
from aikya.storage import atomic_write
from aikya.workflows.sdd import engine

PATH='.aikya/pi/workflow.json'


def _state(root, spec_id, task_id):
    task=engine.require_approved_task(root,spec_id,task_id)
    if task['status']=='done':raise ValueError('Completed tasks require a new reviewed task')
    folder,data=engine.load(root,spec_id)
    return digest(data)


def intent(root,spec_id,task_id):
    selected=engine.require_approved_task(root,spec_id,task_id)
    _,data=engine.load(root,spec_id);requirements={r['id']:r for r in data['spec']['requirements']}
    criteria=[criterion for ref in selected['requirements'] for criterion in requirements[ref]['acceptance']]
    value=dict(objective=selected['description'],acceptance=criteria)
    if len(value['objective'])>1000 or not 1<=len(criteria)<=10 or any(len(c)>300 for c in criteria):
        raise ValueError('Split SDD task intent before bounded native execution/review')
    return value


def bind(root,session,spec_id,task_id,files,approved=False,mobile_scope=None):
    root=project_root(root);identifier(session)
    if approved is not True:raise ValueError('Explicit task-scope confirmation required')
    if not isinstance(files,list) or not 1<=len(files)<=20 or len(set(files))!=len(files):
        raise ValueError('Explicit unique file scope required')
    from aikya.code_index.policy import excluded
    for path in files:
        safe_file(root,path,write=True)
        if excluded(path):raise ValueError('Protected task path')
    state=_state(root,spec_id,task_id);selected_intent=intent(root,spec_id,task_id)
    payload=dict(schema=1,project=str(root),session=session,spec_id=spec_id,task_id=task_id,
                 files=sorted(files),state=state,nonce=uuid.uuid4().hex)
    if mobile_scope is not None:
        from aikya.workflows.mobile_scope import validated
        from .documentation_inputs import profile
        payload['mobile_scope']=validated(profile(root),mobile_scope)
    authentication.key(root,create=True)
    path=safe_file(root,PATH);path.parent.mkdir(parents=True,exist_ok=True)
    with locked(path.parent):atomic_write(path,encoded(authentication.seal(root,payload))+'\n',mode=0o600)
    return dict(status='task_bound',intent=selected_intent,**payload)


def current(root,session):
    root=project_root(root);identifier(session)
    try:raw=parse(read_source(root,PATH,16384))
    except OSError as exc:raise ValueError('A current host-selected SDD task is required') from exc
    value=authentication.verify(root,raw)
    fields={'schema','project','session','spec_id','task_id','files','state'}
    if (not isinstance(value,dict) or not fields<=set(value) or set(value)-fields-{'nonce','mobile_scope'}
            or value['schema']!=1 or value['project']!=str(root) or value['session']!=session
            or not isinstance(value['files'],list) or not 1<=len(value['files'])<=20
            or any(not isinstance(p,str) for p in value['files']) or len(set(value['files']))!=len(value['files'])):
        raise ValueError('Current signed SDD selection and original author required')
    if 'nonce' in value and (not isinstance(value['nonce'],str) or not re.fullmatch('[a-f0-9]{32}',value['nonce'])):
        raise ValueError('Invalid SDD selection identity')
    if 'mobile_scope' in value:
        from aikya.workflows.mobile_scope import validated
        from .documentation_inputs import profile
        validated(profile(root),value['mobile_scope'])
    if value['state']!=_state(root,value['spec_id'],value['task_id']):raise ValueError('SDD task selection changed')
    return value,digest(raw)


def revision(root,path,session=None):
    from .bridge import profile_status
    profile=profile_status(root)
    if profile['methodology']=='odd':
        from .odd_binding import revision as odd_revision
        return odd_revision(root,path,session)
    if profile['methodology']!='sdd':return None
    value,version=current(root,session)
    if path not in value['files']:
        raise ValueError('SDD requires a current task and session-bound file scope')
    return version


def candidate_revision(root,scope,session):
    versions={revision(root,path,session) for path in scope}
    if versions=={None}:return None
    if len(versions)!=1 or None in versions:raise ValueError('Candidate must stay inside one current task binding')
    return versions.pop()
