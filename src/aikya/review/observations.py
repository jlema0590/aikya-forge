"""Private host observation witnesses for native-policy executions, not raw output."""
from aikya.core.checkpoints import safe_file,identity
from aikya.review import authentication
from aikya.review.contracts import identifier,digest,encoded,read_record
from aikya.storage import atomic_write


def path_for(change_id,run_id):
    return '.aikya/pi/check-observations/'+identifier(change_id)+'/'+identifier(run_id)+'.json'


def record(root,candidate,metadata):
    path=safe_file(root,path_for(candidate['change_id'],metadata['run_id']))
    if path.exists():raise ValueError('Existing host observation is preserved; reconcile without replay')
    payload=dict(schema=1,project=identity(root),candidate=candidate['id'],session_id=candidate['session_id'],
                 change_id=candidate['change_id'],run_id=metadata['run_id'],metadata_hash=digest(metadata))
    authentication.key(root,create=True)
    atomic_write(path,encoded(authentication.seal(root,payload))+'\n',mode=0o600)


def verify(root,candidate,metadata):
    value=authentication.verify(root,read_record(root,path_for(candidate['change_id'],metadata['run_id']),4096))
    expected=dict(schema=1,project=identity(root),candidate=candidate['id'],session_id=candidate['session_id'],
                  change_id=candidate['change_id'],run_id=metadata['run_id'],metadata_hash=digest(metadata))
    if value!=expected:raise ValueError('Native execution differs from the private host observation')
