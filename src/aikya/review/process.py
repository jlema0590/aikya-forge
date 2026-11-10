"""Bounded stdout/stderr capture for an explicitly authorized local process."""
import hashlib
import os
import signal
import subprocess
import time
from aikya.core.pipe_reader import PipeReader


def _stop(proc):
    if os.name != 'nt':
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        except PermissionError:
            # Darwin may deny signalling an exited, unreaped process group.
            # Reap that child; never hide denial while the child is still running.
            if proc.poll() is None:raise
    elif proc.poll() is None:
        try:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        except (OSError, subprocess.TimeoutExpired): proc.kill()
    if proc.poll() is None: proc.kill()
    proc.wait(timeout=5)


def capture_process(argv, cwd, env, timeout, output_limit, cancel):
    started, clock = time.time_ns(), time.monotonic_ns()
    meta = dict(status='cancelled', exit_code=None, started_ns=started,
                finished_ns=started, duration_ns=0, stdout_bytes=0, stderr_bytes=0)
    hashes = {name: hashlib.sha256() for name in ('stdout', 'stderr')}
    data, readers, proc = bytearray(), {}, None
    try:
        if not cancel():
            proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name != 'nt')
            readers = {name: PipeReader(getattr(proc, name)) for name in ('stdout', 'stderr')}
            ended = set(); deadline = time.monotonic() + timeout
            meta['status'] = 'completed'
            while len(ended) < 2 or proc.poll() is None:
                if cancel(): meta['status'] = 'cancelled'; break
                if time.monotonic() >= deadline: meta['status'] = 'timed_out'; break
                for name, reader in readers.items():
                    if name in ended: continue
                    chunk = reader.read(.01)
                    if chunk is None: continue
                    if not chunk: ended.add(name); continue
                    hashes[name].update(chunk); meta[name + '_bytes'] += len(chunk)
                    if name == 'stdout': data.extend(chunk[:max(0, output_limit - len(data))])
                    if meta['stdout_bytes'] + meta['stderr_bytes'] > output_limit:
                        meta['status'] = 'output_limit'; break
                if meta['status'] != 'completed': break
    except KeyboardInterrupt:
        meta['status'] = 'cancelled'
    except OSError:
        meta['status'] = 'launch_failed'
    finally:
        if proc is not None:
            _stop(proc)
            meta['exit_code'] = proc.returncode
            for name, reader in readers.items():
                getattr(proc, name).close(); reader.close()
        meta.update(finished_ns=time.time_ns(), duration_ns=time.monotonic_ns() - clock)
        meta.update({name + '_sha256': value.hexdigest() for name, value in hashes.items()})
    return meta, bytes(data)
