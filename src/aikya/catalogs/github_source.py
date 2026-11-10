"""Capture pinned public GitHub tree/blob data without checkout or client credentials."""
import hashlib
import re
import time
from urllib.parse import quote
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import URLError,HTTPError
from aikya.code_index.policy import excluded
from aikya.review.contracts import parse
from .skill_paths import validate as validate_paths


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,request,file,code,message,headers,newurl):return None


def repository(value):
    match=re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',value) if isinstance(value,str) else None
    if not match:raise ValueError('Choose a public HTTPS GitHub repository without credentials, query or redirect')
    owner,name=match.groups();name=name.removesuffix('.git')
    if owner in ('.','..') or name in ('','.','..'):raise ValueError('Invalid GitHub repository identity')
    return 'https://github.com/'+owner+'/'+name


def relative(value):
    if value=='.':return value
    if (not isinstance(value,str) or not 1<=len(value)<=240 or '\\' in value or ':' in value
            or any(p in ('','.','..') for p in value.split('/')) or len(value.split('/'))>12):
        raise ValueError('Choose an explicit contained GitHub skill path')
    return value


def object_id(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{40}',value):raise ValueError('Pin a complete lowercase Git commit/object SHA')
    return value


def ready(deadline,cancel):
    if cancel() or time.monotonic()>deadline:raise ValueError('GitHub source capture interrupted or timed out')


def read_url(url,limit,deadline,cancel,*,media_type='application/vnd.github+json'):
    ready(deadline,cancel)
    headers={'User-Agent':'Aikya-Forge','Accept':media_type,'X-GitHub-Api-Version':'2026-03-10'}
    try:
        with build_opener(NoRedirect()).open(Request(url,headers=headers),timeout=max(.1,min(10,deadline-time.monotonic()))) as response:
            if response.geturl()!=url:raise ValueError('Source origin changed; review the new source explicitly')
            length=response.headers.get('Content-Length')
            if length is not None and (not length.isdigit() or int(length)>limit):raise ValueError('GitHub source exceeds its download bound')
            raw=response.read(limit+1)
    except (HTTPError,URLError,TimeoutError) as error:raise ValueError('Public GitHub source data is unavailable') from error
    ready(deadline,cancel)
    if len(raw)>limit:raise ValueError('GitHub source exceeds its download bound')
    return raw


def _json(url,deadline,cancel):
    value=parse(read_url(url,1000000,deadline,cancel))
    if not isinstance(value,dict):raise ValueError('Invalid GitHub object response')
    return value


def _tree(api,sha,deadline,cancel,recursive=False,max_nodes=160):
    value=_json(api+'/git/trees/'+object_id(sha)+('?recursive=1' if recursive else ''),deadline,cancel)
    if (value.get('sha')!=sha or value.get('truncated') is not False or not isinstance(value.get('tree'),list)
            or len(value['tree'])>(max_nodes if recursive else 2000)):raise ValueError('Incomplete or excessive GitHub tree')
    return value['tree']


def _selected(api,tree,path,deadline,cancel):
    if path=='.':return tree
    for part in path.split('/'):
        ready(deadline,cancel);rows=_tree(api,tree,deadline,cancel)
        matches=[r for r in rows if isinstance(r,dict) and r.get('path')==part]
        if len(matches)!=1 or matches[0].get('mode')!='040000' or matches[0].get('type')!='tree':
            raise ValueError('Selected source is missing, aliased or not a regular directory')
        tree=object_id(matches[0].get('sha'))
    return tree


def _members(rows,max_files=80,max_nodes=160):
    names=set();files=[];total=0
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid GitHub tree member')
        name=relative(row.get('path'))
        if name=='.' or len(name)>160 or excluded(name) or name.casefold() in names:raise ValueError('Unsafe or duplicate skill member')
        names.add(name.casefold());object_id(row.get('sha'))
        if row.get('type')=='tree' and row.get('mode')=='040000':continue
        size=row.get('size')
        if (row.get('type')!='blob' or row.get('mode') not in ('100644','100755')
                or type(size) is not int or not 0<=size<=1000000):raise ValueError('Only bounded regular skill data is supported')
        total+=size;files.append(row)
    if len(files)>max_files or total>5000000 or not any(r['path']=='SKILL.md' for r in files):raise ValueError('Skill package exceeds its data budget or lacks SKILL.md')
    validate_paths([row['path'] for row in files],max_files=max_files,max_nodes=max_nodes)
    return files


def capture(repo,path,commit,*,cancel=lambda:False,compatibility='native'):
    if compatibility not in ('native','legacy'):raise ValueError('Unknown skill capture contract')
    max_files,max_nodes=(80,160) if compatibility=='native' else (500,1000)
    repo=repository(repo);path=relative(path);object_id(commit);deadline=time.monotonic()+60;ready(deadline,cancel)
    slug=repo.removeprefix('https://github.com/');api='https://api.github.com/repos/'+slug
    value=_json(api+'/git/commits/'+commit,deadline,cancel)
    if value.get('sha')!=commit or not isinstance(value.get('tree'),dict):raise ValueError('Pinned source commit changed')
    tree=_selected(api,object_id(value['tree'].get('sha')),path,deadline,cancel)
    rows=_members(_tree(api,tree,deadline,cancel,recursive=True,max_nodes=max_nodes),max_files,max_nodes);raws={};prefix='' if path=='.' else path+'/'
    for row in rows:
        ready(deadline,cancel);name=row['path'];url='https://raw.githubusercontent.com/'+slug+'/'+commit+'/'+quote(prefix+name,safe='/.-_')
        raw=read_url(url,row['size'],deadline,cancel,media_type='application/octet-stream')
        if len(raw)!=row['size'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['sha']:
            raise ValueError('Captured skill bytes differ from the pinned Git object')
        raws[name]=raw
    return dict(repo=repo,path=path,commit=commit,tree=tree,files=raws,modes={row['path']:row['mode'] for row in rows},bytes=sum(map(len,raws.values())),execution='none')



def resolve(repo,ref=None,*,cancel=lambda:False):
    """Resolve selected metadata once; subsequent content capture requires the returned SHA."""
    repo=repository(repo);api='https://api.github.com/repos/'+repo.removeprefix('https://github.com/')
    deadline=time.monotonic()+30;ready(deadline,cancel)
    if ref is None:
        branch=_json(api,deadline,cancel).get('default_branch')
        if not isinstance(branch,str):raise ValueError('Repository default branch is unavailable')
        ref='heads/'+branch
    if (not isinstance(ref,str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._/-]{0,120}',ref)
            or '..' in ref or ref.endswith('.lock')):raise ValueError('Choose a valid source reference')
    raw=read_url(api+'/commits/'+quote(ref,safe=''),128,deadline,cancel,media_type='application/vnd.github.sha')
    commit=object_id(raw.decode('ascii').strip())
    return dict(repo=repo,ref=ref,commit=commit,execution='none')
