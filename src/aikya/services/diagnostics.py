"""Bounded host diagnostics; no inference, SDK execution or project writes."""
import hashlib
import platform
from pathlib import Path
import shutil
import sys
import tempfile
from aikya.code_index.policy import project_root,read_source,excluded
from aikya.core.checkpoints import safe_file
from aikya.installation.profile import validated
from aikya.installation.requirements import required_tools
from aikya.review.contracts import parse,digest
from aikya.quality import source

PROFILE='.harness/project-profile.json'
EXCEPTIONS='.aikya/code-quality-exceptions.json'


def _profile(root):
    try:
        if not safe_file(root,PROFILE).exists():return None,'unconfigured'
        raw=parse(read_source(root,PROFILE,65536))
        if not isinstance(raw,dict):raise ValueError('Invalid profile')
        data=raw.get('decisions',raw)
        if not isinstance(data,dict) or data.get('methodology') not in ('odd','sdd'):raise ValueError('Explicit methodology required')
        return validated(data,root),'configured'
    except (ValueError,OSError,TypeError,UnicodeError,RecursionError):return None,'invalid'


def doctor(root):
    root=project_root(root);profile,state=_profile(root);checks=[]
    for tool in required_tools(profile) if profile else ['python3','git']:
        command={'docker-compose':'docker','opentofu':'tofu'}.get(tool,tool)
        found='not_checked' if tool=='android-sdk' else 'found' if shutil.which(command) else 'missing'
        if tool=='xcodebuild' and platform.system()!='Darwin':found='unsupported_host'
        checks.append(dict(tool=tool,presence=found,version=None,compatibility='not_verified',
                           detail='Parent command only; subcommand not executed' if tool=='docker-compose' else ''))
    return dict(profile=dict(status=state,methodology=profile['methodology'] if profile else None,
                             project_type=profile['project_type'] if profile else None),
                host=dict(platform=platform.system(),python=platform.python_version(),executable='current_python',
                          python_supported=sys.version_info>=(3,10)),toolchains=checks,ready=None,
                compatibility='not_verified',effects='none',inference='none',
                next_step='Use explicit approved checks to verify versions, builds and framework compatibility. No SDK command was executed.')


def _inputs(root,paths):
    if (not isinstance(paths,list) or not 1<=len(paths)<=20
            or any(not isinstance(p,str) or not 1<=len(p)<=240 for p in paths) or len(set(paths))!=len(paths)):
        raise ValueError('Select 1–20 unique relative source files')
    result={};total=0
    for path in paths:
        if excluded(path) or Path(path).suffix.lower() not in source.SOURCE_SUFFIXES:
            raise ValueError('Private or unsupported quality path')
        raw=read_source(root,path,1000000);total+=len(raw)
        if total>2000000:raise ValueError('Quality packet exceeds 2 MB')
        result[path]=raw
    return result


def _finding(item):
    value={key:item[key] for key in ('path','line','code','function') if key in item}
    if 'function' in value:value['function']=value['function'][:100]
    if 'message' in item:value['message']=item['message'][:400]
    if 'reason' in item:value['reason']=item['reason'][:400]
    if 'locations' in item:
        value['locations']=[{**loc,'function':loc['function'][:100]} for loc in item['locations'][:3]]
        value['locations_total']=len(item['locations'])
    return value


def quality(root,paths):
    root=project_root(root);inputs=_inputs(root,paths)
    exception=read_source(root,EXCEPTIONS,100000) if safe_file(root,EXCEPTIONS).exists() else None
    # Inspect the captured bytes with the existing engine, never re-open mutable inputs.
    with tempfile.TemporaryDirectory(prefix='aikya-quality-') as folder:
        stage=Path(folder)
        for name,raw in {**inputs,**({EXCEPTIONS:exception} if exception is not None else {})}.items():
            path=safe_file(stage,name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        report=source.inspect_paths(stage,list(inputs))
    hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in inputs.items()}
    errors=report['errors'][:20];warnings=report['warnings'][:20-len(errors)]
    return dict(status='issues_found' if report['errors'] or report['warnings'] else 'no_static_findings',
                files=report['files'],hashes=hashes,scope_revision=digest(dict(files=hashes,exceptions=hashlib.sha256(exception).hexdigest() if exception is not None else None)),
                coverage={name:'python_ast_and_physical_lines' if Path(name).suffix.lower() in ('.py','.pyi') else 'physical_lines_only' for name in inputs},
                errors=[_finding(item) for item in errors],warnings=[_finding(item) for item in warnings],
                error_count=len(report['errors']),warning_count=len(report['warnings']),
                truncated=len(errors)+len(warnings)<len(report['errors'])+len(report['warnings']) or any(len(item.get('locations',[]))>3 for item in warnings),
                security='not_run',tests='not_run',effects='none',inference='none',validity='captured_bytes_only')
