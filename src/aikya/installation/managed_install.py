"""Reviewed native promotions; prior payloads and user data are retained for recovery."""
import hashlib
from pathlib import Path
import uuid
from aikya.review import authentication
from aikya.review.contracts import encoded
from aikya.storage import write_new
from .bootstrap import state
from .managed_versions import order
from . import managed_launchers as launchers,managed_ownership as ownership,managed_probe,managed_migration,managed_runtime as runtime

CURRENT='terminal/current.json'
PREVIOUS='terminal/previous.json'
PENDING='terminal/pending.json'


def _active(root,relative=CURRENT):
    if not state.safe(root/relative).exists():return None
    receipt=runtime.receipt(root,relative);checked=runtime.inspect(root/receipt['payload'],version=receipt['version'],target=receipt['platform'])
    if checked['manifest_hash']!=receipt['manifest_hash']:raise ValueError('Retained payload identity changed')
    return receipt


def preview(root,source=None,*,action='install'):
    if action not in ('install','update','rollback','uninstall'):raise ValueError('Unknown native installation action')
    root=ownership.root(root)
    if state.safe(root/PENDING).exists():raise ValueError('Interrupted terminal operation requires reviewed recovery')
    current=_active(root);previous=_active(root,PREVIOUS);before=launchers.capture(root)
    if action=='install' and current is not None:raise ValueError('A managed terminal is installed; choose update')
    if action!='install' and current is None:raise ValueError('No active managed terminal for this action')
    candidate=None
    if action in ('install','update'):
        if source is None:raise ValueError('Select an explicitly verified native payload')
        source=state.safe(Path(source).absolute());raw=runtime.parse(runtime._read(source/'manifest.json',16000000))
        if not isinstance(raw,dict):raise ValueError('Unknown native payload identity')
        candidate=runtime.inspect(source,version=raw.get('version'),target=runtime.host_platform())
        if current and current['manifest_hash']!=candidate['manifest_hash'] and order(candidate['version'])<=order(current['version']):
            raise ValueError('Update requires a newer immutable release; use explicit retained rollback for a downgrade')
    elif action=='rollback':
        if previous is None:raise ValueError('No known prior payload is retained')
        source=root/previous['payload'];candidate=runtime.inspect(source,version=previous['version'],target=previous['platform'])
    after=None
    if candidate:
        destination=root/'terminal/versions'/candidate['manifest_hash']
        if destination.exists():
            known=runtime.inspect(destination,version=candidate['version'],target=runtime.host_platform())
            if known['manifest_hash']!=candidate['manifest_hash']:raise ValueError('Existing candidate payload differs')
        python=destination/Path(candidate['python']).relative_to(source)
        retain=runtime.host_platform().startswith('win32') and ownership.read(root,launchers.RECORD) is not None
        after=launchers.intended(before,launchers.contents(root,python),retain_manager=retain)
    else:after=launchers.restored(before)
    return dict(schema=1,action=action,root=str(root),source=str(source) if candidate else None,
                version=candidate['version'] if candidate else current['version'],manifest_hash=candidate['manifest_hash'] if candidate else None,
                current=current,previous=previous,noop=bool(current and candidate and current['manifest_hash']==candidate['manifest_hash']),legacy=managed_migration.preview(root),launchers_before=before,launchers_after=after,writes=False)


def _copy(source,destination,candidate):
    if destination.exists():return
    destination.mkdir(parents=True)
    files=dict(candidate['manifest']['files']);raw=runtime._read(source/'manifest.json',16000000)
    files['manifest.json']=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),executable=False)
    for name,entry in files.items():
        raw=runtime._read(state.safe(source/name),entry['size'])
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Payload source changed during preparation')
        path=state.safe(destination/name);path.parent.mkdir(parents=True,exist_ok=True);write_new(path,raw,mode=0o700 if entry['executable'] else 0o600)


def _pointer(root,relative,record):
    if record is None:state.safe(root/relative).unlink(missing_ok=True)
    else:ownership.save(root,relative,record)


def apply(plan,*,approved=False):
    if approved is not True:raise ValueError('Explicit native installation approval is required')
    if not isinstance(plan,dict) or not isinstance(plan.get('root'),str):raise ValueError('Invalid native installation preview')
    root=ownership.root(plan['root'])
    if preview(root,plan.get('source'),action=plan.get('action'))!=plan:raise ValueError('Native installation changed since preview')
    if plan['noop']:return dict(status='up-to-date',version=plan['version'],payloads_retained=True)
    with state.installation_lock(root):
        if preview(root,plan.get('source'),action=plan['action'])!=plan:raise ValueError('Native installation changed before reservation')
        authentication.key(root,create=True);ident=uuid.uuid4().hex
        operation='terminal/operations/'+ident+'.json';record=dict(schema=1,id=ident,plan=plan,status='reserved',after=None)
        ownership.save(root,operation,record);ownership.save(root,PENDING,dict(schema=1,operation=operation,id=ident))
        managed_migration.backup(root,plan['legacy'],root/'terminal/operations'/ident/'legacy')
        candidate=None;after=None
        if plan['source']:
            source=Path(plan['source']);candidate=runtime.inspect(source,version=plan['version'],target=runtime.host_platform())
            destination=root/'terminal/versions'/plan['manifest_hash'];_copy(source,destination,candidate)
            checked=runtime.inspect(destination,version=plan['version'],target=runtime.host_platform())
            if checked['manifest_hash']!=plan['manifest_hash']:raise ValueError('Final candidate differs from reviewed payload')
            managed_probe.check(checked,root/'terminal/operations'/ident/'probe-home')
            checked=runtime.inspect(destination,version=plan['version'],target=runtime.host_platform())
            if checked['manifest_hash']!=plan['manifest_hash']:raise ValueError('Native payload changed during preflight')
            after=dict(schema=1,generated_by='aikya-managed-terminal',version=plan['version'],platform=runtime.host_platform(),
                       payload='terminal/versions/'+plan['manifest_hash'],manifest_hash=plan['manifest_hash'])
        record.update(status='prepared',after=after);ownership.save(root,operation,record)
        launchers.publish(root,plan['launchers_after'])
        _pointer(root,PREVIOUS,plan['current']);_pointer(root,CURRENT,after)
        record['status']='complete';ownership.save(root,operation,record);state.safe(root/PENDING).unlink()
    return dict(status={'install':'installed','update':'updated','rollback':'rolled-back','uninstall':'uninstalled'}[plan['action']],version=plan['version'],operation=ident,payloads_retained=True)


def recover(root,*,approved=False):
    """Finalize only an entirely observed promotion; never rerun uncertain effects."""
    if approved is not True:raise ValueError('Explicit native recovery approval is required')
    root=ownership.root(root)
    with state.installation_lock(root):
        pending=ownership.read(root,PENDING)
        if (not isinstance(pending,dict) or set(pending)!={'schema','operation','id'} or pending['schema']!=1
                or not isinstance(pending['id'],str) or len(pending['id'])!=32 or any(c not in 'abcdef0123456789' for c in pending['id'])
                or pending['operation']!='terminal/operations/'+pending['id']+'.json'):raise ValueError('No known pending native operation')
        record=ownership.read(root,pending['operation'])
        if (not isinstance(record,dict) or set(record)!={'schema','id','plan','status','after'} or record['schema']!=1
                or record['id']!=pending['id'] or record['status'] not in ('prepared','complete') or not isinstance(record['plan'],dict)
                or record['plan'].get('root')!=str(root)):raise ValueError('Incomplete native effect requires manual review')
        plan=record['plan']
        if (_active(root)!=record['after'] or _active(root,PREVIOUS)!=plan['current']
                or launchers.capture(root)!=plan['launchers_after']):raise ValueError('Partial/customized effects are preserved; automatic replay is blocked')
        record['status']='complete';ownership.save(root,pending['operation'],record);state.safe(root/PENDING).unlink()
    return dict(status='reconciled',operation=pending['id'],replayed=False)
