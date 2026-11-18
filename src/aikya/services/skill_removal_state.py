"""Shared ownership and immutable backup validation for native skill withdrawal."""
from contextlib import contextmanager
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.installation.bootstrap import state as installer
from aikya.review import authentication
from aikya.review.contracts import digest,hash_id,read_record
from aikya.tools.skills_lint import NAME
from . import selected_skills as project,skill_library_state as library,skill_packages as packages

GENERATOR='aikya-native-skill-removal'


def context(root,scope,guard=True):
    if scope not in ('project','global'):raise ValueError('Choose project or global skill scope')
    root=project_root(root)
    if scope=='project':
        folder=root;registry=project._registry(root);relative=project.REGISTRY
        pending='.aikya/pi/skills/pending.json';operations='.aikya/pi/skills/operations/'
    else:
        folder=library.root();registry=library.load(folder);relative=library.REGISTRY
        pending=library.PENDING;operations='operations/'
    if guard and safe_file(folder,pending).exists():raise ValueError('Pending skill operation requires explicit recovery')
    return dict(root=root,folder=folder,scope=scope,registry=registry,relative=relative,pending=pending,operations=operations)


@contextmanager
def lock(ctx):
    if ctx['scope']=='global':
        with installer.installation_lock(ctx['folder'].parent):yield
    else:
        with locked(safe_file(ctx['folder'],'.aikya/pi/skills/.lock').parent):yield


def names(value):
    if (not isinstance(value,list) or not 1<=len(value)<=20
            or any(not isinstance(n,str) or not NAME.fullmatch(n) or n.startswith('aikya-') for n in value)
            or len(value)!=len(set(value))):
        raise ValueError('Select unique owned skill names; canonical commands are protected')
    return sorted(value)


def cached(ctx,name,entry):
    folder=ctx['folder']
    if ctx['scope']=='project':
        source=entry.get('source_hash');hash_id(source)
        destination='.aikya/pi/skills/packages/'+source+'/'+name
        data=packages.read(folder,destination)
        manifest=authentication.verify(folder,read_record(folder,destination+'/manifest.json',32000))
        if project.make_entry(destination,data,manifest)!=entry or data['name']!=name:
            raise ValueError('Changed or legacy skill package requires review; preserved')
    else:
        if (not isinstance(entry,dict) or set(entry)!={'current','versions'} or not isinstance(entry['versions'],list)
                or not 1<=len(entry['versions'])<=10 or entry['current'] not in entry['versions']):raise ValueError('Invalid retained global entry')
        for version in entry['versions']:
            hash_id(version);data=packages.read(folder,'packages/'+version+'/'+name)
            if data['name']!=name or data['source_hash']!=version:raise ValueError('Changed retained global skill is preserved')


def original(ctx,operation_id):
    hash_id(operation_id)
    value=authentication.verify(ctx['folder'],read_record(ctx['folder'],ctx['operations']+operation_id+'.json',500000))
    if (value.get('generated_by')!=GENERATOR or value.get('status')!='completed'
            or value.get('project')!=identity(ctx['folder']) or value.get('plan',{}).get('action')!='remove'
            or digest(value['plan'])!=operation_id or value['plan'].get('scope')!=ctx['scope']):
        raise ValueError('Select a completed owned withdrawal operation')
    return value


def comparison(ctx):
    return project._comparison(ctx['root'],ctx['registry']) if ctx['scope']=='project' else None


def pending(ctx):
    value=authentication.verify(ctx['folder'],read_record(ctx['folder'],ctx['pending'],500000))
    fields={'schema','generated_by','project','status','plan','backup','next_registry','comparison','audit'}
    if (not isinstance(value,dict) or set(value)!=fields or value['schema']!=1
            or value['generated_by']!=GENERATOR or value['project']!=identity(ctx['folder']) or value['status']!='pending'):
        raise ValueError('Unknown skill interruption is preserved')
    plan=value['plan']
    if plan['scope']!=ctx['scope'] or plan['project']!=identity(ctx['folder']):raise ValueError('Foreign recovery scope')
    for name,entry in value['backup'].items():cached(ctx,name,entry)
    if digest(ctx['registry']) not in (plan['before'],digest(value['next_registry'])):raise ValueError('Registry changed during withdrawal')
    return value
