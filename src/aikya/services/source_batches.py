"""One confirmed source batch with durable partial outcomes; no automatic rollback."""
import time
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.documentation.language import resolve
from aikya.documentation.layout import write_document,stamp
from aikya.review import authentication
from aikya.review.candidates import load_candidate,is_current,freeze_candidate
from aikya.review.contracts import digest,encoded,dossier,identifier
from aikya.review.document_transitions import digest_bytes
from aikya.storage import atomic_write
from . import authorization_tokens as tokens,batch_inputs as inputs,checks
from .task_binding import candidate_revision
from .batch_records import PENDING,OPERATIONS,RESERVATIONS,guard


def _prepare(root,intent,session):
    identifier(session)
    guard(root)
    if (not isinstance(intent,dict) or set(intent)!={'change_id','operations'}
            or len(encoded(intent).encode())>12000):raise ValueError('Bounded source batch with native change_id required')
    identifier(intent['change_id']);candidate=load_candidate(root,intent['change_id']);registry=checks._registry(root,intent['change_id'])
    if (candidate['session_id']!=session or registry['session_id']!=session or registry['candidate']!=candidate['id']
            or candidate['policy'].get('native_observations') is not True or not is_current(root,candidate)):
        raise ValueError('Current native author candidate required')
    rows,prepared=inputs.prepare(root,intent['operations'])
    if set(item['path'] for item in rows)-set(candidate['scope']):raise ValueError('Batch source is outside the frozen scope')
    workflow=candidate_revision(root,[item['path'] for item in rows],session)
    if workflow!=candidate['policy'].get('workflow_revision'):raise ValueError('Frozen task binding changed')
    language=resolve(root)
    checked=dict(candidate=candidate['id'],files=rows,intent_hash=digest(intent),workflow_revision=workflow,
        source_revision=digest(dict(candidate=candidate['id'],files=rows,language=language)),language=language,
        checks='not_run',delivery_authorized=False)
    return checked,prepared,candidate


def preview(root,intent,*,session):return _prepare(project_root(root),intent,session)[0]


def issue(root,session,intent,key,*,now=None,ttl=120):
    checked=preview(root,intent,session=session)
    return tokens.issue(root,session,checked,key,'file.batch',now=now,ttl=ttl)


def perform(root,item):
    target=inputs.destination(root,item['path'])
    current=digest_bytes(read_source(root,item['path'],1000000)) if target.exists() else None
    if current!=item['before']:raise ValueError('Concurrent destination edit; preserve pending batch')
    if item['raw'] is None:target.unlink()
    elif item['before'] is None:
        target.parent.mkdir(parents=True,exist_ok=True);inputs.destination(root,item['path'])
        from .generation import write_new
        write_new(target,item['raw'])
    else:atomic_write(target,item['raw'],mode=item['mode'])
    actual=digest_bytes(read_source(root,item['path'],1000000)) if target.exists() else None
    if actual!=item['after']:raise ValueError('Source batch readback failed; preserve pending state')


def observed(root,pending):
    candidate=load_candidate(root,pending['change_id'])
    registry=checks._registry(root,pending['change_id'])
    if (candidate['id']!=pending['candidate'] or candidate['session_id']!=pending['session']
            or registry['candidate']!=candidate['id'] or registry['session_id']!=pending['session']):
        raise ValueError('Pending batch candidate identity changed')
    expected=dict(candidate['files'])
    for item in pending['files']:
        if item['path'] not in candidate['scope'] or item['before']!=expected.get(item['path']):
            raise ValueError('Reserved source differs from the frozen candidate')
        if item['after'] is None:expected.pop(item['path'],None)
        else:expected[item['path']]=item['after']
    fresh=freeze_candidate(root,candidate['change_id'],candidate['scope'],session_id=candidate['session_id'],
                           policy=candidate['policy'],parent=candidate['parent'])
    if fresh['files']!=expected or fresh['base']!=candidate['base'] or resolve(root)!=pending['language']:
        raise ValueError('Source batch effects are partial, stale or uncertain')
    paths=[item['path'] for item in pending['files']]
    if candidate_revision(root,paths,pending['session'])!=pending['workflow_revision']:raise ValueError('Pending batch task binding changed')


def finish(root,pending):
    observed(root,pending)
    report=dossier(pending['change_id'])+'/operations/source-'+pending['nonce']+'.md'
    es=pending['language']=='es'
    body=stamp(('# Lote de cambios locales' if es else '# Local source batch')+'\n\n'
        +('Archivos observados; checks no ejecutados. No autoriza entrega.' if es else
          'Observed files; checks not run. Delivery is not authorized.')+'\n\n```json\n'+encoded(pending['files'])+'\n```')
    write_document(root,report,body)
    from .maintenance import after_write
    memory=after_write(root);observed(root,pending)
    result=dict(status='written',files=pending['files'],report=report,checks='not_run',delivery_authorized=False,memory=memory)
    value={**pending,'status':'written','result':result}
    atomic_write(safe_file(root,OPERATIONS+pending['nonce']+'.json'),encoded(authentication.seal(root,value))+'\n',mode=0o600)
    safe_file(root,RESERVATIONS+pending['nonce']+'.json').unlink(missing_ok=True)
    safe_file(root,PENDING).unlink()
    return result


def apply(root,session,intent,token,key,*,now=None):
    root=project_root(root);checked,prepared,candidate=_prepare(root,intent,session)
    data=tokens.verify(root,session,checked,token,key,'file.batch',time.time() if now is None else now)
    folder=safe_file(root,PENDING).parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        checked,prepared,candidate=_prepare(root,intent,session)
        data=tokens.verify(root,session,checked,token,key,'file.batch',time.time() if now is None else now)
        record=safe_file(root,OPERATIONS+data['nonce']+'.json')
        reservation=safe_file(root,RESERVATIONS+data['nonce']+'.json')
        if record.exists() or reservation.exists():raise ValueError('Batch grant consumed; reconcile without replay')
        files=[{k:item[k] for k in ('path','before','after','action')} for item in checked['files']]
        pending=dict(schema=1,project=identity(root),status='pending',session=session,change_id=candidate['change_id'],
                     candidate=candidate['id'],intent_hash=checked['intent_hash'],workflow_revision=checked['workflow_revision'],
                     language=checked['language'],nonce=data['nonce'],files=files)
        authentication.key(root,create=True)
        atomic_write(reservation,encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        atomic_write(safe_file(root,PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        for item in prepared:perform(root,item)
        return finish(root,pending)
