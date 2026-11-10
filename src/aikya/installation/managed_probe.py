"""Fixed native preflight, without providers, model prompts or project initialization."""
from pathlib import Path
import subprocess
from .build_sources import environment
from .managed_versions import python_version


def check(value,home):
    env=environment(home);folder=Path(value['runtime']).parent
    commands=([value['python'],'-I','-B','-c','from importlib.metadata import version;import aikya;print(version("aikya-harness"))'],
              [value['node'],'--experimental-strip-types',str(Path(value['runtime'])/'src/launcher.ts'),'--help'])
    for index,command in enumerate(commands):
        result=subprocess.run(command,cwd=folder,env=env,capture_output=True,text=True,timeout=60)
        if result.returncode or (index==0 and result.stdout.strip()!=python_version(value['version'])):raise ValueError('Native payload preflight failed; previous active terminal is retained')
    return dict(status='passed')
