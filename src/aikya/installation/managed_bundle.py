"""Build one native self-contained terminal from explicit official pinned components."""
import hashlib
from pathlib import Path
import subprocess
from aikya.review.contracts import encoded,parse
from aikya.storage import write_new
from . import build_sources,managed_archives,managed_inputs,managed_node,managed_payload,managed_distribution,managed_runtime,managed_versions,managed_wheel
from .bootstrap import download,state


def _components(recipe,assets,fetch):
    result={}
    for name in ('python','node'):
        item=recipe[name]
        if assets is not None:
            path=state.safe(Path(assets)/item['file'])
            raw=managed_runtime._read(path,256000000)
        elif fetch:
            raw=download.https_bytes(item['url'],256000000,hosts=frozenset(download.HOSTS)|{'nodejs.org'})
        else:raise ValueError('Provide verified component assets or explicitly select --fetch-components')
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Official component integrity checksum mismatch')
        result[name]=raw
    return result


def _run(command,cwd,environment,log):
    process=subprocess.run(command,cwd=cwd,env=environment,capture_output=True,timeout=60)
    write_new(log,process.stdout+process.stderr,mode=0o600)
    if process.returncode:raise ValueError('Bundled interpreter preflight failed; retained local build log requires review')
    return process.stdout.decode('utf8').strip()


def _licenses(payload):
    result=[]
    for path in sorted(payload.rglob('package.json')):
        if path.is_symlink():raise ValueError('Unreviewed package metadata link')
        record=parse(managed_runtime._read(state.safe(path),1000000))
        if not isinstance(record,dict):raise ValueError('Unknown Node package metadata')
        if isinstance(record.get('name'),str) and isinstance(record.get('version'),str):
            result.append(dict(path=path.relative_to(payload).as_posix(),name=record['name'],version=record['version'],license=record.get('license')))
        if len(result)>2000:raise ValueError('Package license inventory exceeds its bound')
    return result


def build(source,destination,version,*,assets=None,target=None,fetch_components=False):
    managed_versions.parts(version);target=target or managed_runtime.host_platform()
    if target!=managed_runtime.host_platform():raise ValueError('Build on the native target; cross-platform execution is not acceptance')
    recipe=managed_inputs.load(target);source=Path(source).resolve(strict=True);destination=state.safe(Path(destination).absolute())
    if destination.exists():raise ValueError('Existing terminal build output is preserved')
    components=_components(recipe,assets,fetch_components)
    destination.mkdir(parents=True);payload=destination/'payload';payload.mkdir();downloads=destination/'downloads';downloads.mkdir()
    for name,raw in components.items():
        path=downloads/recipe[name]['file'];write_new(path,raw,mode=0o600)
        managed_archives.extract(path,payload/name,recipe[name]['sha256'],recipe[name]['prefix'])
    core=managed_wheel.build(source,destination/'core',version)
    snapshot=managed_node.prepare(source/'packages/aikya-pi',payload/'runtime',version)
    python=payload/'python'/recipe['python']['executable'];node=payload/'node'/recipe['node']['executable']
    environment=build_sources.environment(destination/'home')
    py_version=_run([str(python),'-I','-B','-c','import platform;print(platform.python_version())'],payload,environment,destination/'python-version.log')
    node_version=_run([str(node),'--version'],payload,environment,destination/'node-version.log')
    if py_version!=recipe['versions']['python'] or node_version!='v'+recipe['versions']['node']:raise ValueError('Interpreter identity differs from its pinned recipe')
    purelib=Path(_run([str(python),'-I','-B','-c','import sysconfig;print(sysconfig.get_path("purelib"))'],payload,environment,destination/'purelib.log'))
    if not purelib.is_relative_to(payload/'python') or not state.safe(purelib).is_dir():raise ValueError('Interpreter site-packages escaped the staged payload')
    managed_archives.extract(core['wheel'],purelib,core['sha256'],'.',merge=True)
    links=managed_node.install(payload/'runtime',node,destination/'npm-home',destination/'npm-ci.log')
    installed=_run([str(python),'-I','-B','-c','from importlib.metadata import version;import aikya;print(version("aikya-harness"))'],payload,environment,destination/'core-import.log')
    if installed!=core['python_version']:raise ValueError('Installed core identity differs from private wheel metadata')
    _run([str(python),'-I','-B','-m','aikya','--help'],payload,environment,destination/'core-help.log')
    _run([str(node),'--experimental-strip-types',str(payload/'runtime/src/launcher.ts'),'--help'],payload,environment,destination/'terminal-help.log')
    provenance=dict(schema=1,version=version,platform=target,components={name:recipe[name] for name in ('python','node')},versions=recipe['versions'],
                    core=dict(sha256=core['sha256'],python_version=core['python_version'],source=parse((destination/'core/source-inputs.json').read_bytes())),
                    runtime=snapshot,links_flattened=links,node_packages=_licenses(payload),requirements=recipe['requirements'],
                    acceptance='Native build/import/help only; live provider and OS release gates remain separate')
    write_new(payload/'provenance.json',encoded(provenance)+'\n',mode=0o600)
    sealed=managed_payload.seal(payload,version=version,target=target,versions=recipe['versions'],
                               python=python.relative_to(payload).as_posix(),node=node.relative_to(payload).as_posix(),runtime='runtime')
    result=managed_distribution.finish(payload,destination,version,target)
    result.update(version=version,platform=target,payload=str(payload),files=sealed['files'],bytes=sealed['bytes'])
    write_new(destination/'result.json',encoded(result)+'\n',mode=0o600)
    return result
