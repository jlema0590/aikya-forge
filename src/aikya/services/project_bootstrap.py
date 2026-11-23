"""Native project/infra/scaffold facade; source effects use confirmed batches."""
from aikya.code_index.policy import project_root
from aikya.documentation.language import resolve
from aikya.review.contracts import encoded,digest
from . import bootstrap_plans as plans,generation
from .documentation_inputs import profile


def _assemble(root,command,data):
    if not isinstance(data,dict) or len(encoded(data))>8000:raise ValueError('Bounded bootstrap input required')
    p=profile(root);language=resolve(root);action=data.get('action')
    if command=='aikya-project':
        if action not in ('plan','record'):raise ValueError('Choose plan or record')
        review=plans.project(root,data)
        files={'aikya/docs/plan/project-'+review['slug']+'.md':plans.project_document(review,language)}
        return p,'bootstrap',files,review,action=='plan'
    if command=='aikya-infra':
        if action not in ('plan','generate') or set(data)!=({'action'} if action=='plan' else {'action','paths'}):
            raise ValueError('Choose infra plan or named-file generation')
        files,details=plans.infra(root,p,language)
        if action=='plan':
            return p,'infra',files,{**details,'artifacts':[dict(path=name,bytes=len(raw)) for name,raw in files.items()],'execution':'not_run'},True
        selected=data['paths']
        if not isinstance(selected,list) or not 1<=len(selected)<=100 or len(set(selected))!=len(selected) or any(name not in files for name in selected):
            raise ValueError('Choose known unique proposed artifacts')
        return p,'infra',{name:files[name] for name in selected},details,False
    if command=='aikya-scaffold':
        if action!='plan' or set(data)!={'action'}:raise ValueError('Generator preparation requires an identified recipe')
        return p,'scaffold',{},plans.scaffold_plan(p),True
    raise ValueError('Unknown bootstrap command')


def preview(root,command,input_data,session_id):
    root=project_root(root);p,category,files,details,readonly=_assemble(root,command,input_data)
    if readonly:
        status='existing_project' if command=='aikya-scaffold' and p['mode']!='new' else 'manual_required' if command=='aikya-scaffold' and not details['generators'] else 'planned'
        return dict(status=status,plan=None,review=details)
    value=generation.preview(root,files,session_id,category,details)
    if value['plan'] is not None:
        if value['plan']['profile_hash']!=digest(p):raise ValueError('Profile changed during bootstrap preparation')
        value['plan']=dict(command=command,input_data=input_data,session_id=session_id,generation=value['plan'])
        if len(encoded(value['plan']))>12000:raise ValueError('Bootstrap confirmation exceeds its host bound')
    return value


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native bootstrap confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'command','input_data','session_id','generation'}:raise ValueError('Invalid bootstrap preview')
    value=preview(root,plan['command'],plan['input_data'],plan['session_id'])
    if value['plan']!=plan:raise ValueError('Bootstrap preview changed')
    _,_,files,_,_=_assemble(root,plan['command'],plan['input_data'])
    return generation.apply(root,plan['generation'],files,approved=True)
