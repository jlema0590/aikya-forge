"""Bounded source, profile and signed ownership inputs for native documentation."""
import hashlib
import re
from pathlib import Path
from aikya.code_index.policy import excluded,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.installation.profile import validated
from aikya.review import authentication
from aikya.review.contracts import read_record

REGISTRY='.aikya/pi/documentation/registry.json'
PENDING='.aikya/pi/documentation/pending.json'
ROLES={'overview':('aikya-analyze','overview'),'architecture':('aikya-arc-review','architecture'),
       'strategy':('aikya-tests','strategy'),'design':('aikya-arc-review','design'),
       'decision':('aikya-arc-review','decision'),'case':('aikya-tests','case'),'summary':('aikya-tests','summary')}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def profile(root):
    raw=read_record(root,'.harness/project-profile.json',65536)
    if not isinstance(raw,dict):raise ValueError('Invalid documentation profile')
    data=raw.get('decisions',raw)
    if not isinstance(data,dict) or data.get('methodology') not in ('odd','sdd'):raise ValueError('Explicit ODD/SDD profile required')
    return validated(data,root)


def signed(root,path):return authentication.verify(root,read_record(root,path,65536))


def registry(root):
    if not safe_file(root,REGISTRY).exists():return {}
    value=signed(root,REGISTRY)
    if not isinstance(value,dict) or set(value)!={'schema','project','pages'} or value['schema']!=1 or value['project']!=identity(root) or not isinstance(value['pages'],dict) or len(value['pages'])>200:
        raise ValueError('Unknown documentation ownership is preserved')
    return value['pages']


def sources(root,paths,*,allow_docs=False):
    if not isinstance(paths,list) or not 1<=len(paths)<=20 or any(not isinstance(p,str) or len(p)>240 for p in paths) or len(set(paths))!=len(paths):
        raise ValueError('Select 1–20 unique source paths')
    result={};total=0
    for name in paths:
        if (excluded(name) or (not allow_docs and name.startswith('aikya/docs/')) or any(p.lower() in ('.agents','.codex','.pi') for p in name.split('/'))
                or any(ord(c)<32 for c in name)):
            raise ValueError('Private or documentation path cannot be a source baseline')
        path=safe_file(root,name)
        raw=read_source(root,name,1000000) if path.exists() else None
        total+=len(raw) if raw is not None else 0
        if total>2000000:raise ValueError('Source packet exceeds 2 MB')
        result[name]=sha(raw) if raw is not None else None
    return result


def request_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'REQ-[0-9]{8}-[a-f0-9]{8}',value):raise ValueError('Expected REQ-YYYYMMDD-xxxxxxxx')
    return value


def baseline_path(value):return '.aikya/pi/documentation/baselines/'+request_id(value)+'.json'


def baseline(root,ident,session):
    value=signed(root,baseline_path(ident))
    if (not isinstance(value,dict) or set(value)!={'schema','project','change_id','session_id','sources'} or value['schema']!=1
            or value['project']!=identity(root) or value['change_id']!=ident or value['session_id']!=session or not isinstance(value['sources'],dict)):
        raise ValueError('Foreign documentation baseline')
    sources(root,list(value['sources']))
    if safe_file(root,'.aikya/pi/documentation/completed/'+ident+'.json').exists() or safe_file(root,'aikya/docs/changes/'+ident+'.md').exists():raise ValueError('Existing request record is preserved')
    return value
