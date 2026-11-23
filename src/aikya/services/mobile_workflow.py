"""Mobile task metadata delegates to canonical engines; SDK presence grants no build."""
from aikya.code_index.policy import project_root
from aikya.documentation.language import resolve
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import encoded,digest
from . import mobile_inputs as inputs,odd_workflow,odd_binding,task_binding


def preview(root,data,session):
    root=project_root(root);p,platforms=inputs.selection(root,data.get('platforms'));mobile=inputs.context(p,platforms);action=data.get('action')
    common={'action','platforms'}
    if action=='plan':
        if set(data)!=common|{'files'}:raise ValueError('Mobile plan requires explicit platforms and paths')
        files=inputs.scope(root,data['files'],platforms)
        return dict(status='not_configured' if mobile['readiness']=='not_configured' else 'planned',plan=None,
                    review=dict(mobile=mobile,files=files,methodology=p['methodology'],inference='none'))
    args={key:value for key,value in data.items() if key not in common};inner=None
    if p['methodology']=='odd':
        if action=='status':
            if set(args)!={'feature_id'}:raise ValueError('Choose the ODD mobile feature')
            from aikya.workflows.odd import load
            if load(root,args['feature_id']).get('mobile_scope')!=dict(platforms=platforms,framework=p['mobile_framework']):
                raise ValueError('Choose the recorded mobile feature scope')
            return dict(status='feature_status',plan=None,review=dict(workflow=odd_workflow.status(root,**args),mobile=mobile))
        allowed={'create':{'feature_id','input_data'},'bind':{'feature_id','task_id'},'complete':{'feature_id','task_id','change_id'}}
        if action not in allowed or set(args)!=allowed[action]:raise ValueError('Choose mobile plan/create/bind/status/complete')
        if action=='create':
            raw=args['input_data']
            if not isinstance(raw,dict) or not isinstance(raw.get('tasks'),list):raise ValueError('Explicit mobile feature tasks required')
            for task in raw['tasks']:
                if not isinstance(task,dict):raise ValueError('Explicit mobile task required')
                inputs.scope(root,task.get('files'),platforms)
            sections=raw.get('sections',{})
            if not isinstance(sections,dict) or not isinstance(sections.get('context-and-scope',''),str):raise ValueError('Mobile context must be reviewed prose')
            es=resolve(root)=='es'
            note=(('Plataformas registradas: ' if es else 'Recorded platforms: ')+', '.join(platforms)+'. '+
                  ('Framework registrado: ' if es else 'Recorded framework: ')+p['mobile_framework']+'. '+
                  ('Build, pruebas y simulador no ejecutados por esta planificación.' if es else 'Build, tests and simulator are not executed by this planning.'))
            args={**args,'input_data':{**raw,'mobile_scope':dict(platforms=platforms,framework=p['mobile_framework']),'sections':{**sections,'context-and-scope':(sections.get('context-and-scope','')+'\n\n'+note).strip()}}}
        else:
            state,task,_=odd_binding.task(root,args['feature_id'],args['task_id']);inputs.scope(root,task['files'],platforms)
            if state.get('mobile_scope')!=dict(platforms=platforms,framework=p['mobile_framework']):
                raise ValueError('Mobile selection differs from the canonical feature; review its context explicitly')
        inner=odd_workflow.preview(root,action,args,session)
    else:
        if action=='status':
            if set(args)!={'spec_id'}:raise ValueError('Choose the SDD specification')
            from .sdd import status
            return dict(status='specification_status',plan=None,review=dict(workflow=status(root,args['spec_id']),mobile=mobile))
        if action!='bind' or set(args)!={'spec_id','task_id','files'}:raise ValueError('Use dedicated SDD stages, then bind its approved mobile task')
        files=inputs.scope(root,args['files'],platforms);state=task_binding._state(root,args['spec_id'],args['task_id'])
        inner=dict(spec_id=args['spec_id'],task_id=args['task_id'],files=files,state=state,
                   mobile_scope=dict(platforms=platforms,framework=p['mobile_framework']))
    source=freeze_candidate(root,'pi-mobile-workflow',['aikya/docs/overview.md'],session_id=session)['id']
    plan=dict(input_data=data,session_id=session,methodology=p['methodology'],profile_hash=digest(p),language=resolve(root),
              source_revision=source,inner=inner)
    if len(encoded(plan))>30000:raise ValueError('Split mobile task metadata into smaller reviewed input')
    return dict(status='review_ready',plan=plan,review=dict(mobile=mobile,transition=inner,language=plan['language']))


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit mobile workflow confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'input_data','session_id','methodology','profile_hash','language','source_revision','inner'}:
        raise ValueError('Invalid mobile workflow preview')
    current=preview(root,plan['input_data'],plan['session_id'])
    if current.get('plan')!=plan:raise ValueError('Mobile workflow changed before effect')
    if plan['methodology']=='odd':result=odd_workflow.apply(root,plan['inner'],approved=True)
    else:
        inner=plan['inner'];result=task_binding.bind(root,plan['session_id'],inner['spec_id'],inner['task_id'],inner['files'],approved=True,mobile_scope=inner['mobile_scope'])
        if result['state']!=inner['state']:raise ValueError('SDD task changed while selecting mobile scope')
    p,_=inputs.selection(root,plan['input_data']['platforms'])
    if digest(p)!=plan['profile_hash'] or resolve(root)!=plan['language']:raise ValueError('Mobile profile/locale changed during metadata effect')
    return {**result,'mobile':current['review']['mobile']}
