"""Reviewed binary-only parser recipes for the bundled CPython 3.13 runtime."""
import hashlib
from importlib.resources import files
from pathlib import Path
import re
from urllib.parse import urlsplit,unquote
from aikya.review.contracts import parse,hash_id
from .bootstrap import download,state
from .bootstrap.code_index import PINS
from .managed_runtime import _read
from .managed_inputs import TARGETS


def path():return Path(str(files('aikya')/'resources/terminal-parsers.json'))


def compatible(filename,target):
    if target not in TARGETS or not isinstance(filename,str):return False
    parts=filename.removesuffix('.whl').split('-')
    if len(parts)!=5 or not filename.endswith('.whl'):return False
    _,_,python,abi,platforms=parts
    if not (python=='cp313' and abi=='cp313' or abi=='abi3' and re.fullmatch(r'cp3[0-9]{1,2}',python)
            and 8<=int(python[3:])<=13):return False
    architecture='aarch64' if 'arm64' in target else 'x86_64'
    for platform in platforms.split('.'):
        if target.startswith('win32'):
            if platform==('win_arm64' if 'arm64' in target else 'win_amd64'):return True
        elif target.startswith('darwin'):
            match=re.fullmatch(r'macosx_([0-9]+)_([0-9]+)_(arm64|x86_64|universal2)',platform)
            arch='arm64' if 'arm64' in target else 'x86_64'
            if match and tuple(map(int,match.groups()[:2]))<=(13,5) and match[3] in (arch,'universal2'):return True
        elif target.endswith('-musl'):
            match=re.fullmatch(r'musllinux_([0-9]+)_([0-9]+)_'+architecture,platform)
            if match and tuple(map(int,match.groups()))<=(1,2):return True
        else:
            match=re.fullmatch(r'manylinux_([0-9]+)_([0-9]+)_'+architecture,platform)
            if match and tuple(map(int,match.groups()))<=(2,28):return True
            if platform in ('manylinux1_'+architecture,'manylinux2010_'+architecture,'manylinux2014_'+architecture):return True
    return False


def load(target,source=None):
    if target not in TARGETS:raise ValueError('Unsupported parser platform')
    value=parse(_read(state.safe(Path(source) if source is not None else path()),128000))
    if (not isinstance(value,dict) or set(value)!={'schema','python','platforms'} or value['schema']!=1 or value['python']!='3.13'
            or not isinstance(value['platforms'],dict) or set(value['platforms'])!=set(TARGETS)):
        raise ValueError('Invalid reviewed parser input catalog')
    selected=value['platforms'][target]
    if not isinstance(selected,dict) or set(selected)-set(PINS):raise ValueError('Unknown parser package')
    if selected and 'tree-sitter' not in selected:raise ValueError('Grammars require the pinned engine')
    for name,item in selected.items():
        if (not isinstance(item,dict) or set(item)!={'file','url','version','sha256'} or item['version']!=PINS[name]
                or not isinstance(item['url'],str) or not isinstance(item['file'],str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,240}\.whl',item['file'])
                or not item['file'].startswith(name.replace('-','_')+'-'+PINS[name]+'-') or not compatible(item['file'],target)):
            raise ValueError('Parser identity/ABI differs from reviewed pins')
        hash_id(item['sha256']);uri=urlsplit(item['url'])
        if (uri.scheme!='https' or uri.netloc!='files.pythonhosted.org' or uri.query or uri.fragment
                or unquote(uri.path).rsplit('/',1)[-1]!=item['file'] or not uri.path.startswith('/packages/')):
            raise ValueError('Parser origin differs from reviewed public PyPI data')
    return dict(wheels=selected,unavailable={name:'No reviewed compatible binary wheel for '+target for name in PINS if name not in selected})


def prepare(target,assets=None,*,fetch=False):
    from . import component_download
    recipe=load(target);result={};total=0
    for name,item in recipe['wheels'].items():
        if assets is not None:raw=_read(state.safe(Path(assets)/item['file']),10000000)
        elif fetch:raw=component_download.fetch(item['url'],10000000,hosts=frozenset({'files.pythonhosted.org'}))
        else:raise ValueError('Provide pinned parser wheel assets or explicitly fetch components')
        total+=len(raw)
        if total>70000000 or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Binary parser integrity/bounds failed')
        result[name]=raw
    return recipe,result


def install(recipe,raws,destination,purelib):
    from .managed_archives import extract
    from aikya.storage import write_new
    destination.mkdir(mode=0o700)
    for name,raw in raws.items():
        item=recipe['wheels'][name];wheel=destination/item['file'];write_new(wheel,raw,mode=0o600)
        extract(wheel,purelib,item['sha256'],'.',merge=True)


def probe_script(recipe):
    """Exercise declarations using the actual packaged bindings, not just metadata."""
    examples={'tree-sitter-java':('Sample.java','class Sample { int value() { return 1; } }'),
        'tree-sitter-javascript':('sample.js','class Sample { value() { return 1; } }'),
        'tree-sitter-typescript':('sample.ts','class Sample { value(): number { return 1; } }'),
        'tree-sitter-c-sharp':('Sample.cs','public class Sample { public int Value() => 1; }'),
        'tree-sitter-go':('sample.go','package sample\ntype Sample struct {}\nfunc Value() int { return 1 }\n'),
        'tree-sitter-dart':('sample.dart','class Sample { int value() => 1; }')}
    cases={name:value for name,value in examples.items() if name in recipe['wheels']}
    versions={name:PINS[name] for name in recipe['wheels']}
    return ('import importlib.metadata as m,json;from aikya.code_index.parsers.registry import parse_file;'
        +'versions='+repr(versions)+';assert all(m.version(n)==v for n,v in versions.items());'
        +'cases='+repr(cases)+';results={n:parse_file(p,s.encode()) for n,(p,s) in cases.items()};'
        +'assert all(r.status=="indexed" and r.symbols for r in results.values()), {n:(r.status,r.diagnostics) for n,r in results.items()};'
        +'print(json.dumps({n:dict(status=r.status,parser=r.parser_id,symbols=len(r.symbols)) for n,r in results.items()}))')
