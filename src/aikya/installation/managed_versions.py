"""Canonical Forge identities with explicit compatibility for retained v8 payloads."""
import re

PATTERN=re.compile(r'(0|8)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-(alpha|beta|rc)\.(0|[1-9][0-9]*))?')


def parts(value):
    match=PATTERN.fullmatch(value) if isinstance(value,str) else None
    if match is None:raise ValueError('Select a Forge 0.x release or a retained v8 alpha/beta/rc identity')
    major,minor,patch,kind,number=match.groups()
    return int(major),int(minor),int(patch),kind,int(number) if number is not None else None


def python_version(value):
    major,minor,patch,kind,number=parts(value);base=f'{major}.{minor}.{patch}'
    return base+({'alpha':'a','beta':'b','rc':'rc'}[kind]+str(number) if kind else '')


def order(value):
    major,minor,patch,kind,number=parts(value)
    return major,minor,patch,{'alpha':0,'beta':1,'rc':2,None:3}[kind],number or 0

