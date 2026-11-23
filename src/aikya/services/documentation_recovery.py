"""Finish known documentary bookkeeping after readback, never replay source effects."""
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.language import resolve
from aikya.documentation.layout import update_index
from aikya.review import authentication
from aikya.review.candidates import validate,freeze_candidate,_derived_index
from aikya.review.contracts import digest,encoded,identifier,read_record
from aikya.review.document_transitions import permitted,digest_bytes,OPERATIONS
from aikya.storage import atomic_write
from . import documentation_inputs as inputs

LIMIT=2_100_000


def reservation(root,plan,state,before):
    effects=[dict(path=item['path'],before=before['files'].get(item['path']),
                  after=digest_bytes(item['after'].encode()),evidence=item.get('evidence_hashes',{}))
             for item in state['detail'].get('documents',[])]
    baseline=None
    if plan['input_data']['action']=='baseline':
        baseline=dict(path=state['detail']['path'],payload=dict(schema=1,project=identity(root),
            change_id=plan['input_data']['change_id'],session_id=plan['session_id'],sources=state['detail']['sources']))
    value=dict(schema=1,project=identity(root),status='pending',plan=plan,before=before,
               effects=effects,pages_before=state['pages'],baseline=baseline)
    if len(encoded(value))>LIMIT-200:raise ValueError('Document recovery reservation exceeds its bound')
    return value


def operation(plan,result,transition=None):
    value=dict(schema=1,project=plan['project'],status='recorded',plan=plan,result=result)
    if transition is not None:value['transition']=transition
    return value


def _observed(root,pending):
    before=validate(root,pending['before']);plan=pending['plan'];effects=pending['effects']
    if (before['id']!=plan['source_revision'] or before['session_id']!=plan['session_id']
            or not isinstance(effects,list) or len(effects)>4):raise ValueError('Invalid reserved documentary source')
    expected=dict(before['files']);pages=dict(pending['pages_before']);changes={}
    for item in effects:
        if (not isinstance(item,dict) or set(item)!={'path','before','after','evidence'} or not permitted(item['path'])
                or item['before']!=expected.get(item['path'])):raise ValueError('Invalid reserved documentary effect')
        raw=read_source(root,item['path'],12000)
        if digest_bytes(raw)!=item['after']:raise ValueError('Documentary effect is missing or differs from the reviewed bytes')
        if item['evidence'] and inputs.sources(root,list(item['evidence']),allow_docs=True)!=item['evidence']:
            raise ValueError('Document evidence changed')
        expected[item['path']]=item['after'];pages[item['path']]=item['after']
        changes[item['path']]=dict(before=item['before'],after=item['after'])
    current=freeze_candidate(root,'pi-documentation',['aikya/docs/overview.md'],session_id=plan['session_id'])
    if (current['files']!=expected or current['base']!=before['base'] or digest(inputs.profile(root))!=plan['profile_hash']
            or resolve(root)!=plan['language']):raise ValueError('Source, profile or language changed during the pending operation')
    index=safe_file(root,'aikya/docs/indice.md')
    if index.exists() and not _derived_index(read_source(root,'aikya/docs/indice.md',1000000)):
        raise ValueError('Customized document index is preserved')
    if inputs.registry(root) not in (pending['pages_before'],pages):raise ValueError('Documentation ownership changed')
    if pending['baseline'] is not None:
        baseline=pending['baseline']
        if inputs.signed(root,baseline['path'])!=baseline['payload']:raise ValueError('Baseline effect is uncertain')
    marker=None
    if plan['input_data']['action']=='sync':
        marker='.aikya/pi/documentation/completed/'+plan['input_data']['change_id']+'.json'
        if safe_file(root,marker).exists() and inputs.signed(root,marker)!=dict(schema=1,operation=digest(plan)):
            raise ValueError('Unknown completion record is preserved')
    return pages,dict(base=before['base'],changes=changes) if changes else None,marker


def _pending(root,session_id):
    value=authentication.verify(root,read_record(root,inputs.PENDING,LIMIT))
    if (not isinstance(value,dict) or value.get('schema')!=1 or value.get('project')!=identity(root)
            or value.get('status')!='pending' or not isinstance(value.get('plan'),dict)
            or value['plan'].get('session_id')!=session_id):raise ValueError('Original documentary author session is required')
    return value


def preview(root,session_id):
    root=project_root(root);identifier(session_id)
    if not safe_file(root,inputs.PENDING).exists():return dict(status='nothing_pending',plan=None)
    pending=_pending(root,session_id)
    if set(pending)!={'schema','project','status','plan','before','effects','pages_before','baseline'}:
        return dict(status='manual_reconciliation',plan=None,reason='Legacy pending state lacks a complete effect reservation')
    try:pages,transition,marker=_observed(root,pending)
    except (ValueError,OSError):
        return dict(status='manual_reconciliation',plan=None,reason='Exact effects and unchanged surrounding source cannot be established')
    record=OPERATIONS+digest(pending['plan'])+'.json'
    if safe_file(root,record).exists():
        existing=inputs.signed(root,record)
        if existing.get('plan')!=pending['plan'] or existing.get('status')!='recorded' or existing.get('transition')!=transition:
            raise ValueError('Unknown operation record is preserved')
    plan=dict(schema=1,project=identity(root),session_id=session_id,pending_hash=digest(pending),
              operation=digest(pending['plan']),effects=pending['effects'])
    return dict(status='reconciliation_ready',plan=plan,review=dict(documents=plan['effects'],
                action=pending['plan']['input_data']['action'],effects='bookkeeping only; no document replay',checks='not_run'))


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit documentation reconciliation confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','session_id','pending_hash','operation','effects'}:
        raise ValueError('Invalid documentation reconciliation preview')
    def fresh():
        if preview(root,plan['session_id']).get('plan')!=plan:raise ValueError('Pending documentation changed before reconciliation')
    fresh()
    with locked(safe_file(root,inputs.PENDING).parent):
        fresh();pending=_pending(root,plan['session_id']);pages,transition,marker=_observed(root,pending)
        baseline=pending['baseline'];documents=[e['path'] for e in pending['effects']]
        if baseline is None:
            value=dict(schema=1,project=identity(root),pages=pages)
            atomic_write(safe_file(root,inputs.REGISTRY),encoded(authentication.seal(root,value))+'\n',mode=0o600)
            update_index(root)
        if marker:atomic_write(safe_file(root,marker),encoded(authentication.seal(root,dict(schema=1,operation=plan['operation'])))+'\n',mode=0o600)
        result=dict(status='baseline_reconciled' if baseline else 'documents_reconciled',documents=documents,
                    checks='not_run',delivery_authorized=False)
        if documents:
            from .maintenance import after_write
            result['memory']=after_write(root)
        _observed(root,pending)
        record=safe_file(root,OPERATIONS+plan['operation']+'.json')
        if not record.exists():atomic_write(record,encoded(authentication.seal(root,operation(pending['plan'],result,transition)))+'\n',mode=0o600)
        safe_file(root,inputs.PENDING).unlink()
    return result
