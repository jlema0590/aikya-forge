"""Host-selected ODD task scope; a worklist is not execution evidence or consent."""
import uuid
from aikya.code_index.policy import project_root,excluded,read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.review import authentication
from aikya.review.contracts import identifier,digest,encoded,parse
from aikya.storage import atomic_write
from aikya.workflows import odd

PATH='.aikya/pi/odd-workflow.json'
FIELDS={'schema','project','session','feature_id','task_id','files','checks','intent','state','nonce'}


def task(root,feature_id,task_id):
    data=odd.load(root,feature_id)
    selected=next((t for t in data['tasks'] if t['id']==task_id),None)
    if not selected or selected['status'] not in ('todo','in_progress'):
        raise ValueError('A ready unfinished ODD task is required')
    byid={t['id']:t for t in data['tasks']}
    if any(byid[d]['status']!='done' for d in selected['depends_on']):raise ValueError('Complete ODD dependencies first')
    files=selected['files'];names=selected['checks']
    if not 1<=len(files)<=20 or not 1<=len(names)<=10:raise ValueError('Split this task before native execution')
    for path in files:
        safe_file(root,path,write=True)
        if excluded(path) or path.startswith('aikya/docs/features/'+feature_id+'/'):
            raise ValueError('Task control paths cannot certify themselves')
    for name in names:identifier(name)
    criteria={'AC-'+str(i).zfill(2):text for i,text in enumerate(data['acceptance'],1)}
    intent=dict(objective=selected['description'],acceptance=[criteria[c] for c in selected['acceptance']])
    if len(intent['objective'])>1000 or len(intent['acceptance'])>10 or any(len(x)>300 for x in intent['acceptance']):
        raise ValueError('Split task intent before bounded review')
    return data,selected,intent


def existing(root):
    path=safe_file(root,PATH)
    if not path.exists():return None
    raw=parse(read_source(root,PATH,16384));value=authentication.verify(root,raw)
    if (not isinstance(value,dict) or set(value)!=FIELDS or value['schema']!=1 or value['project']!=identity(root)
            or not isinstance(value['nonce'],str) or len(value['nonce'])!=32):
        raise ValueError('Custom or foreign task binding is preserved')
    identifier(value['session'])
    return raw


def current(root,session):
    raw=existing(root)
    if raw is None:raise ValueError('An explicit native ODD task selection is required')
    value=authentication.verify(root,raw)
    if value['session']!=session:raise ValueError('ODD task belongs to another author session')
    data,selected,intent=task(root,value['feature_id'],value['task_id'])
    if (value['state']!=digest(data) or value['files']!=sorted(selected['files'])
            or value['checks']!=selected['checks'] or value['intent']!=intent):
        raise ValueError('ODD task changed; confirm a current task selection')
    return value,digest(raw)


def revision(root,path,session):
    if existing(root) is None:return None
    value,version=current(root,session)
    if path not in value['files']:raise ValueError('Write is outside the selected ODD task')
    return version


def bind(root,session,feature_id,task_id,approved=False):
    if approved is not True:raise ValueError('Explicit ODD task-scope confirmation required')
    root=project_root(root);identifier(session);existing(root)
    data,selected,intent=task(root,feature_id,task_id)
    value=dict(schema=1,project=identity(root),session=session,feature_id=feature_id,task_id=task_id,
               files=sorted(selected['files']),checks=selected['checks'],intent=intent,state=digest(data),nonce=uuid.uuid4().hex)
    path=safe_file(root,PATH);path.parent.mkdir(parents=True,exist_ok=True)
    with locked(path.parent):
        existing(root)
        if task(root,feature_id,task_id)[0]!=data:raise ValueError('ODD task changed before binding')
        authentication.key(root,create=True);raw=authentication.seal(root,value)
        atomic_write(path,encoded(raw)+'\n',mode=0o600)
    return dict(status='task_bound',feature_id=feature_id,task_id=task_id,files=value['files'],checks=value['checks'],
                intent=intent,workflow_revision=digest(raw))
