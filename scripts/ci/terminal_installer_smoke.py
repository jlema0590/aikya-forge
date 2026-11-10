"""Exercise a verified native installer in a new isolated directory, without inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from aikya.installation.bootstrap import download, state
from aikya.installation.build_sources import environment
from aikya.installation.managed_runtime import host_platform, _read
from aikya.installation.managed_versions import parts
from aikya.storage import write_new


def _inputs(assets):
    record=json.loads(_read(state.safe(assets/'terminal-bootstrap.json'),128000))
    version=record['version'];parts(version);target=host_platform()
    selected=record['platforms'].get(target)
    if not selected:raise ValueError('No native installer for the current platform')
    asset='aikya-terminal-'+version+'-'+target+('.zip' if os.name=='nt' else '.tar.gz')
    if selected['asset']!=asset:raise ValueError('Unexpected native installer asset')
    hashes=download.parse_checksums(_read(state.safe(assets/'SHA256SUMS'),128000))
    entries=record['entries']
    allowed={'install.ps1','install.cmd'} if os.name=='nt' else {'install.sh','install.command'}
    if not entries or set(entries)-allowed:raise ValueError('Unknown native installer entry')
    for name in (asset,'terminal-bootstrap.json',*entries):
        raw=_read(state.safe(assets/name),256000000)
        digest=hashlib.sha256(raw).hexdigest()
        if hashes.get(name)!=digest or (name in entries and entries[name]!=digest):
            raise ValueError('Native installer integrity checksum mismatch: '+name)
    if hashes[asset]!=selected['sha256']:raise ValueError('Native payload checksum differs from its entry')
    return version


def _step(name,command,target,env):
    process=subprocess.run(list(map(str,command)),cwd=target/'project',env=env,capture_output=True,text=True,encoding='utf8',timeout=600)
    record=dict(command=list(map(str,command)),exit_code=process.returncode,stdout=process.stdout,stderr=process.stderr)
    write_new(target/'logs'/(name+'.json'),json.dumps(record,ensure_ascii=False,indent=2)+'\n',mode=0o600)
    if process.returncode:raise ValueError(name+' failed with exit '+str(process.returncode)+'; see '+str(target/'logs'))
    return process.stdout


def _json(raw):
    try:return json.loads(raw.strip().splitlines()[-1])
    except (ValueError,IndexError) as error:raise ValueError('Native command did not return an observed JSON result') from error


def run(assets,target):
    assets=state.safe(Path(assets).absolute());target=state.safe(Path(target).absolute())
    if target.exists():raise ValueError('Existing smoke output is preserved')
    version=_inputs(assets)
    target.mkdir(parents=True);(target/'project').mkdir();(target/'logs').mkdir()
    env=environment(target/'home');application=target/'application';env['AIKYA_INSTALL_ROOT']=str(application)
    if os.name=='nt':
        entry=['powershell.exe','-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',assets/'install.ps1','-OfflineDir',assets,'-NoPath']
        preview=[*entry,'-DryRun'];suffix='.exe'
    else:
        entry=['/bin/sh',assets/'install.sh','--offline-dir',assets,'--no-path']
        preview=[*entry,'--dry-run'];suffix=''
    checked=_json(_step('preview',preview,target,env))
    if checked.get('writes') is not False or checked.get('network') is not False or application.exists():raise ValueError('preview changed application state')
    installed=_json(_step('install',entry,target,env))
    if installed.get('status')!='installed':raise ValueError('install did not create a new native activation')
    _step('help',[application/'bin'/('aikya'+suffix),'--help'],target,env)
    manager=application/'bin'/('aikya-manage'+suffix)
    doctor=_json(_step('doctor',[manager,'doctor'],target,env))
    if doctor.get('installed') is not True or doctor.get('pending') is not False or doctor.get('errors')!=[]:raise ValueError('doctor did not confirm a healthy installation')
    write_new(application/'owner-data.txt','Preserve owner data.\n',mode=0o600)
    repeated=_json(_step('reinstall',entry,target,env))
    if repeated.get('status')!='up-to-date':raise ValueError('reinstall did not preserve the exact activation')
    uninstall=[*entry,'-Action','uninstall'] if os.name=='nt' else [manager,'uninstall','--yes']
    removed=_json(_step('uninstall',uninstall,target,env))
    if removed.get('status')!='uninstalled' or (application/'terminal/current.json').exists():raise ValueError('uninstall left an active terminal')
    if (application/'owner-data.txt').read_text()!='Preserve owner data.\n' or list((target/'project').iterdir()):raise ValueError('Installation lifecycle changed owner/project data')
    return dict(status='passed',version=version,platform=host_platform(),steps=['preview','install','help','doctor','reinstall','uninstall'],target=str(target))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--target',type=Path,required=True,help='New isolated directory; existing paths are refused')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():parser.error('Existing smoke report is preserved')
    try:result=run(args.assets,args.target)
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:result=dict(status='failed',error=str(error),target=str(args.target))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    write_new(args.output,json.dumps(result,indent=2)+'\n',mode=0o600)
    print(json.dumps(result));return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
