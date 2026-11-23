"""Canonical selected-task intent and explicitly reviewed run/security limits."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file
from aikya.documentation.layout import index_paths
from aikya.review.candidates import load_candidate,is_current
from aikya.review.contracts import digest,dossier
from aikya.review.executor import _guard_incomplete
from . import checks,odd_binding,task_binding,batch_records
from .documentation_inputs import profile,PENDING as DOCUMENT_PENDING


def limits(value=None):
    value=dict(calls=6,seconds=300,corrections=1) if value is None else value
    if (not isinstance(value,dict) or set(value)!={'calls','seconds','corrections'}
            or any(type(v) is not int for v in value.values()) or not 1<=value['calls']<=20
            or not 10<=value['seconds']<=600 or not 0<=value['corrections']<=1):
        raise ValueError('Review bounded run calls (1–20), seconds (10–600) and corrections (0–1)')
    return dict(value)


def security(value,names):
    if not isinstance(value,dict) or set(value)!={'checks','not_applicable'}:raise ValueError('Explicit security applicability required')
    selected=value['checks'];reason=value['not_applicable']
    if (not isinstance(selected,list) or any(not isinstance(n,str) for n in selected)
            or len(set(selected))!=len(selected) or set(selected)-set(names)):
        raise ValueError('Choose frozen check names for security')
    if selected:
        if reason is not None:raise ValueError('Choose security checks or an explicit non-applicability reason')
    elif not isinstance(reason,str) or not 20<=len(reason.strip())<=500 or '\x00' in reason:
        raise ValueError('Review why security checks do not apply to this bounded task')
    return dict(checks=list(selected),not_applicable=reason)


def selected(root,candidate,session_id):
    method=profile(root)['methodology']
    if method=='odd':
        value,revision=odd_binding.current(root,session_id)
        task_intent=value['intent'];ident=dict(feature_id=value['feature_id'],task_id=value['task_id'])
        names=value['checks']
    else:
        value,revision=task_binding.current(root,session_id)
        task_intent=task_binding.intent(root,value['spec_id'],value['task_id'])
        ident=dict(spec_id=value['spec_id'],task_id=value['task_id']);names=candidate['policy']['checks']
    actual=checks.bound_intent(root,candidate)
    if (candidate['scope']!=value['files'] or candidate['policy'].get('workflow_revision')!=revision
            or candidate['policy']['checks']!=names or actual['objective']!=task_intent['objective']
            or actual['acceptance']!=task_intent['acceptance']):raise ValueError('Frozen task intent, scope, checks and selection must agree')
    return dict(methodology=method,**ident,workflow_revision=revision,files=value['files'],checks=list(names),intent=task_intent)


def current(root,change_id,session_id,*,require_current=True):
    root=project_root(root);index_paths(root);batch_records.guard(root)
    if safe_file(root,DOCUMENT_PENDING).exists():raise ValueError('Reconcile pending documentation first')
    candidate=load_candidate(root,change_id);registry=checks._registry(root,change_id)
    if (candidate['session_id']!=session_id or registry['session_id']!=session_id or registry['candidate']!=candidate['id']
            or candidate['policy'].get('native_observations') is not True or (require_current and not is_current(root,candidate))):
        raise ValueError('Current native author candidate required')
    folder=safe_file(root,dossier(change_id)+'/checks/.probe').parent
    for name in candidate['policy']['checks']:_guard_incomplete(root,folder,name)
    return candidate,selected(root,candidate,session_id)
