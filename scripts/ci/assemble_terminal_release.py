"""Assemble all native targets from same-commit successful CI artifacts; never publish."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile
import zipfile
from aikya.installation.bootstrap import state,download
from aikya.installation import managed_entries,managed_runtime,managed_versions
from aikya.installation.managed_inputs import TARGETS
from aikya.review.contracts import hash_id,parse
from aikya.storage import write_new,atomic_write


def read(path,limit=128000):return managed_runtime._read(state.safe(path),limit)


def checksum(path):
    path=state.safe(path)
    if not path.is_file() or not 0<path.stat().st_size<=256000000:raise ValueError('Native archive size/type differs')
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):result.update(chunk)
    return result.hexdigest()


def zip_manifest(path,version,target):
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        if not 1<=len(entries)<=50001 or len({e.filename for e in entries})!=len(entries):raise ValueError('Invalid native ZIP inventory')
        info=archive.getinfo('manifest.json')
        if info.file_size>16000000:raise ValueError('Oversized native manifest')
        raw=archive.read(info);manifest=parse(raw)
        managed_runtime._manifest(manifest,dict(version=version,platform=target))
        if set(e.filename for e in entries)!=set(manifest['files'])|{'manifest.json'}:raise ValueError('Archive inventory differs from native manifest')
        for entry in entries:
            if entry.filename=='manifest.json':continue
            record=manifest['files'][entry.filename]
            if entry.is_dir() or entry.file_size!=record['size'] or entry.flag_bits&1:raise ValueError('Unknown native ZIP entry')
            value=hashlib.sha256()
            with archive.open(entry) as stream:
                for chunk in iter(lambda:stream.read(65536),b''):value.update(chunk)
            if value.hexdigest()!=record['sha256']:raise ValueError('Native ZIP file hash differs')
        return hashlib.sha256(raw).hexdigest()


def tar_manifest(path,expected):
    total=0
    with tarfile.open(path,'r|gz') as archive:
        for count,entry in enumerate(archive):
            total+=entry.size
            if count>=50001 or not entry.isfile() or entry.size>256000000 or total>1500000000:raise ValueError('Invalid native TAR inventory')
            if entry.name=='manifest.json':
                if entry.size>16000000:raise ValueError('Oversized native TAR manifest')
                if hashlib.sha256(archive.extractfile(entry).read(16000001)).hexdigest()!=expected:raise ValueError('TAR manifest differs from native ZIP')
                return
    raise ValueError('Native TAR has no matching manifest')


def native_inputs(folder,version,target,commit):
    folder=state.safe(folder);result=parse(read(folder/'result.json'));accepted=parse(read(folder/'acceptance.json',1000000));origin=parse(read(folder/'build-origin.json'))
    for record in (result,accepted,origin):
        if not isinstance(record,dict) or record.get('version')!=version or record.get('platform')!=target:raise ValueError('Native artifact identity differs')
    if origin.get('source_commit')!=commit:raise ValueError('Native source commit differs')
    if (accepted.get('passed') is not True or type(accepted.get('provider_calls')) is not int or accepted['provider_calls']!=0
            or accepted.get('manifest_hash')!=result.get('manifest_hash')):raise ValueError('Native acceptance is incomplete or differs')
    if managed_versions.order(accepted.get('next_version'))<=managed_versions.order(version):raise ValueError('Native update/rollback acceptance is absent')
    hash_id(result['manifest_hash']);hashes=download.parse_checksums(read(folder/'SHA256SUMS'));prefix='aikya-terminal-'+version+'-'+target
    names=[prefix+'.zip']+([] if target.startswith('win32') else [prefix+'.tar.gz'])
    for name in names:
        if name not in hashes or checksum(folder/name)!=hashes[name]:raise ValueError('Native artifact integrity differs')
    if result.get('sha256')!=hashes[names[0]] or zip_manifest(folder/names[0],version,target)!=result['manifest_hash']:
        raise ValueError('Native archive manifest differs from execution evidence')
    if len(names)>1:tar_manifest(folder/names[1],result['manifest_hash'])
    return dict(archives={name:hashes[name] for name in names},manifest_hash=result['manifest_hash'],next_version=accepted['next_version'],
                runtime_fingerprint=hash_id(accepted.get('runtime_fingerprint')))


def assemble(inputs,output,version,commit):
    managed_versions.parts(version)
    if not isinstance(commit,str) or not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',commit):raise ValueError('Explicit source commit required')
    inputs=state.safe(Path(inputs).absolute());output=state.safe(Path(output).absolute())
    if output.exists():raise ValueError('Existing release output is preserved')
    wanted={'forge-native-'+target for target in TARGETS}
    if set(p.name for p in inputs.iterdir())!=wanted:raise ValueError('A complete unique seven-target native set is required')
    checked={target:native_inputs(inputs/('forge-native-'+target),version,target,commit) for target in TARGETS}
    if len({record['runtime_fingerprint'] for record in checked.values()})!=1:
        raise ValueError('Native packaged source fingerprints differ across platforms')
    output.mkdir(parents=True);hashes={}
    for target,record in checked.items():
        for name,expected in record['archives'].items():
            shutil.copyfile(inputs/('forge-native-'+target)/name,output/name)
            if checksum(output/name)!=expected:raise ValueError('Native artifact changed during release copy')
            hashes[name]=expected
    initial=''.join(value+'  '+name+'\n' for name,value in sorted(hashes.items())).encode()
    write_new(output/'SHA256SUMS',initial,mode=0o600)
    entries=managed_entries.build(version,output,output/'entries')
    for name in (*entries['entries'],'terminal-bootstrap.json'):
        raw=read(output/'entries'/name);write_new(output/name,raw,mode=0o700 if name.endswith('.sh') else 0o600)
        hashes[name]=hashlib.sha256(raw).hexdigest()
    release=dict(schema=1,version=version,source_commit=commit,platforms=checked,
                 limitations='Native installed SDK acceptance; external-provider and visual-terminal evidence are separate gates')
    raw=(json.dumps(release,indent=2)+'\n').encode();write_new(output/'release.json',raw,mode=0o600);hashes['release.json']=hashlib.sha256(raw).hexdigest()
    atomic_write(output/'SHA256SUMS',''.join(value+'  '+name+'\n' for name,value in sorted(hashes.items())),mode=0o600)
    return release


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--version',required=True);parser.add_argument('--commit',required=True)
    args=parser.parse_args();result=assemble(args.inputs,args.output,args.version,args.commit)
    print(json.dumps(dict(version=result['version'],platforms=sorted(result['platforms']),published=False)))


if __name__=='__main__':main()
