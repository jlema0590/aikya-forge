"""Build two native Forge versions and retain publishable artifacts plus actual acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from aikya.installation.managed_bundle import build
from aikya.installation.managed_versions import parts
from native_terminal_acceptance import run


def successor(version):
    major,minor,patch,kind,number=parts(version)
    return f'{major}.{minor}.{patch}-{kind}.{number+1}' if kind else f'{major}.{minor}.{patch+1}'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2]);args=parser.parse_args()
    source=args.source.resolve();work=(args.work or Path(os.environ.get('RUNNER_TEMP',tempfile.gettempdir()))/'forge-native-build').absolute()
    if work.exists():raise ValueError('Native job output must be new')
    version=(source/'VERSION').read_text().strip();next_version=successor(version);work.mkdir(parents=True)
    first=work/'primary';second=work/'successor';result=build(source,first,version,fetch_components=True)
    for wheel in (first/'parser-downloads').glob('*.whl'):shutil.copy2(wheel,first/'downloads'/wheel.name)
    build(source,second,next_version,assets=first/'downloads')
    output=work/'publish';output.mkdir()
    evidence=run(first,work/'acceptance.json',second,work=work)
    assert evidence['passed'] and evidence['next_version']==next_version
    for artifact in sorted({result[key] for key in ('archive','bootstrap_archive') if key in result}):
        shutil.copy2(artifact,output/Path(artifact).name)
    for name in ('SHA256SUMS','result.json','terminal-bootstrap.json'):
        shutil.copy2(first/name,output/name)
    shutil.copy2(work/'acceptance.json',output/'acceptance.json')
    source_sha=os.environ.get('GITHUB_SHA')
    (output/'build-origin.json').write_text(json.dumps(dict(version=version,platform=result['platform'],source_commit=source_sha,
        source_version_sha256=hashlib.sha256((source/'VERSION').read_bytes()).hexdigest(),provider_calls=0),indent=2)+'\n')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as stream:stream.write('platform='+result['platform']+'\noutput='+str(output)+'\n')
    print(json.dumps(dict(passed=True,platform=result['platform'],version=version,next_version=next_version,output=str(output))))


if __name__=='__main__':main()
