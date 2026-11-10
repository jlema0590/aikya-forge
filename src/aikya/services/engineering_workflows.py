"""Bounded native engineering facades over existing document and workflow engines."""
from aikya.code_index.policy import project_root
from aikya.review.contracts import encoded,digest,identifier
from . import architecture_findings,documentation


def _assemble(root,command,data,session):
    if command=='aikya-mobile-feature':
        from .mobile_workflow import preview
        return preview(root,data,session)
    if command=='aikya-arc-review':
        prepared=architecture_findings.prepare(root,data)
    elif command=='aikya-bugfix':
        from .bug_evidence import prepare
        prepared=prepare(root,data,session)
    else:raise ValueError('Unknown native engineering workflow')
    if 'plan' in prepared:return prepared
    args=dict(sources=list(prepared['sources']))
    if command=='aikya-bugfix':args.update(action='append',payload=prepared['payload'])
    else:args.update(action='write',documents=prepared['documents'])
    result=documentation.preview(root,'aikya-bugfix' if command=='aikya-bugfix' else 'aikya-docs',args,session)
    if result.get('plan') is not None and result['review'].get('sources')!=prepared['sources']:
        raise ValueError('Source changed between excerpt capture and document preparation')
    if 'bug_evidence' in prepared and result.get('plan') is not None:result['review']['bug_evidence']=prepared['bug_evidence']
    return result


def preview(root,command,input_data,session_id):
    root=project_root(root);identifier(session_id)
    if not isinstance(input_data,dict) or len(encoded(input_data))>8000:raise ValueError('Bounded explicit engineering input required')
    result=_assemble(root,command,input_data,session_id)
    if result.get('plan') is None:return result
    plan=dict(command=command,input_data=input_data,session_id=session_id,inner_plan_hash=digest(result['plan']))
    if len(encoded(plan))>12000:raise ValueError('Engineering confirmation exceeds its request bound')
    return {**result,'plan':plan}


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native engineering confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'command','input_data','session_id','inner_plan_hash'}:raise ValueError('Invalid engineering preview')
    current=preview(root,plan['command'],plan['input_data'],plan['session_id'])
    if current.get('plan')!=plan:raise ValueError('Engineering preview changed')
    prepared=_assemble(root,plan['command'],plan['input_data'],plan['session_id'])
    if prepared.get('plan') is None or digest(prepared['plan'])!=plan['inner_plan_hash']:raise ValueError('Engineering input changed before effect')
    if plan['command']=='aikya-mobile-feature':
        from .mobile_workflow import apply
        return apply(root,prepared['plan'],approved=True)
    return documentation.apply(root,prepared['plan'],approved=True)
