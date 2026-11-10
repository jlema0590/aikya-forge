"""Local memory maintenance reuses existing project policy and ownership checks."""
from aikya.code_index.policy import load_policy
from aikya.code_index.sync import sync
from aikya.memory.viewer.export import export_view


def after_write(root):
    try:
        policy=load_policy(root)
        if not policy.enabled:return dict(status='disabled')
        result=sync(root)
        exported=export_view(root,refresh=False) if policy.auto_export else None
        return dict(status='updated',generation=result.generation,index_status=result.status,
                    html_status=exported.status if exported else 'disabled')
    except (ValueError,OSError,UnicodeError):
        # The source write already happened. Report degradation without suggesting replay.
        return dict(status='degraded',diagnostic='Memory maintenance unavailable; preserve source and owned artifacts')


def session_event(root,session,event):
    """Own only this Pi lease; reuse the existing zero-inference project observer."""
    from aikya.code_index.policy import project_root
    from aikya.code_index.hooks import process_event,active_sessions
    from aikya.review.contracts import identifier
    root=project_root(root);identifier(session)
    hooks={'start':'SessionStart','activity':'UserPromptSubmit','end':'SessionEnd'}
    if event not in hooks:raise ValueError('Unknown memory lifecycle event')
    policy=load_policy(root)
    if event!='end' and (not policy.enabled or not policy.watch):return dict(status='disabled')
    process_event(root,dict(hook_event_name=hooks[event],session_id=session))
    return dict(status='lease_released' if event=='end' else 'observing',active=active_sessions(root))
