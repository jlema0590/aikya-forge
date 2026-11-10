"""Canonical optional feature context for explicitly selected mobile platforms."""


def validated(profile,value):
    if not isinstance(value,dict) or set(value)!={'platforms','framework'}:raise ValueError('Mobile scope requires platforms and framework')
    mobile=profile.get('mobile');allowed={'android','ios'} if mobile=='both' else {mobile} if mobile in ('android','ios') else set()
    platforms=value['platforms'];framework=value['framework']
    if (profile.get('project_type','development')!='development' or not isinstance(platforms,list) or not 1<=len(platforms)<=2
            or any(not isinstance(p,str) for p in platforms) or len(set(platforms))!=len(platforms) or not set(platforms)<=allowed
            or framework not in ('flutter','react-native','native') or framework!=profile.get('mobile_framework')):
        raise ValueError('Mobile feature scope must match the recorded project platforms/framework')
    return dict(platforms=sorted(platforms),framework=framework)
