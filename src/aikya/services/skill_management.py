"""Trusted native skill administration, never a model tool or inferred consent."""
from aikya.code_index.policy import project_root
from aikya.catalogs import github_source
from . import selected_skills as project,skill_library as library,skill_fetch


def _scope(scope):
    if scope not in ('project','global'):raise ValueError('Choose project or global skill scope')


def preview(root,scope='project',action='install',source=None,name=None,source_hash=None):
    _scope(scope);root=project_root(root)
    if isinstance(source,dict) and source.get('kind')=='captured' and source.get('project')!=str(root):raise ValueError('Captured source belongs to another project')
    if action=='recover':
        if any(v is not None for v in (source,name,source_hash)):raise ValueError('Recovery uses the owned pending operation')
        return project.recovery_preview(root) if scope=='project' else library.recovery_preview()
    if action=='install':
        if name is not None or source_hash is not None:raise ValueError('Choose an explicit source descriptor')
        return project.preview(root,source) if scope=='project' else library.preview(source)
    args=dict(action=action,source=source,name=name,source_hash=source_hash)
    return project.change_preview(root,**args) if scope=='project' else library.change_preview(**args)


def apply(root,plan,scope='project',recovery=False,approved=False):
    _scope(scope)
    if type(recovery) is not bool:raise ValueError('Invalid recovery action')
    if recovery:return project.recover(root,plan,approved) if scope=='project' else library.recover(plan,approved)
    return project.apply(root,plan,approved) if scope=='project' else library.apply(plan,approved)


def status(root,scope='project',offset=0):
    _scope(scope)
    if scope=='global':
        if offset!=0:raise ValueError('Global library fits one bounded page')
        return library.status()
    return project.status(root,offset)


def resolve(root,repo,ref=None,approved=False):
    if approved is not True:raise ValueError('Explicit public metadata request confirmation required')
    return github_source.resolve(repo,ref)
