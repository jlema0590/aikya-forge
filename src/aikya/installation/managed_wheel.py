"""Build a private Python core from a captured source snapshot without versioning stable."""
import hashlib
from pathlib import Path
import subprocess
import sys
from aikya.storage import write_new
from aikya.review.contracts import encoded
from aikya.installation.bootstrap.environment import verify_wheel
from . import build_sources,managed_versions

FILES=('setup.py','pyproject.toml','MANIFEST.in','VERSION','README.md','README.es.md','LICENSE','THIRD_PARTY_LICENSES.md',
       'requirements-agent-loop.txt','docs/AGENT_LOOP.md','docs/SECURITY_CONTROLS.md')


def build(source,destination,version):
    private_version=managed_versions.python_version(version)
    source=Path(source).resolve(strict=True);destination=Path(destination).absolute()
    if destination.exists() or destination.is_symlink():raise ValueError('Existing build output is preserved')
    raw=build_sources.capture(source,files=FILES,directories=('src',))
    fingerprints={name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}
    # Capture a coherent set. Never build a mixture of files changed during inspection.
    if build_sources.capture(source,files=FILES,directories=('src',))!=raw:raise ValueError('Builder source changed during snapshot')
    destination.mkdir(parents=True)
    stage=destination/'source';stage.mkdir()
    for relative,value in sorted(raw.items()):
        path=stage/relative;path.parent.mkdir(parents=True,exist_ok=True)
        write_new(path,(private_version+'\n').encode() if relative=='VERSION' else value,mode=0o600)
    write_new(destination/'source-inputs.json',encoded(dict(schema=1,runtime_version=version,python_version=private_version,files=fingerprints))+'\n',mode=0o600)
    command=[sys.executable,'-I','-B','-m','build','--wheel','--no-isolation','--outdir',str(destination/'dist')]
    process=subprocess.run(command,cwd=stage,env=build_sources.environment(destination/'home'),capture_output=True,timeout=300)
    write_new(destination/'build.log',process.stdout+process.stderr,mode=0o600)
    if process.returncode:raise ValueError('Private core wheel build failed; retained local build log requires review')
    wheels=list((destination/'dist').glob('*.whl'))
    if len(wheels)!=1:raise ValueError('Private build produced an unexpected wheel set')
    wheel=wheels[0];verify_wheel(wheel,private_version)
    return dict(wheel=str(wheel),runtime_version=version,python_version=private_version,sha256=hashlib.sha256(wheel.read_bytes()).hexdigest())
