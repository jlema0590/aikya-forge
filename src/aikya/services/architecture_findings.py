"""Explicit static interpretations anchored to captured source; never runtime proof."""
from aikya.code_index.policy import read_source
from aikya.review.contracts import encoded
from aikya.documentation.language import resolve
from .documentation_inputs import profile,sources,sha
from .bootstrap_plans import text
from .bridge import scoped_context


def prepare(root,data):
    profile(root);action=data.get('action');paths=data.get('paths');hashes=sources(root,paths)
    if any(value is None for value in hashes.values()):raise ValueError('Architecture sources must exist')
    if action=='inspect':
        if set(data)!={'action','paths','query','max_chars'}:raise ValueError('Choose explicit paths, query and bounded context')
        packet=scoped_context(root,{key:data[key] for key in ('paths','query','max_chars')})
        return dict(status='context_ready',plan=None,review=dict(sources=hashes,context=packet,runtime='not_verified',inference='none'))
    if action!='record' or set(data)!={'action','title','paths','findings'}:raise ValueError('Choose inspect or record with explicit source findings')
    title=text(data['title'],'architecture review title',180)
    if '\n' in title or '\r' in title:raise ValueError('Review title requires one line')
    findings=data['findings']
    if not isinstance(findings,list) or not 1<=len(findings)<=20:raise ValueError('Select 1–20 anchored interpretations')
    captured={}
    for path,expected in hashes.items():
        raw=read_source(root,path,1000000)
        if sha(raw)!=expected:raise ValueError('Architecture source changed during capture')
        captured[path]=raw.decode('utf8').splitlines()
    rows=[]
    for item in findings:
        if not isinstance(item,dict) or set(item)!={'path','line','end_line','quote','kind','severity','message'}:raise ValueError('Finding requires source lines/quote, kind/severity and message')
        path=item['path'];start=item['line'];end=item['end_line']
        if (path not in captured or type(start) is not int or type(end) is not int or not 1<=start<=end<=len(captured[path]) or end-start>=20):raise ValueError('Finding must reference selected existing source lines')
        quote=text(item['quote'],'source excerpt',2000)
        if quote!='\n'.join(captured[path][start-1:end]).strip():raise ValueError('Finding excerpt differs from the selected source')
        if item['kind'] not in ('observation','hypothesis','recommendation') or item['severity'] not in ('info','warning','critical'):
            raise ValueError('Static interpretation kind/severity required')
        rows.append({**item,'quote':quote,'message':text(item['message'],'finding interpretation',500),'sha256':hashes[path]})
    if sources(root,paths)!=hashes:raise ValueError('Architecture source changed before composition')
    es=resolve(root)=='es'
    note=('Interpretaciones aportadas sobre fragmentos verificados. No se ha verificado el comportamiento en ejecución ni ejecutado pruebas.' if es else
          'Supplied interpretations of verified excerpts. Runtime behavior is not verified and tests have not been executed.')
    body=note+'\n\n```json\n'+encoded(dict(findings=rows,sources=hashes,runtime='not_verified',tests='not_run'))+'\n```'
    return dict(sources=hashes,documents=[dict(document='architecture',payload=dict(title=title,sections={'11-known-problems-and-direction':body}))])
