"""Owned global skill metadata; no model/session/memory discovery or activation."""
import json
from aikya.installation.bootstrap import options,state
from aikya.core.checkpoints import identity,safe_file
from aikya.review import authentication
from aikya.review.contracts import read_record,hash_id
from aikya.tools.skills_lint import NAME

REGISTRY='registry.json'
PENDING='pending.json'


def root():
    application=state.safe(options.app_root())
    if application.exists() and any(application.iterdir()):
        marker=state.safe(application/'owner.json')
        if not marker.is_file() or marker.stat().st_size>16000 or json.loads(marker.read_text())!=state.OWNER:
            raise ValueError('Unowned application data is preserved')
    folder=state.safe(application/'skills')
    if folder.exists() and any(folder.iterdir()):
        marker=state.safe(folder/'owner.json')
        expected=dict(schema=1,generated_by='aikya-pi-skill-library',root=str(folder))
        if not marker.is_file() or marker.stat().st_size>16000 or json.loads(marker.read_text())!=expected:
            raise ValueError('Unknown skill library ownership is preserved')
        allowed={'owner.json',REGISTRY,PENDING,'packages','operations','.aikya','.lock'}
        if set(p.name for p in folder.iterdir())-allowed:raise ValueError('Unknown skill library data is preserved')
    return folder


def load(folder):
    path=safe_file(folder,REGISTRY)
    if not path.exists():
        if any((folder/name).exists() for name in ('packages','operations')) and not safe_file(folder,PENDING).exists():
            raise ValueError('Missing global registry cannot adopt cached skill packages')
        return None
    value=authentication.verify(folder,read_record(folder,REGISTRY,64000))
    if (not isinstance(value,dict) or set(value)!={'schema','project','skills'} or value['schema']!=1
            or value['project']!=identity(folder) or not isinstance(value['skills'],dict) or len(value['skills'])>20):
        raise ValueError('Unknown global skill registry is preserved')
    for name,entry in value['skills'].items():
        if (not NAME.fullmatch(name) or name.startswith('aikya-') or not isinstance(entry,dict)
                or set(entry)!={'current','versions'} or not isinstance(entry['versions'],list)
                or not 1<=len(entry['versions'])<=10 or any(not isinstance(v,str) for v in entry['versions'])
                or len(set(entry['versions']))!=len(entry['versions']) or entry['current'] not in entry['versions']):
            raise ValueError('Invalid owned skill library entry')
        for version in entry['versions']:hash_id(version)
    return value


def guard(folder):
    if safe_file(folder,PENDING).exists():raise ValueError('Uncertain skill library effect requires reviewed reconciliation')
