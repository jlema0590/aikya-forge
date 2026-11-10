"""Confirmed pinned public data cache, without installing or activating instructions."""
from aikya.catalogs import github_source
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.review import authentication
from aikya.review.contracts import encoded
from aikya.storage import atomic_write
from aikya.tools.skills_lint import NAME
from . import skill_packages as packages
from .skill_source import from_bytes

BASE='.aikya/pi/skill-sources/'


def preview(root,repo,path,commit,name):
    root=project_root(root);repo=github_source.repository(repo);path=github_source.relative(path);github_source.object_id(commit)
    if not isinstance(name,str) or not NAME.fullmatch(name) or name.startswith('aikya-'):raise ValueError('Choose a nonreserved skill name')
    plan=dict(schema=1,project=identity(root),repo=repo,path=path,commit=commit,name=name)
    return dict(plan=plan,review=dict(source=repo,path=path,commit=commit,name=name,activation='none',execution='none',
        network='Public HTTPS only; no credentials, redirects, checkout, scripts or dependency installation',
        limits='80 files, 5 MB total; captured content requires a separate installation review'))


def apply(root,plan,approved=False,*,cancel=lambda:False):
    if approved is not True:raise ValueError('Explicit source download confirmation required')
    root=project_root(root);fields={'schema','project','repo','path','commit','name'}
    if not isinstance(plan,dict) or set(plan)!=fields or preview(root,**{k:plan[k] for k in ('repo','path','commit','name')})['plan']!=plan:
        raise ValueError('Invalid pinned source preview')
    capture=github_source.capture(plan['repo'],plan['path'],plan['commit'],cancel=cancel)
    provenance=plan['repo']+'@'+plan['commit']+':'+plan['path']
    data=from_bytes(capture['files'],provenance,expected_name=plan['name'])
    destination=BASE+data['source_hash']+'/'+data['name'];pending=destination+'/pending.json'
    packages.preflight(root,destination,data)
    # Network/validation precede local effects. Partial existing data is preserved, never replayed.
    folder=safe_file(root,BASE+'.lock').parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        if cancel():raise ValueError('Source download interrupted before capture')
        if safe_file(root,destination+'/.probe').parent.exists():
            current=packages.read(root,destination)
            if current['source']!=provenance or current['files']!=data['files'] or safe_file(root,pending).exists():
                raise ValueError('Existing or uncertain captured source requires review')
        else:
            authentication.key(root,create=True)
            value=dict(schema=1,project=identity(root),plan=plan,source_hash=data['source_hash'],tree=capture['tree'])
            atomic_write(safe_file(root,pending),encoded(authentication.seal(root,value))+'\n',mode=0o600)
            zipped=packages.write(root,destination,data);packages.manifest(root,destination,data,zipped)
            packages.read(root,destination);safe_file(root,pending).unlink()
    source=dict(kind='captured',project=str(root),source_hash=data['source_hash'],name=data['name'])
    return dict(status='captured',activation='none',execution='none',source=source,package=str(root/destination),
                provenance=dict(repo=plan['repo'],path=plan['path'],commit=plan['commit'],tree=capture['tree']),ignored_fields=data['ignored_fields'])


def read(source,root=None):
    fields={'kind','project','source_hash','name'}
    if not isinstance(source,dict) or set(source)!=fields or source['kind']!='captured':raise ValueError('Invalid captured source descriptor')
    project=project_root(source['project'])
    if root is not None and project!=project_root(root):raise ValueError('Captured source belongs to another project')
    from aikya.review.contracts import hash_id,identifier
    hash_id(source['source_hash']);identifier(source['name'])
    destination=BASE+source['source_hash']+'/'+source['name']
    if safe_file(project,destination+'/pending.json').exists():raise ValueError('Captured source has uncertain effects')
    data=packages.read(project,destination)
    if data['source_hash']!=source['source_hash'] or data['name']!=source['name']:raise ValueError('Captured source identity changed')
    return data
