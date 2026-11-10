"""Disposable SDK command transport for local process tests, never project code."""
import hashlib
import os
from pathlib import Path
import stat
import sys


def tool_path(folder,name):return Path(folder)/(name+('.cmd' if os.name=='nt' else ''))


def write_tool(path,body):
    if os.name=='nt':
        script=path.with_suffix('.py');script.write_text(body,encoding='utf8')
        # The fixture wrapper changes with the script, preserving tool drift cases.
        path.write_text('@echo off\n"'+sys.executable+'" -I -B "'+str(script)+'" %*\nrem '+hashlib.sha256(body.encode()).hexdigest()+'\n',encoding='utf8')
    else:path.write_text('#!'+sys.executable+'\n'+body,encoding='utf8')
    path.chmod(path.stat().st_mode|stat.S_IXUSR)
