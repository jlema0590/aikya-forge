"""One explicit data source resolver for project selection and inert global storage."""
from .skill_source import snapshot


def capture(source,root=None):
    if isinstance(source,str):return snapshot(source)
    if isinstance(source,dict) and source.get('kind')=='captured':
        from .skill_fetch import read
        return read(source,root)
    if not isinstance(source,dict) or set(source)!={'kind','name','source_hash'} or source['kind']!='global':
        raise ValueError('Select a local directory, reviewed capture or explicit pinned global version')
    from .skill_library import package
    data=package(source['name'],source['source_hash'])
    return {**data,'source':'global:'+source['name']+'@'+source['source_hash']}
