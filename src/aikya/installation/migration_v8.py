"""Explicit legacy-to-Pi profile adoption with signed local backups and guarded undo."""
import hashlib
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.documentation.layout import index_paths,write_document,stamp
from aikya.documentation.language import resolve
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import digest,encoded,parse,read_record,identifier
from aikya.storage import atomic_write
from aikya.workflows.methodology import normalize_methodology
from .profile import validated
from .portable import PROFILE,SELECTION

FILES=(PROFILE,SELECTION)


def _raw(root,path):
    return read_source(root,path,65536) if safe_file(root,path).exists() else None


def _hash(value):
    return hashlib.sha256(value).hexdigest() if value is not None else None


def _destination(root,methodology):
    raw=_raw(root,PROFILE)
    if raw is None:raise ValueError('An existing managed legacy profile is required')
    value=parse(raw)
    if (not isinstance(value,dict) or value.get('_generated_by')!='claude-dev-harness-interactive'
            or value.get('schema_version')!=1 or not isinstance(value.get('decisions'),dict)):
        raise ValueError('Custom or already migrated profile is preserved')
    old=value['decisions']
    if methodology not in ('odd','sdd') or methodology!=normalize_methodology(old.get('methodology')):
        raise ValueError('Migration requires explicit preservation of the existing ODD/SDD choice')
    decisions=validated({**old,'methodology':methodology,'mode':'existing'},root)
    if set(old)-set(decisions):raise ValueError('Custom profile fields require manual migration')
    selection=_raw(root,SELECTION)
    if selection is not None:raise ValueError('Existing runtime selection requires manual review')
    value={**value,'_generated_by':'aikya-pi-onboarding','decisions':decisions}
    selected=dict(schema=1,generated_by='aikya-runtime-selection',project=identity(root),runtime='pi')
    result={PROFILE:(encoded(value)+'\n').encode(),SELECTION:(encoded(selected)+'\n').encode()}
    if any(len(raw)>65536 for raw in result.values()):raise ValueError('Migrated metadata exceeds supported bounds')
    return result


def preview(root,methodology):
    root=project_root(root);after=_destination(root,methodology)
    before={path:_hash(_raw(root,path)) for path in FILES}
    revision=freeze_candidate(root,'pi-migration',['aikya/docs/overview.md'],session_id='migration')['id']
    payload=dict(schema=1,project=identity(root),methodology=methodology,language=resolve(root),source_revision=revision,
                 before=before,after={path:_hash(raw) for path,raw in after.items()})
    ident=digest(payload)[:32];report='aikya/docs/operations/runtime-migration-'+ident+'.md'
    if safe_file(root,report).exists():raise ValueError('Existing migration report is preserved')
    if safe_file(root,'.aikya/pi/migrations/'+ident+'/record.json').parent.exists():
        raise ValueError('Existing migration folder requires explicit recovery')
    index_paths(root);resolve(root)
    if safe_file(root,authentication.KEY).exists():authentication.key(root)
    return dict(**payload,id=ident,report=report,
                operations=[*[dict(path=path,action='replace' if before[path] else 'create') for path in FILES],
                            dict(path=report,action='create'),dict(path='aikya/docs/indice.md',action='update-generated-navigation')],
                authority_path=authentication.KEY,
                backup_path='.aikya/pi/migrations/'+ident+'/',
                preserved=['source','existing document bodies','local notes and code-index policy','client settings and installed skills'])


def _folder(root,ident):
    identifier(ident)
    if len(ident)!=32 or any(c not in 'abcdef0123456789' for c in ident):raise ValueError('Invalid migration ID')
    return '.aikya/pi/migrations/'+ident


def _record(root,ident):
    path=_folder(root,ident)+'/record.json'
    value=authentication.verify(root,read_record(root,path,16000))
    if value.get('project')!=identity(root) or value.get('id')!=ident or value.get('schema')!=1:
        raise ValueError('Foreign migration record')
    return value


def _save(root,record):
    path=safe_file(root,_folder(root,record['id'])+'/record.json')
    atomic_write(path,encoded(authentication.seal(root,record))+'\n',mode=0o600)


def _report(record,status):
    if record['language']=='es':
        return stamp('# Migración del runtime '+record['id']+'\n\nEstado: '+status+'.\n\n'
            +'Identidad del proyecto: `'+record['project']+'`. Metodología: `'+record['methodology']+'`.\n\n'
            +'Metadatos modificados: `.harness/project-profile.json` y `.aikya/runtime-selection.json`. '
            +'Los bytes originales están respaldados en `.aikya/pi/migrations/'+record['id']+'/`. '
            +'Se conservaron código, documentos existentes, memoria, políticas, configuración de clientes y skills. '
            +'Este registro acredita la adopción del perfil; la aceptación completa del producto sigue pendiente.')
    return stamp('# Runtime migration '+record['id']+'\n\nStatus: '+status+'.\n\n'
        +'Project identity: `'+record['project']+'`. Methodology: `'+record['methodology']+'`.\n\n'
        +'Changed metadata: `.harness/project-profile.json` and `.aikya/runtime-selection.json`. '
        +'Original bytes are backed up locally under `.aikya/pi/migrations/'+record['id']+'/`. '
        +'Source, existing documentation, memory/index policy, client settings and installed skills were preserved. '
        +'This records profile adoption; it does not certify full workflow or release compatibility.')


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit migration approval required')
    root=project_root(root)
    if not isinstance(plan,dict) or not isinstance(plan.get('id'),str):raise ValueError('Invalid migration preview')
    folder=_folder(root,plan['id']);path=safe_file(root,folder+'/record.json')
    if path.exists():
        record=_record(root,plan['id'])
        if (record['plan']!=plan or record['status']!='applied' or any(_hash(_raw(root,p))!=record['after'][p] for p in FILES)
                or _raw(root,record['report'])!=_report(record,'migrated').encode()):
            raise ValueError('Migration exists or is uncertain; reconcile/rollback without replay')
        return dict(status='migrated',id=record['id'],report=record['report'])
    if preview(root,plan.get('methodology'))!=plan:raise ValueError('Migration source changed')
    guard=safe_file(root,'.aikya/pi/migrations/.lock').parent;guard.mkdir(parents=True,exist_ok=True)
    with locked(guard):
        if preview(root,plan['methodology'])!=plan or path.exists():raise ValueError('Migration changed before commit')
        after=_destination(root,plan['methodology']);authentication.key(root,create=True)
        record=dict(schema=1,project=identity(root),id=plan['id'],plan=plan,status='pending',methodology=plan['methodology'],language=plan['language'],
                    before=plan['before'],after=plan['after'],report=plan['report'],modes={})
        for index,p in enumerate(FILES):
            raw=_raw(root,p);target=safe_file(root,p)
            record['modes'][p]=(target.stat().st_mode&0o777) if raw is not None else 0o600
            if raw is not None:atomic_write(safe_file(root,folder+'/'+str(index)+'.before'),raw,mode=0o600)
        _save(root,record)  # Durable originals and intent precede all user metadata effects.
        for p in FILES:
            if _hash(_raw(root,p))!=record['before'][p]:raise ValueError('Metadata changed; explicit reconciliation required')
            atomic_write(safe_file(root,p),after[p],mode=record['modes'][p])
        write_document(root,record['report'],_report(record,'migrated'))
        record['status']='applied';_save(root,record)
        return dict(status='migrated',id=record['id'],report=record['report'])


def rollback_preview(root,ident):
    root=project_root(root);record=_record(root,ident)
    if record['status'] not in ('pending','applied','restored'):raise ValueError('Unknown migration recovery state')
    for p in FILES:
        if _hash(_raw(root,p)) not in (record['before'][p],record['after'][p]):raise ValueError('Customized metadata is preserved')
    report=_raw(root,record['report'])
    allowed={_hash(_report(record,status).encode()) for status in ('migrated','restored')}
    if report is not None and _hash(report) not in allowed:raise ValueError('Customized migration report is preserved')
    index_paths(root);resolve(root)
    return dict(id=ident,status=record['status'],project=identity(root),restore=list(FILES),audit_report=record['report'])


def rollback(root,ident,approved=False):
    if approved is not True:raise ValueError('Explicit rollback approval required')
    root=project_root(root);rollback_preview(root,ident)
    guard=safe_file(root,'.aikya/pi/migrations/.lock').parent
    with locked(guard):
        rollback_preview(root,ident);record=_record(root,ident)
        originals={}
        for index,p in enumerate(FILES):
            raw=_raw(root,_folder(root,ident)+'/'+str(index)+'.before') if record['before'][p] is not None else None
            if _hash(raw)!=record['before'][p]:raise ValueError('Original backup is unavailable or changed')
            originals[p]=raw
        for p,raw in originals.items():
            path=safe_file(root,p)
            if raw is None:
                if path.exists():path.unlink()
            else:atomic_write(path,raw,mode=record['modes'][p])
        write_document(root,record['report'],_report(record,'restored'),replace_generated=True)
        record['status']='restored';_save(root,record)
        return dict(status='restored',id=ident,report=record['report'])
