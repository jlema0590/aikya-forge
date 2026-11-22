"""Render fixed Aikya FIGlet variants for the terminal without reading the project."""
import json
from importlib.metadata import PackageNotFoundError,version

VERSION='1.0.4'


def banner():
    fallback=dict(schema=1,text='Aikya',generator='plain',version=None,variants=[])
    try:
        from pyfiglet import Figlet,FigletError
    except ImportError:return fallback
    try:
        if version('pyfiglet')!=VERSION:return fallback
        variants=[]
        for font in ('slant','small'):
            lines=[row.rstrip() for row in Figlet(font=font,width=200).renderText('Aikya').splitlines()]
            if not 1<=len(lines)<=8 or any(len(row)>80 or any(not 32<=ord(c)<=126 for c in row) for row in lines):return fallback
            variants.append(dict(font=font,lines=lines))
        return dict(schema=1,text='Aikya',generator='pyfiglet',version=VERSION,variants=variants)
    except (OSError,ValueError,TypeError,PackageNotFoundError,FigletError):return fallback


def main():
    print(json.dumps(banner(),ensure_ascii=True));return 0


if __name__=='__main__':raise SystemExit(main())
