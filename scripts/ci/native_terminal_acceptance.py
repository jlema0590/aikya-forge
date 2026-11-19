"""Isolated native install/update/rollback and installed memory acceptance; no v7 adoption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from aikya.installation import managed_runtime,managed_versions

SCRIPTS=Path(__file__).resolve().parent


def run(bundle,output,next_bundle=None,work=None):
    bundle=Path(bundle).resolve(strict=True);output=Path(output).absolute()
    if output.exists():raise ValueError('Existing native acceptance evidence is preserved')
    result=json.loads((bundle/'result.json').read_bytes())
    verified=managed_runtime.inspect(bundle/'payload',version=result['version'],target=managed_runtime.host_platform())
    if result['manifest_hash']!=verified['manifest_hash']:raise ValueError('Native bundle differs from builder result')
    if next_bundle is not None:
        next_bundle=Path(next_bundle).resolve(strict=True);following=json.loads((next_bundle/'result.json').read_bytes())
        managed_runtime.inspect(next_bundle/'payload',version=following['version'],target=result['platform'])
    base=Path(tempfile.mkdtemp(prefix='forge-native-acceptance-',dir=work)).resolve()
    home=base/'home';home.mkdir();app=base/'Forge application áikya & tools';project=base/'Existing project áikya';project.mkdir()
    allowed=('PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','TMPDIR','LANG','LC_ALL','SSL_CERT_FILE','SSL_CERT_DIR')
    env={k:v for k,v in os.environ.items() if k in allowed}
    env.update(HOME=str(home),USERPROFILE=str(home),LOCALAPPDATA=str(home/'AppData/Local'),APPDATA=str(home/'AppData/Roaming'),
        XDG_CONFIG_HOME=str(home/'.config'),XDG_CACHE_HOME=str(home/'.cache'),XDG_STATE_HOME=str(home/'.state'),
        AIKYA_INSTALL_ROOT=str(app),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',DO_NOT_TRACK='1')
    steps=[]
    def execute(name,command,timeout=300):
        started=time.monotonic()
        try:process=subprocess.run([str(a) for a in command],env=env,cwd=base,capture_output=True,text=True,encoding='utf8',timeout=timeout)
        except subprocess.TimeoutExpired as error:
            partial=[v.decode('utf8',errors='replace') if isinstance(v,bytes) else v or '' for v in (error.stdout,error.stderr)]
            (base/(name+'.log')).write_text(''.join(partial),encoding='utf8')
            steps.append(dict(name=name,exit_code=None,seconds=time.monotonic()-started,timed_out=True))
            raise ValueError('Native acceptance timed out: '+name+'; inspect '+str(base/(name+'.log'))) from error
        (base/(name+'.log')).write_text(process.stdout+process.stderr,encoding='utf8')
        steps.append(dict(name=name,exit_code=process.returncode,seconds=time.monotonic()-started))
        if process.returncode:raise ValueError('Native acceptance failed: '+name+'; inspect '+str(base/(name+'.log'))+'\n'+process.stderr[-3000:])
        return process.stdout
    def install(source,name,action='install'):
        if os.name=='nt':
            powershell=shutil.which('pwsh') or shutil.which('powershell')
            if not powershell:raise ValueError('Native Windows acceptance needs PowerShell')
            return execute(name,[powershell,'-NoProfile','-NonInteractive','-File',source/'install.ps1','-OfflineDir',source,'-NoPath','-Action',action],timeout=1200)
        return execute(name,['/bin/sh',source/'install.sh','--offline-dir',source,'--no-path'])
    try:
        install(bundle,'install');manager=app/'bin'/('aikya-manage.exe' if os.name=='nt' else 'aikya-manage')
        assert json.loads(execute('doctor',[manager,'doctor']))['version']==result['version']
        current=managed_runtime.resolve(app);python=current['python'];node=current['node']
        data=json.loads(execute('seed',[python,'-I','-B',SCRIPTS/'native_terminal_seed.py',project]))
        launcher=app/'bin'/('aikya.exe' if os.name=='nt' else 'aikya')
        launch=json.loads(execute('installed-launcher',[launcher,'--target',project,'--print-command']))
        assert launch['command'][0]==node and launch['command'][-1]==python
        selection=[python,'-I','-B','-m','aikya','skills','uninstall','--target',project,'--scope','project','--name','acceptance-skill']
        assert json.loads(execute('skill-withdraw-preview',selection))['status']=='preview'
        removed=json.loads(execute('skill-withdraw',selection+['--yes']))
        assert removed['status']=='removed' and removed['packages_retained'] is True
        restoration=[python,'-I','-B','-m','aikya','skills','restore','--target',project,'--scope','project',
                     '--all','--operation',removed['operation_id']]
        assert json.loads(execute('skill-restore-preview',restoration))['status']=='preview'
        assert json.loads(execute('skill-restore',restoration+['--yes']))['status']=='restored'
        commands=base/'commands.json';commands.write_text(json.dumps(data['commands']))
        session=json.loads(execute('installed-session',[node,SCRIPTS/'native_terminal_session.mjs',current['runtime'],project,python,commands]))
        observation=project/'aikya/docs/validation/installed-observation.json'
        execute('export-observation',[python,'-I','-B','-m','aikya','acceptance','export','--target',project,'--output',observation])
        exported=json.loads(observation.read_bytes())
        assert exported['runtime_version']==result['version'] and len(exported['runtime_fingerprint'])==64
        assert exported['provider_verified'] is False and exported['calls']==0
        theme=project/'.aikya/pi/theme.json';theme_before=theme.read_bytes();source_before=(project/'source.py').read_bytes()
        assert json.loads(install(bundle,'reinstall'))['status']=='up-to-date'
        if next_bundle is not None:
            install(next_bundle,'update');assert json.loads(execute('doctor-updated',[manager,'doctor']))['version']==following['version']
            assert json.loads(execute('manager-core-updated',[manager,'doctor']))['core_version']==managed_versions.python_version(following['version'])
            assert theme.read_bytes()==theme_before and (project/'source.py').read_bytes()==source_before
            execute('rollback',[manager,'rollback','--yes'])
            assert json.loads(execute('doctor-rollback',[manager,'doctor']))['version']==result['version']
        check=('import json;from pathlib import Path;from aikya.services.memory import search;from aikya.services.selected_skills import resolve;'
               'r=Path('+repr(str(project))+');assert len(search(r,"Acceptance decision",2000)["notes"])==1;'
               'assert len(resolve(r)["skills"])==1;print("retained")')
        execute('retained-data',[python,'-I','-B','-c',check])
        if os.name=='nt':install(bundle,'uninstall',action='uninstall')
        else:execute('uninstall',[manager,'uninstall','--yes'])
        assert not (app/'terminal/current.json').exists()
        assert not (app/'bin'/('aikya.exe' if os.name=='nt' else 'aikya')).exists()
        assert theme.read_bytes()==theme_before and (project/'source.py').read_bytes()==source_before
        execute('retained-after-uninstall',[python,'-I','-B','-c',check])
        evidence=dict(schema=1,version=result['version'],platform=result['platform'],manifest_hash=result['manifest_hash'],
            passed=True,steps=steps,provider_calls=session['provider_calls'],session=session,coverage=data['coverage'],profiles=data['profiles'],
            command_count=len(data['commands']),next_version=following['version'] if next_bundle is not None else None,
            runtime_fingerprint=exported['runtime_fingerprint'],
            work=str(base),legacy_migration='excluded by product scope',windows_uninstall='verified external installer, not a running locked executable')
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(evidence,indent=2)+'\n');return evidence
    except Exception:
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(dict(passed=False,version=result['version'],platform=result['platform'],steps=steps,work=str(base)),indent=2)+'\n')
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--next-bundle',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=run(args.bundle,args.output,args.next_bundle)
    print(json.dumps({key:result[key] for key in ('passed','version','platform','command_count','provider_calls')}))


if __name__=='__main__':main()
