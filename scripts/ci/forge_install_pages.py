"""Copy exact native Forge installers from an already published verified release."""
import argparse
import hashlib
import json
from pathlib import Path
from aikya.installation import managed_runtime,managed_versions
from aikya.installation.bootstrap import state,download
from aikya.installation.managed_inputs import TARGETS
from aikya.review.contracts import parse


def build(version,assets,output,commit):
    identity=managed_versions.parts(version)
    if identity[3]:raise ValueError('Stable installation Pages must not select a prerelease')
    assets=state.safe(Path(assets).absolute());output=state.safe(Path(output).absolute())
    if output.exists():raise ValueError('Existing Pages output is preserved')
    hashes=download.parse_checksums(managed_runtime._read(state.safe(assets/'SHA256SUMS'),128000));raws={}
    for name in ('install.sh','install.ps1','release.json','terminal-bootstrap.json'):
        raw=managed_runtime._read(state.safe(assets/name),128000)
        if hashlib.sha256(raw).hexdigest()!=hashes.get(name):raise ValueError('Published installer provenance differs')
        raws[name]=raw
    release=parse(raws['release.json']);bootstrap=parse(raws['terminal-bootstrap.json'])
    if (release.get('version')!=version or release.get('source_commit')!=commit or bootstrap.get('version')!=version
            or bootstrap.get('channel')!='stable' or set(bootstrap.get('platforms',{}))!=set(TARGETS)
            or bootstrap.get('entries')!={n:hashes[n] for n in ('install.sh','install.ps1')}):
        raise ValueError('Published Forge identity or native target coverage differs')
    output.mkdir(parents=True)
    for name in ('install.sh','install.ps1'):(output/(name+'.txt' if name.endswith('.ps1') else name)).write_bytes(raws[name])
    (output/'.nojekyll').write_bytes(b'')
    provenance=dict(tag='v'+version,source_commit=commit,source=download.REPOSITORY+'/releases/tag/v'+version,
                    sha256={n:hashes[n] for n in ('install.sh','install.ps1')})
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf8')
    (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Aikya Forge</title>'
        '<h1>Aikya Forge</h1><p>Verified native terminal with bundled Python and Node. Project memory stays local.</p>'
        '<h2>macOS / Linux</h2><pre>curl -fsSL https://jlema0590.github.io/aikya-forge/install.sh | sh</pre>'
        '<h2>Windows PowerShell</h2><pre>irm https://jlema0590.github.io/aikya-forge/install.ps1.txt | iex</pre>'
        '<p>Open a new terminal, then run <code>aikya</code> inside your project. Model use needs explicit configuration and budget.</p>'
        '<p><a href="install.sh">Shell source</a> · <a href="install.ps1.txt">PowerShell source</a> · '
        '<a href="provenance.json">Published provenance</a> · <a href="https://github.com/jlema0590/aikya-forge">Guide</a></p></html>\n',encoding='utf8')
    return provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--version',required=True)
    parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--commit',required=True);args=parser.parse_args()
    print(json.dumps(build(args.version,args.assets,args.output,args.commit)))


if __name__=='__main__':main()
