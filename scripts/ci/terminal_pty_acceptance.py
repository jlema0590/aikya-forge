"""Bounded actual POSIX/ConPTY checks without providers or human visual acceptance."""
import argparse
import errno
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import subprocess
import time
from aikya.installation import build_sources,managed_runtime,managed_tools
from aikya.installation.bootstrap import state
from aikya.storage import write_new


def plain(raw):
    raw=re.sub(rb'\x1b\].*?(?:\x07|\x1b\\)',b'',raw,flags=re.S)
    return re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',raw).decode('utf8',errors='replace')


class ConsoleCapture:
    def __init__(self,command,cwd,environment,*,max_bytes=2000000):
        if not 256<=max_bytes<=4000000:raise ValueError('Invalid PTY byte bound')
        self.command=command;self.cwd=cwd;self.environment=environment;self.max_bytes=max_bytes
        self.raw=bytearray();self.pid=None;self.group=None;self.fd=None;self.exit_code=None;self.columns=120;self.rows=38;self.windows=None

    def __enter__(self):
        self.started=time.monotonic()
        if os.name=='nt':
            import importlib.util
            spec=importlib.util.spec_from_file_location('forge_windows_pty',Path(__file__).with_name('windows_pty.py'))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            self.windows=module.WindowsPty(self.command,self.cwd,self.environment,self.columns,self.rows)
            self.pid=self.windows.process.pid;return self
        import pty
        pid,fd=pty.fork()
        if pid==0:
            try:os.chdir(self.cwd);os.execvpe(self.command[0],self.command,self.environment)
            except OSError:os.write(2,b'PTY process unavailable\n');os._exit(127)
        self.pid=pid;self.group=pid;self.fd=fd;self.resize(self.columns,self.rows);return self

    def _reap(self):
        if self.pid is None:return
        if self.windows:
            code=self.windows.poll()
            if code is not None:
                self.exit_code=code;self.pid=None
                while chunk:=self.windows.read(0):self._append(chunk)
            return
        # Keep the leader waitable until group cleanup so its ID cannot be reused.
        observed=os.waitid(os.P_PID,self.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
        if observed and observed.si_pid:
            self.exit_code=observed.si_status if observed.si_code==os.CLD_EXITED else -observed.si_status;self.pid=None

    def pump(self,wait=.05):
        if time.monotonic()-self.started>120:raise TimeoutError('Overall PTY deadline exceeded')
        if self.windows:
            self._append(self.windows.read(wait));self._reap();return
        ready,_,_=select.select([self.fd],[],[],wait)
        if ready:
            try:chunk=os.read(self.fd,65536)
            except OSError as error:
                if error.errno!=errno.EIO:raise
                chunk=b''
            self._append(chunk)
        self._reap()

    def _append(self,chunk):
        previous=len(self.raw)
        if previous+len(chunk)>self.max_bytes:raise ValueError('PTY output exceeds its byte bound')
        self.raw.extend(chunk)
        if self.pid is None:return
        for query,reply in [(b'\x1b[6n',b'\x1b[1;1R'),(b'\x1b]11;?',b'\x1b]11;rgb:1111/1111/1111\x1b\\')]:
            if query in self.raw[max(0,previous-len(query)+1):]:self._write(reply)

    def _write(self,value):
        if self.windows:self.windows.write(value)
        else:os.write(self.fd,value)

    def until(self,predicate,timeout=20):
        deadline=time.monotonic()+timeout
        while not predicate():
            if time.monotonic()>=deadline:raise TimeoutError('Expected PTY state was not observed')
            if self.pid is None:raise ValueError('PTY exited before its expected state')
            self.pump()

    def expect(self,text,timeout=20,after=0):
        self.until(lambda:text in plain(self.raw[after:]),timeout)

    def settle(self,duration):
        if not 0<=duration<=1:raise ValueError('Invalid terminal input gap')
        deadline=time.monotonic()+duration
        while time.monotonic()<deadline:
            if self.pid is None:raise ValueError('PTY exited during input settling')
            self.pump(min(.02,max(0,deadline-time.monotonic())))

    def send(self,text):
        offset=len(self.raw);self._write(text.encode('utf8'));return offset

    def resize(self,columns,rows):
        if not 40<=columns<=200 or not 20<=rows<=80:raise ValueError('Invalid terminal size')
        if self.windows:self.windows.resize(columns,rows)
        else:
            import fcntl,struct,termios
            fcntl.ioctl(self.fd,termios.TIOCSWINSZ,struct.pack('HHHH',rows,columns,0,0))
        self.columns=columns;self.rows=rows

    def finish(self,timeout=10):
        deadline=time.monotonic()+timeout
        while self.pid is not None:
            if time.monotonic()>=deadline:raise TimeoutError('PTY child did not exit gracefully')
            self.pump()
        return self.exit_code

    def _signal_group(self,value):
        try:os.killpg(self.group,value)
        except ProcessLookupError:pass
        except PermissionError:
            # Darwin can report EPERM for an anchored group containing only its
            # exited leader. A live owned leader still requires a hard failure.
            self._reap()
            if self.pid is not None:raise

    def __exit__(self,*ignored):
        if self.windows:
            self.windows.close();self.pid=None;return
        try:
            self._reap()
            if self.group is not None:
                self._signal_group(signal.SIGTERM)
                deadline=time.monotonic()+3
                while self.pid is not None and time.monotonic()<deadline:self._reap();time.sleep(.02)
                self._signal_group(signal.SIGKILL)
                _,status=os.waitpid(self.group,0)
                self.exit_code=os.waitstatus_to_exitcode(status);self.pid=None;self.group=None
        finally:
            if self.fd is not None:os.close(self.fd);self.fd=None


def _theme(project):
    try:return json.loads((project/'.aikya/pi/console.json').read_bytes())['settings']['theme']
    except (FileNotFoundError,PermissionError):pass
    try:return json.loads((project/'.aikya/pi/theme.json').read_bytes()).get('name')
    except (FileNotFoundError,PermissionError):return None


def _console_style(project):
    try:return json.loads((project/'.aikya/pi/console.json').read_bytes())['settings']['textStyle']
    except (FileNotFoundError,PermissionError):return None


def settings_roundtrip(terminal,output,project):
    offset=terminal.send('/aikya-settings\r');terminal.expect('Forge settings',after=offset)
    write_new(output/'settings.ansi',bytes(terminal.raw))
    terminal.send('\r');terminal.expect('Providers · local catalog')
    terminal.expect('openai-codex');terminal.send('\x1b');terminal.settle(.2)
    terminal.send('\x1b[B');terminal.settle(.1);terminal.send('\r');terminal.expect('Appearance')
    for _ in range(5):terminal.send('\x1b[B');terminal.settle(.05)
    terminal.send('\r');terminal.expect('Text style')
    terminal.send('\x1b[B');terminal.settle(.1);terminal.send('\r')
    terminal.until(lambda:_console_style(project)=='bold')
    terminal.settle(.2);terminal.send('\x1b');terminal.settle(.2)
    write_new(output/'settings-applied.ansi',bytes(terminal.raw))


def run(output,*,application=None,source=None,assets=None,fetch=False):
    if bool(application)==bool(source):raise ValueError('Choose exactly one installed application or source runtime')
    output=state.safe(Path(output).absolute()).resolve(strict=False)
    if output.exists():raise ValueError('Existing PTY evidence is preserved')
    if source and output.is_relative_to(Path(source).resolve()):raise ValueError('PTY evidence must be outside the source checkout')
    git_fixture=None
    output.mkdir(parents=True);project=output/'project';project.mkdir();env=build_sources.environment(output/'home')
    env.update(TERM='xterm-256color',COLORTERM='truecolor',COLUMNS='120',LINES='38')
    if os.name=='nt':
        env.update(APPDATA=str(output/'home/AppData/Roaming'),LOCALAPPDATA=str(output/'home/AppData/Local'))
        for key in ('APPDATA','LOCALAPPDATA'):Path(env[key]).mkdir(parents=True)
    if application:
        runtime=managed_runtime.resolve(application);python=runtime['python'];version=runtime['version']
        env['PATH']='';env['AIKYA_INSTALL_ROOT']=str(Path(application).resolve())
        command=[str(Path(application)/'bin'/('aikya.exe' if os.name=='nt' else 'aikya')),'--target',str(project)]
    else:
        import sys
        source=Path(source).resolve(strict=True);node=shutil.which('node')
        if not node:raise ValueError('Source-mode PTY acceptance requires an explicit available Node')
        recipe,raws=managed_tools.prepare(managed_runtime.host_platform(),assets,fetch=fetch)
        downloads=output/'downloads';downloads.mkdir();payload=output/'payload';payload.mkdir()
        managed_tools.install(recipe,raws,downloads,payload)
        path_entries=[str(payload/'tools/fd'),str(payload/'tools/rg'),str(Path(node).resolve().parent)]
        git=shutil.which('git')
        if git:
            git=str(Path(git).resolve());path_entries.append(str(Path(git).parent))
            for arguments in (['init','--quiet','--initial-branch','preview/forge',str(project)],['-C',str(project),'config','user.name','Forge Preview']):
                subprocess.run([git,*arguments],env=env,cwd=output,capture_output=True,check=True,timeout=10)
            git_fixture=dict(project=project.name,branch='preview/forge',user='Forge Preview')
        env['PATH']=os.pathsep.join(path_entries)
        version=(source/'VERSION').read_text().strip();python=sys.executable
        command=[python,'-I','-B','-m','aikya','terminal','--runtime-dir',str(source/'packages/aikya-pi'),'--target',str(project)]
    terminal=None;result=dict(status='failed',mode='managed' if application else 'source',version=version,platform=managed_runtime.host_platform(),
        provider_calls=0,visual_acceptance=False,ui=('Actual Windows ConPTY' if os.name=='nt' else 'Actual POSIX PTY')+'; no human visual/device or provider acceptance')
    fixture=project/'verified/nested/SearchFixture.java';fixture.parent.mkdir(parents=True);write_new(fixture,'class SearchFixture {}\n')
    if os.name=='nt':
        for name in ('fd.exe','rg.exe'):write_new(project/name,b'Inert invalid executable, never runnable')
    try:
        with ConsoleCapture(command,project,env) as terminal:
            terminal.expect('Aikya Forge v'+version,timeout=45)
            terminal.expect('Project & Git',timeout=10)
            terminal.expect('Aikya local budget',timeout=10)
            for field in ('Claude','Codex','Context: unavailable','Tokens: unknown','Usage 5h: unavailable','Usage 7d: unavailable'):
                terminal.expect(field,timeout=10)
            terminal.expect('Project: '+project.name,timeout=10)
            if git_fixture:
                terminal.expect('Branch: preview/forge',timeout=10)
                terminal.expect('User: Forge Preview',timeout=10)
            terminal.expect('/   |  (_) /____  ______ _',timeout=10)
            offset=terminal.send('/aikya-tokens\r');terminal.expect('Provider quota: unavailable',timeout=30,after=offset)
            assert 'not found. Offline mode' not in plain(terminal.raw)
            assert 'Downloading...' not in plain(terminal.raw)
            offset=terminal.send('@SearchFix');terminal.expect('verified/nested/SearchFixture.java',timeout=20,after=offset)
            terminal.send('\x1b');terminal.settle(.2)
            terminal.send('\x15');terminal.settle(.2)
            write_new(output/'startup.ansi',bytes(terminal.raw))
            if git_fixture:
                subprocess.run([git,'-C',str(project),'symbolic-ref','HEAD','refs/heads/preview/updated'],env=env,cwd=output,capture_output=True,check=True,timeout=10)
                terminal.expect('Branch: preview/updated',timeout=15)
            offset=terminal.send('/aikya-theme light\r');terminal.expect('Apply this theme?',timeout=20,after=offset)
            terminal.send('\x1b[A');terminal.settle(.1);terminal.send('\r');terminal.until(lambda:_theme(project)=='light',timeout=20)
            write_new(output/'light-theme.ansi',bytes(terminal.raw))
            settings_roundtrip(terminal,output,project)
            assert _theme(project)=='light','Changing text style must retain the selected base theme'
            terminal.resize(100,32);offset=terminal.send('/aikya-tokens\r')
            terminal.expect('Provider quota: unavailable',timeout=20,after=offset)
            write_new(output/'resized.ansi',bytes(terminal.raw));terminal.send('/quit\r')
            if terminal.finish()!=0:raise ValueError('Interactive terminal did not exit cleanly')
        from aikya.routing import pi_usage
        usage=pi_usage.status(project);assert usage['calls']==0 and usage['status']!='available'
        cache=project/'.aikya/pi/agent/bin';cache.mkdir();marker=cache/'fd';write_new(marker,b'Unreviewed data; never executable')
        with ConsoleCapture(command,project,env) as denied:
            denied.expect('Project-local tool cache',timeout=45)
            if denied.finish()!=2:raise ValueError('Project cache did not block native startup')
        assert marker.read_bytes()==b'Unreviewed data; never executable'
        result.update(status='passed',theme='light',resize=dict(columns=100,rows=32),cache_refused=True,
            usage_status=usage['status'],bytes=len(terminal.raw),exit_code=terminal.exit_code,file_completion=True,
            launcher_supplies_tools=bool(application))
        result.update(settings_panel=True,provider_catalog=True,text_style='bold',banner='pyfiglet-1.0.4',project_identity=git_fixture,branch_change_observed=bool(git_fixture),provider_metrics=True)
        return result
    finally:
        if terminal is not None:write_new(output/'terminal.log',bytes(terminal.raw))
        write_new(output/'pty-result.json',json.dumps(result,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--application',type=Path);group.add_argument('--source',type=Path)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--assets',type=Path)
    parser.add_argument('--fetch-tools',action='store_true');args=parser.parse_args()
    print(json.dumps(run(args.output,application=args.application,source=args.source,assets=args.assets,fetch=args.fetch_tools),sort_keys=True))


if __name__=='__main__':main()
