"""Temporary no-inference Windows ARM diagnostic using unchanged verified native inputs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
from aikya.installation import managed_entries, managed_runtime


def main():
    source=Path(__file__).resolve().parents[2]
    inputs=source/'native-inputs';output=source/'observer-probe';output.mkdir()
    origin=json.loads((inputs/'build-origin.json').read_bytes())
    if origin['source_commit']!='86c37346ce27749713109e4529061f4b2d07aef0':
        raise ValueError('Unexpected retained native source')
    managed_entries.build(origin['version'],inputs,output/'entries')
    shutil.copy2(output/'entries/install.ps1',inputs/'install.ps1')
    home=output/'home';home.mkdir();application=output/'Forge application áikya & tools'
    allowed=('PROCESSOR_ARCHITECTURE','PROCESSOR_ARCHITEW6432','PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','LANG','LC_ALL')
    env={k:v for k,v in os.environ.items() if k in allowed}
    env.update(HOME=str(home),USERPROFILE=str(home),LOCALAPPDATA=str(home/'AppData/Local'),APPDATA=str(home/'AppData/Roaming'),
        XDG_CONFIG_HOME=str(home/'.config'),XDG_CACHE_HOME=str(home/'.cache'),XDG_STATE_HOME=str(home/'.state'),
        AIKYA_INSTALL_ROOT=str(application),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',DO_NOT_TRACK='1')
    def execute(name,command):
        result=subprocess.run([str(v) for v in command],env=env,cwd=output,capture_output=True,timeout=1200)
        (output/(name+'.log')).write_bytes(result.stdout+result.stderr)
        return result
    installed=execute('install',[shutil.which('pwsh'),'-NoProfile','-NonInteractive','-File',inputs/'install.ps1','-OfflineDir',inputs,'-NoPath'])
    if installed.returncode:raise ValueError('Diagnostic installation failed')
    current=managed_runtime.resolve(application);failures=[]
    for trial in range(1,11):
        trial_root=output/('trial-'+str(trial));trial_root.mkdir()
        root=trial_root/'Existing project áikya';root.mkdir()
        seed=execute('seed-'+str(trial),[current['python'],'-I','-B',source/'scripts/ci/native_terminal_seed.py',root])
        if seed.returncode:raise ValueError('Diagnostic seed failed')
        commands=output/('commands-'+str(trial)+'.json');commands.write_text(json.dumps(json.loads(seed.stdout)['commands']))
        session=execute('session-'+str(trial),[current['node'],source/'scripts/ci/native_terminal_session.mjs',current['runtime'],root,current['python'],commands])
        print(json.dumps(dict(trial=trial,exit_code=session.returncode)),flush=True)
        if session.returncode:failures.append(trial)
    if failures:raise ValueError('Installed observer diagnostic failed in trials '+str(failures))


if __name__=='__main__':main()
