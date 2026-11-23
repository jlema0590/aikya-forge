"""Host-neutral project onboarding; never installs client hooks or copied runtimes."""
import hashlib
import json
from aikya.code_index.policy import project_root,read_source,configure
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.discovery.scanner import scan
from aikya.documentation.bootstrap import pages
from aikya.documentation.language import resolve,write_approved
from aikya.documentation.layout import index_paths,write_document,update_index,stamp,content
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import encoded,read_record
from aikya.storage import atomic_write
from .profile import validated

PROFILE='.harness/project-profile.json'
SELECTION='.aikya/runtime-selection.json'


def _hash(root,path):
    target=safe_file(root,path)
    return hashlib.sha256(read_source(root,path,1_048_576)).hexdigest() if target.exists() else None


def _profile(root,answers):
    if not isinstance(answers,dict) or answers.get('methodology') not in ('odd','sdd'):
        raise ValueError('Explicit ODD or SDD selection required')
    known=set(validated(dict(backend='python',methodology='odd'),root))
    if set(answers)-known:raise ValueError('Unknown onboarding fields')
    profile=validated(answers,root)
    if safe_file(root,SELECTION).exists():
        selection=read_record(root,SELECTION,16000)
        if selection!=dict(schema=1,generated_by='aikya-runtime-selection',project=identity(root),runtime='pi'):
            raise ValueError('Runtime selection requires reviewed migration')
    if safe_file(root,PROFILE).exists():
        previous=read_record(root,PROFILE,65536)
        if previous.get('_generated_by')!='aikya-pi-onboarding':
            raise ValueError('Existing profile requires explicit runtime migration; preserved')
        old=previous.get('decisions')
        if old!=profile and not (isinstance(old,dict) and old.get('mode')=='new' and profile['mode']=='existing'
                and {**old,'mode':'existing'}==profile):raise ValueError('Profile changes require reviewed migration')
    if profile['mode']=='new':_new_project(root,safe_file(root,PROFILE).exists())
    return profile


def _new_project(root,managed):
    allowed={'.git','.aikya'}|({'.harness','aikya'} if managed else set())
    comments={'# Aikya local terminal state'}
    patterns={'.aikya/pi/'}
    if managed:
        comments.add('# Aikya local state');patterns|={'.harness/state/','aikya/docs/memory/view/'}
    for entry in root.iterdir():
        if entry.name=='.gitignore':
            text=read_source(root,'.gitignore',1048576).decode('utf8')
            if all(not line.strip() or line in comments|patterns for line in text.splitlines()):continue
        if entry.name not in allowed:raise ValueError('Existing project requires aikya-analyze')
        if entry.name=='aikya':
            if entry.is_symlink():raise ValueError('Linked project source is not a new project')
            for number,path in enumerate(entry.rglob('*')):
                if number>120000:raise ValueError('New-project inspection exceeded its bound')
                if path.is_symlink() or (path.is_file() and not path.is_relative_to(root/'aikya/docs')):
                    raise ValueError('Existing project source requires aikya-analyze')


def _documents(root,profile,inventory,language):
    value=dict(profile)
    value['_documentation_testing_evidence']=[p for p in ('tests','test','src/test') if safe_file(root,p+'/.test-evidence').parent.is_dir()]
    docs=pages(value,inventory['modules'],language)
    guide=('Open aikya in this project. Choose a configured provider/model and a project budget before inference. '
           'Use approved scoped writes, execute checks and request independent review. No client runtime, SDK, dependency or application scaffold was installed.'
           if language=='en' else 'Abre aikya en este proyecto. Configura proveedor/modelo y presupuesto antes de la inferencia. '
           'Utiliza escrituras acotadas aprobadas, ejecuta comprobaciones y solicita revisión independiente. No se instaló un runtime de cliente, SDK, dependencia ni código de aplicación.')
    docs['aikya/docs/overview.md']=stamp(content(docs['aikya/docs/overview.md'])+'\n\n## Aikya terminal\n\n'+guide)
    return docs


def preview(root,answers,*,language='en'):
    root=project_root(root);profile=_profile(root,answers);language=resolve(root,language)
    index_paths(root)
    inventory=scan(root)
    if inventory.get('truncated'):raise ValueError('Incomplete repository inventory; narrow adoption explicitly')
    documents=_documents(root,profile,inventory,language)
    operations=[]
    for path,body in documents.items():
        safe_file(root,path)
        operations.append(dict(path=path,action='preserve' if (root/path).exists() else 'create',
                               content_hash=hashlib.sha256(stamp(body).encode()).hexdigest(),before=_hash(root,path)))
    revision=freeze_candidate(root,'pi-onboarding',['aikya/docs/overview.md'],session_id='onboarding')['id']
    return dict(schema=1,generated_by='aikya-portable-onboarding',project=identity(root),answers=answers,
                language=language,source_revision=revision,profile_before=_hash(root,PROFILE),selection_before=_hash(root,SELECTION),
                policy_before=_hash(root,'.aikya/docs-policy.json'),index_policy_before=_hash(root,'.aikya/code-index.json'),operations=operations,
                state_paths=[PROFILE,SELECTION,'.aikya/docs-policy.json','.aikya/code-index.json','.gitignore',
                             '.harness/state/code-index/','aikya/docs/memory/view/','.harness/state/memory-view/','.aikya/pi/onboarding/'])


def _ignore(root):
    path=safe_file(root,'.gitignore');raw=read_source(root,'.gitignore',1048576) if path.exists() else b''
    text=raw.decode('utf8');patterns=('.aikya/pi/','.harness/state/','aikya/docs/memory/view/')
    missing=[p for p in patterns if p not in text.splitlines()]
    if missing:
        suffix=('' if not raw or raw.endswith(b'\n') else '\n')+'\n# Aikya local state\n'+'\n'.join(missing)+'\n'
        atomic_write(path,raw+suffix.encode(),mode=path.stat().st_mode&0o777 if path.exists() else 0o644)


def apply(root,plan,*,approved=False):
    if approved is not True:raise ValueError('Onboarding requires explicit host approval')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','generated_by','project','answers','language','source_revision','profile_before','selection_before','policy_before','index_policy_before','operations','state_paths'}:
        raise ValueError('Invalid onboarding preview')
    # Check before creating even the private lock directory.
    if preview(root,plan['answers'],language=plan['language'])!=plan:raise ValueError('Onboarding inputs or source changed')
    guard=safe_file(root,'.aikya/pi/onboarding/.lock').parent;guard.mkdir(parents=True,exist_ok=True)
    with locked(guard):
        if preview(root,plan['answers'],language=plan['language'])!=plan:raise ValueError('Onboarding source changed before commit')
        profile=_profile(root,plan['answers']);inventory=scan(root);documents=_documents(root,profile,inventory,plan['language'])
        for path in (PROFILE,SELECTION,'.aikya/code-index.json'):safe_file(root,path)
        # Existing code-index policy must be readable before any new metadata writes.
        from aikya.code_index.policy import load_policy
        load_policy(root)
        _ignore(root)
        write_approved(root,plan['language'])
        if not (root/PROFILE).exists():
            atomic_write(root/PROFILE,encoded(dict(schema_version=1,_generated_by='aikya-pi-onboarding',decisions=profile,detected=inventory))+'\n')
        if not (root/SELECTION).exists():
            atomic_write(root/SELECTION,encoded(dict(schema=1,generated_by='aikya-runtime-selection',project=identity(root),runtime='pi'))+'\n')
        created=[]
        for path,body in documents.items():
            if (root/path).exists():continue
            value=write_document(root,path,body,index=False)
            if value:created.append(value)
        update_index(root,plan['language'])
        configure(root,approved=True,manage_ignore=False)
        from aikya.services.maintenance import after_write
        memory=after_write(root)
        return dict(status='initialized',methodology=profile['methodology'],project_type=profile['project_type'],
                    runtime='pi',documents=created,memory=memory)
