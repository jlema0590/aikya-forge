"""Static failure categories and first-party stages, never exception content."""
import re


def describe(error):
    if isinstance(error,PermissionError):category='filesystem_permission'
    elif isinstance(error,FileExistsError):category='filesystem_conflict'
    elif isinstance(error,OSError):category='filesystem_unavailable'
    elif isinstance(error,(TypeError,RecursionError)):category='invalid_request'
    else:category='policy_refused'
    stage=None;trace=error.__traceback__;count=0
    while trace is not None and count<64:
        module=trace.tb_frame.f_globals.get('__name__','');function=trace.tb_frame.f_code.co_name
        if isinstance(module,str) and module.startswith('aikya.'):
            candidate=module+'.'+function
            if re.fullmatch(r'[A-Za-z0-9_.]{1,240}',candidate):stage=candidate
        count+=1;trace=trace.tb_next
    return dict(category=category,stage=stage)
