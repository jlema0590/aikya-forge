"""Explicit check applicability; process success is never a substitute for tests."""
from pathlib import Path
from aikya.code_index.policy import CODE_SUFFIXES

KINDS=('behavior','documentation','configuration','infrastructure','refactor')
CONFIG_SUFFIXES=frozenset(('.json','.yaml','.yml','.toml','.ini','.cfg','.conf','.xml','.properties'))
INFRA_SUFFIXES=CONFIG_SUFFIXES|frozenset(('.tf','.tfvars','.hcl','.tpl'))


def classify(scope,definitions,tdd_paths,not_applicable,change_kind,baseline_paths):
    """Return only new policy fields; omitted classification preserves legacy identity."""
    if change_kind is not None and change_kind not in KINDS:
        raise ValueError('Unknown change classification')
    if baseline_paths is not None and change_kind!='refactor':
        raise ValueError('Positive baseline paths require explicit refactor classification')
    types={d['name']:'process' if d['report_format']=='process' else 'test' for d in definitions}
    fields={}
    if change_kind is not None or 'process' in types.values():fields['check_types']=types
    first=definitions[0]['name']
    if change_kind=='refactor':
        if tdd_paths or not baseline_paths or not not_applicable or types[first]!='test':
            raise ValueError('Refactoring requires a positive test baseline and non-applicability reason')
        fields['baseline']=dict(check=first,paths=baseline_paths)
        return fields
    if change_kind in ('documentation','configuration','infrastructure'):
        if tdd_paths or not not_applicable:raise ValueError('Nonbehavior changes require an explicit reason without TDD paths')
        allowed={'.md','.rst','.txt'} if change_kind=='documentation' else (
            CONFIG_SUFFIXES if change_kind=='configuration' else INFRA_SUFFIXES)
        if any(Path(p).suffix.lower() not in allowed for p in scope):
            raise ValueError('Source scope does not support the declared nonbehavior classification')
        return fields
    if tdd_paths:
        if not_applicable is not None or types[first]!='test':
            raise ValueError('Executed TDD requires a test check without non-applicability')
        fields['tdd']=dict(check=first,paths=tdd_paths)
    elif change_kind=='behavior' or any(Path(p).suffix.lower() in CODE_SUFFIXES for p in scope) or not not_applicable:
        raise ValueError('Code changes require explicit TDD test paths; documentation requires a reason')
    return fields
