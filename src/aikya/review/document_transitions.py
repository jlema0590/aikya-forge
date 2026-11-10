"""Signed completed documentation deltas, without transferring checks or consent."""
import os
import re
from aikya.core.checkpoints import identity,safe_file
from aikya.documentation.layout import canonical
from .authentication import verify
from .contracts import digest,dossier,hash_id,read_record

OPERATIONS='.aikya/pi/documentation/operations/'


def permitted(path):
    if not isinstance(path,str) or not path.startswith('aikya/docs/'):return False
    relative=path.removeprefix('aikya/docs/')
    if canonical(relative)!=relative:return False
    return (relative in ('overview.md','plan/testing.md','bugs/bugs.md')
            or relative.startswith(('architecture/','decisions/','plan/test-cases/','quality/test-reports/'))
            or re.fullmatch(r'changes/REQ-[0-9]{8}-[a-f0-9]{8}\.md',relative) is not None)


def transition(before,documents):
    changes={item['path']:dict(before=before['files'].get(item['path']),after=digest_bytes(item['after'].encode()))
             for item in documents}
    if any(not permitted(path) for path in changes):raise ValueError('Control documents cannot become source transitions')
    return dict(base=before['base'],changes=changes)


def digest_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def _events(root,session,base):
    folder=safe_file(root,OPERATIONS+'.probe').parent
    if not folder.exists():return []
    result=[]
    with os.scandir(folder) as entries:
        for count,entry in enumerate(entries):
            if count>=200 or entry.is_symlink() or not entry.is_file():raise ValueError('Unsafe or oversized documentation operation history')
            if not re.fullmatch(r'[a-f0-9]{64}\.json',entry.name):raise ValueError('Unknown documentation operation')
            value=verify(root,read_record(root,OPERATIONS+entry.name,100000))
            if (not isinstance(value,dict) or value.get('project')!=identity(root) or value.get('schema')!=1
                    or value.get('status')!='recorded' or digest(value.get('plan'))+'.json'!=entry.name):
                raise ValueError('Unknown documentation operation identity')
            event=value.get('transition')
            if event is None:continue  # Older records grant no new source scope.
            if (not isinstance(event,dict) or set(event)!={'base','changes'} or not isinstance(event['changes'],dict)
                    or not 1<=len(event['changes'])<=4):raise ValueError('Invalid documentary transition')
            for path,change in event['changes'].items():
                if not permitted(path) or not isinstance(change,dict) or set(change)!={'before','after'}:
                    raise ValueError('Invalid documentary transition path')
                if change['before'] is not None:hash_id(change['before'])
                hash_id(change['after'])
            if value['plan']['session_id']==session and event['base']==base:result.append(event['changes'])
    return result


def observed(root,previous,candidate,paths):
    if not paths:return set()
    if (root is None or not candidate['policy'].get('native_observations')
            or previous['session_id']!=candidate['session_id'] or previous['base']!=candidate['base']):
        raise ValueError('Changed source is outside the declared review scope')
    if any(not permitted(path) for path in paths):raise ValueError('Unobserved source or methodology change')
    events=_events(root,candidate['session_id'],candidate['base'])
    for path in paths:
        reachable={previous['files'].get(path)}
        for _ in range(201):
            following=reachable|{e[path]['after'] for e in events if path in e and e[path]['before'] in reachable}
            if following==reachable:break
            reachable=following
        if candidate['files'].get(path) not in reachable:raise ValueError('Documentary change has no complete host observation')
    return set(paths)


def review_scope(root,candidate):
    """Include earlier observed pages in the final bounded reviewer packet."""
    from .candidates import validate
    paths=set();current=candidate;seen=set()
    for _ in range(100):
        parent=current['parent']
        if parent is None:return sorted(paths)
        if parent in seen:raise ValueError('Cyclic documentary lineage')
        seen.add(parent)
        previous=validate(root,read_record(root,dossier(candidate['change_id'])+'/candidates/'+parent+'.json'))
        if (previous['policy']!=candidate['policy'] or previous['change_id']!=candidate['change_id']
                or previous['session_id']!=candidate['session_id']):return sorted(paths)
        outside={p for p in previous['files'].keys()|current['files'].keys()
                 if previous['files'].get(p)!=current['files'].get(p)}-set(current['scope'])
        paths.update(observed(root,previous,current,outside))
        if len(paths)>20:raise ValueError('Documentary review scope requires explicit escalation')
        current=previous
    raise ValueError('Documentary lineage exceeds supported bound')
