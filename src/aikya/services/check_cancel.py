"""Cooperative host cancellation bound to one author/candidate/run, never a PID."""
import time
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.review import authentication
from aikya.review.candidates import validate
from aikya.review.contracts import identifier,hash_id,dossier,read_record,encoded
from aikya.storage import atomic_write


def _path(change_id,run_id):
    return '.aikya/pi/check-cancel/'+identifier(change_id)+'/'+identifier(run_id)+'.json'


def _payload(root,change_id,session_id,run_id,candidate,allow_future=False):
    identifier(session_id);hash_id(candidate)
    path=safe_file(root,dossier(change_id)+'/candidates/'+candidate+'.json')
    if path.exists():
        old=read_record(root,path.relative_to(root).as_posix());validate(root,old)
        if old['session_id']!=session_id or old['change_id']!=change_id:raise ValueError('Foreign check cancellation')
    elif allow_future:
        from .checks import _registry
        if _registry(root,change_id)['session_id']!=session_id:raise ValueError('Foreign planned check cancellation')
    else:raise ValueError('Unknown execution candidate')
    return dict(schema=1,project=identity(root),change_id=change_id,session_id=session_id,run_id=identifier(run_id),
                candidate=candidate,operation='cancel.check')


def request(root,change_id,session_id,run_id,candidate):
    root=project_root(root);payload=_payload(root,change_id,session_id,run_id,candidate,allow_future=True)
    target=safe_file(root,dossier(change_id)+'/checks/'+run_id+'/execution.json')
    if target.exists():
        meta=read_record(root,target.relative_to(root).as_posix(),65536)
        if meta.get('candidate')!=candidate or meta.get('session_id')!=session_id:raise ValueError('Foreign check run')
        if meta.get('status')!='pending':return dict(status='already_finished',run_id=run_id)
    path=safe_file(root,_path(change_id,run_id));path.parent.mkdir(parents=True,exist_ok=True)
    with locked(path.parent):
        if path.exists():
            if authentication.verify(root,read_record(root,path.relative_to(root).as_posix(),4096))!=payload:
                raise ValueError('Customized cancellation is preserved')
        else:atomic_write(path,encoded(authentication.seal(root,payload))+'\n',mode=0o600)
    return dict(status='cancellation_requested',run_id=run_id)


def predicate(root,plan):
    expected=_payload(root,plan['change_id'],plan['session_id'],plan['run_id'],plan['candidate'])
    relative=_path(plan['change_id'],plan['run_id']);next_read=0;stopped=False
    def cancel():
        nonlocal next_read,stopped
        if stopped:return True
        if time.monotonic()<next_read:return False
        next_read=time.monotonic()+.1
        try:
            if safe_file(root,relative).exists():
                value=authentication.verify(root,read_record(root,relative,4096))
                if value!=expected:raise ValueError('Foreign cancellation record')
                stopped=True
        except (ValueError,OSError):
            # Invalid private control state stops the process; it cannot approve it.
            stopped=True
        return stopped
    return cancel
