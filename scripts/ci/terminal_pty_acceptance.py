"""Bounded actual PTY checks without providers; Windows visual acceptance stays explicit."""
import argparse
import errno
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import time
from aikya.installation import build_sources,managed_runtime,managed_tools
from aikya.installation.bootstrap import state
from aikya.storage import write_new


def plain(raw):
    raw=re.sub(rb'\x1b\].*?(?:\x07|\x1b\\)',b'',raw,flags=re.S)
    return re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',raw).decode('utf8',errors='replace')


class ConsoleCapture:
    def __init__(self,command,cwd,environment,*,max_bytes=2000000):
        if os.name=='nt':raise ValueError('Windows requires separately observed ConPTY/visual acceptance')
        if not 256<=max_bytes<=4000000:raise ValueError('Invalid PTY byte bound')
        self.command=command;self.cwd=cwd;self.environment=environment;self.max_bytes=max_bytes
        self.raw=bytearray();self.pid=None;self.fd=None;self.exit_code=None;self.columns=120;self.rows=38

    def __enter__(self):
        import pty
        self.started=time.monotonic();pid,fd=pty.fork()
        if pid==0:
            try:os.chdir(self.cwd);os.execvpe(self.command[0],self.command,self.environment)
            except OSError:os.write(2,b'PTY process unavailable\n');os._exit(127)
        self.pid=pid;self.fd=fd;self.resize(self.columns,self.rows);return self

    def _reap(self):
        if self.pid is None:return
        pid,status=os.waitpid(self.pid,os.WNOHANG)
        if pid:self.exit_code=os.waitstatus_to_exitcode(status);self.pid=None

    def pump(self,wait=.05):
        if time.monotonic()-self.started>120:raise TimeoutError('Overall PTY deadline exceeded')
        ready,_,_=select.select([self.fd],[],[],wait)
        if ready:
            try:chunk=os.read(self.fd,65536)
            except OSError as error:
                if error.errno!=errno.EIO:raise
                chunk=b''
            previous=len(self.raw)
            if previous+len(chunk)>self.max_bytes:raise ValueError('PTY output exceeds its byte bound')
            self.raw.extend(chunk)
            for query,reply in [(b'\x1b[6n',b'\x1b[1;1R'),(b'\x1b]11;?',b'\x1b]11;rgb:1111/1111/1111\x1b\\')]:
                if query in self.raw[max(0,previous-len(query)+1):]:os.write(self.fd,reply)
        self._reap()

    def until(self,predicate,timeout=20):
        deadline=time.monotonic()+timeout
        while not predicate():
            if time.monotonic()>=deadline:raise TimeoutError('Expected PTY state was not observed')
            if self.pid is None:raise ValueError('PTY exited before its expected state')
            self.pump()

    def expect(self,text,timeout=20,after=0):
        self.until(lambda:text in plain(self.raw[after:]),timeout)

    def send(self,text):
        offset=len(self.raw);os.write(self.fd,text.encode('utf8'));return offset

    def resize(self,columns,rows):
        import fcntl,struct,termios
        if not 40<=columns<=200 or not 20<=rows<=80:raise ValueError('Invalid terminal size')
        fcntl.ioctl(self.fd,termios.TIOCSWINSZ,struct.pack('HHHH',rows,columns,0,0))
        self.columns=columns;self.rows=rows

    def finish(self,timeout=10):
        deadline=time.monotonic()+timeout
        while self.pid is not None:
            if time.monotonic()>=deadline:raise TimeoutError('PTY child did not exit gracefully')
            self.pump()
        return self.exit_code

    def __exit__(self,*ignored):
        try:
            self._reap()
            if self.pid is not None:
                try:os.killpg(self.pid,signal.SIGTERM)
                except (ProcessLookupError,PermissionError):
                    self._reap()
                    if self.pid is not None:raise
                deadline=time.monotonic()+3
                while self.pid is not None and time.monotonic()<deadline:self._reap();time.sleep(.02)
                if self.pid is not None:
                    os.killpg(self.pid,signal.SIGKILL);_,status=os.waitpid(self.pid,0)
                    self.exit_code=os.waitstatus_to_exitcode(status);self.pid=None
        finally:
            if self.fd is not None:os.close(self.fd);self.fd=None


def _theme(project):
    try:return json.loads((project/'.aikya/pi/theme.json').read_bytes()).get('name')
    except (FileNotFoundError,PermissionError):return None


def run(output,*,application=None,source=None,assets=None,fetch=False):
    if os.name=='nt':raise ValueError('Windows visual/ConPTY acceptance is not established by this POSIX collector')
    if bool(application)==bool(source):raise ValueError('Choose exactly one installed application or source runtime')
    output=state.safe(Path(output).absolute()).resolve(strict=False)
    if output.exists():raise ValueError('Existing PTY evidence is preserved')
    if source and output.is_relative_to(Path(source).resolve()):raise ValueError('PTY evidence must be outside the source checkout')
    output.mkdir(parents=True);project=output/'project';project.mkdir();env=build_sources.environment(output/'home')
    env.update(TERM='xterm-256color',COLORTERM='truecolor',COLUMNS='120',LINES='38')
    if application:
        runtime=managed_runtime.resolve(application);python=runtime['python'];version=runtime['version']
        env=managed_tools.environment(runtime,env);env['AIKYA_INSTALL_ROOT']=str(Path(application).resolve())
        command=[python,'-I','-B','-m','aikya','terminal','--target',str(project)]
    else:
        import sys
        source=Path(source).resolve(strict=True);node=shutil.which('node')
        if not node:raise ValueError('Source-mode PTY acceptance requires an explicit available Node')
        recipe,raws=managed_tools.prepare(managed_runtime.host_platform(),assets,fetch=fetch)
        downloads=output/'downloads';downloads.mkdir();payload=output/'payload';payload.mkdir()
        managed_tools.install(recipe,raws,downloads,payload)
        env['PATH']=os.pathsep.join([str(payload/'tools/fd'),str(payload/'tools/rg'),str(Path(node).resolve().parent)])
        version=(source/'VERSION').read_text().strip();python=sys.executable
        command=[python,'-I','-B','-m','aikya','terminal','--runtime-dir',str(source/'packages/aikya-pi'),'--target',str(project)]
    terminal=None;result=dict(status='failed',mode='managed' if application else 'source',version=version,platform=managed_runtime.host_platform(),
        provider_calls=0,visual_acceptance=False,ui='Actual POSIX PTY; no human visual/device or provider acceptance')
    try:
        with ConsoleCapture(command,project,env) as terminal:
            terminal.expect('AIKYA v'+version,timeout=45)
            offset=terminal.send('/aikya-tokens\r');terminal.expect('Provider quota: unavailable',timeout=30,after=offset)
            assert 'not found. Offline mode' not in plain(terminal.raw)
            assert 'Downloading...' not in plain(terminal.raw)
            write_new(output/'startup.ansi',bytes(terminal.raw))
            offset=terminal.send('/aikya-theme light\r');terminal.expect('Apply this theme?',timeout=20,after=offset)
            terminal.send('\x1b[A');terminal.send('\r');terminal.until(lambda:_theme(project)=='light',timeout=20)
            write_new(output/'light-theme.ansi',bytes(terminal.raw))
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
            usage_status=usage['status'],bytes=len(terminal.raw),exit_code=terminal.exit_code)
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
