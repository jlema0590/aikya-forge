"""Shared portable member-name and file/directory topology checks for bounded artifacts."""
import unicodedata

DEVICES={'CON','PRN','AUX','NUL'}|{prefix+n for prefix in ('COM','LPT') for n in '123456789¹²³'}


def validate(paths,*,directories=(),max_files=80,max_nodes=160,max_length=160,denied=None,case_sensitive=False):
    if type(case_sensitive) is not bool:raise ValueError('Explicit filesystem case policy required')
    def normalized(value):
        value=unicodedata.normalize('NFC',value)
        return value if case_sensitive else value.casefold()
    files_list=list(paths);dirs=list(directories);names=files_list+dirs;seen={}
    if not 1<=len(files_list)<=max_files or len(names)>max_nodes:raise ValueError('Package member count exceeds its bound')
    for name in names:
        if (not isinstance(name,str) or not 1<=len(name)<=max_length or '\\' in name
                or (denied is not None and denied(name)) or any(ord(c)<32 or c in '<>:"|?*' for c in name)):
            raise ValueError('Unsafe or nonportable package member name')
        parts=name.split('/')
        if any(p in ('','.','..') or p.endswith(('.',' ')) or p.split('.',1)[0].upper() in DEVICES
               or len(p.encode('utf8'))>255 or len(p.encode('utf-16-le'))>510 for p in parts):
            raise ValueError('Unsafe, reserved or oversized package component')
        for count in range(1,len(parts)+1):
            prefix='/'.join(parts[:count]);key=normalized(prefix)
            if key in seen and seen[key]!=prefix:raise ValueError('Aliased package member path')
            seen[key]=prefix
    if len(seen)>max_nodes:raise ValueError('Package discovery entry budget exceeded')
    files={normalized(name) for name in files_list}
    if len(files)!=len(files_list) or files.intersection(normalized(name) for name in dirs):raise ValueError('Duplicate or conflicting package member roles')
    for name in names:
        parts=name.split('/')
        if any(normalized('/'.join(parts[:count])) in files for count in range(1,len(parts))):raise ValueError('Package file conflicts with a parent directory')
