"""Known generator recipes and verified, bounded registry archives; no shell input."""
import base64
import hashlib
import os
from pathlib import Path
import re
import shutil
import urllib.parse
import urllib.request
from aikya.review.contracts import digest,parse
from aikya.review.definitions import selected_environment,_executable_hash
from .bootstrap_plans import scaffold_plan

PACKAGES={'create-next-app':'create-next-app','@nestjs/cli':'nest','create-vite':'create-vite','create-expo-app':'create-expo-app'}


def tool(name):
    env=selected_environment();value=shutil.which(name,path=env.get('PATH',os.defpath))
    if not value:raise ValueError('Generator SDK is not installed')
    path=Path(value).resolve()
    return dict(path=str(path),sha256=_executable_hash(path),environment=digest(env))


def recipe(profile,generator,version=None):
    if profile['project_type']!='development' or profile['mode']!='new':raise ValueError('Scaffolding requires a new development project')
    row=next((r for r in scaffold_plan(profile)['generators'] if r['id']==generator),None)
    if row is None:raise ValueError('Choose a known generator')
    name=profile['name']
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,79}',name):
        raise ValueError('Review a generator-compatible project name (1–80 letters, digits, dots, underscores or hyphens)')
    command=row['command'];package=None
    if any('@latest' in token for token in command):
        if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*)?',version):
            raise ValueError('Resolve an explicit generator version; latest is not executable')
        token=next(t for t in command if '@latest' in t).removesuffix('@latest')
        package='create-vite' if token=='vite' else token
        if package not in PACKAGES:raise ValueError('Unknown registry generator')
        if command[:2]==['npm','create']:
            args=command[3:];args.remove('--')
        else:args=command[2:]
        return dict(id=generator,tool=tool('npm'),package=package,version=version,bin=PACKAGES[package],args=args,
                    workspace_name=re.sub(r'[^a-z0-9-]','-',name.lower()) if row['destination']=='.' else None,
                    destination=row['destination'],metadata='https://registry.npmjs.org/'+urllib.parse.quote(package,safe='')+'/'+version)
    if version is not None:raise ValueError('Local SDK selection is bound to executable bytes')
    if command[0] not in ('dotnet','flutter'):raise ValueError('Unknown local generator')
    names=['--name',name] if command[0]=='dotnet' else ['--project-name',re.sub(r'[^a-z0-9_]','_',name.lower())]
    return dict(id=generator,tool=tool(command[0]),package=None,version=None,bin=None,args=[*command[1:],*names],
                workspace_name=None,destination=row['destination'],metadata=None)


def fetch(url,limit):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!='registry.npmjs.org' or parsed.fragment or parsed.query or parsed.username:
        raise ValueError('Only the approved HTTPS registry is supported')
    request=urllib.request.Request(url,headers={'User-Agent':'Aikya/8 generator resolver','Accept':'application/json, application/octet-stream'})
    with urllib.request.urlopen(request,timeout=10) as response:
        if response.geturl()!=url:raise ValueError('Generator registry redirect requires a new reviewed source')
        raw=response.read(limit+1)
    if len(raw)>limit:raise ValueError('Generator download exceeds its bound')
    return raw


def download(value):
    data=parse(fetch(value['metadata'],1000000))
    if not isinstance(data,dict) or data.get('name')!=value['package'] or data.get('version')!=value['version']:
        raise ValueError('Registry package identity changed')
    dist=data.get('dist')
    if not isinstance(dist,dict):raise ValueError('Generator registry distribution metadata is missing')
    url=dist.get('tarball');integrity=dist.get('integrity')
    if not isinstance(url,str) or not isinstance(integrity,str) or not integrity.startswith('sha512-'):
        raise ValueError('Generator requires a SHA-512 registry integrity value')
    raw=fetch(url,10000000)
    expected='sha512-'+base64.b64encode(hashlib.sha512(raw).digest()).decode()
    if integrity!=expected:raise ValueError('Generator archive integrity mismatch')
    return raw,dict(name=value['package'],version=value['version'],tarball=url,integrity=integrity,sha256=hashlib.sha256(raw).hexdigest())


def argv(value,archive):
    if value['package'] is None:return [value['tool']['path'],*value['args']]
    return [value['tool']['path'],'exec','--yes','--ignore-scripts','--package='+str(archive),'--',value['bin'],*value['args']]
