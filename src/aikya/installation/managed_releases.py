"""Explicit stable/preview release selection and verified native transport."""
import hashlib
from pathlib import Path
from aikya.review.contracts import parse
from .bootstrap import download,state
from .managed_inputs import TARGETS
from .managed_runtime import _read
from .managed_versions import parts,order

RELEASES='https://api.github.com/repos/jlema0590/aikya-forge/releases?per_page=100'


def resolve(version=None,*,channel='stable',offline=False):
    if channel not in ('stable','preview'):raise ValueError('Choose stable or preview explicitly')
    if version not in (None,'latest'):
        identity=parts(version)
        if channel=='stable' and identity[3] is not None:raise ValueError('Stable selection cannot adopt a prerelease')
        return version
    if offline:raise ValueError('Offline native installation requires an explicit version')
    records=parse(download.https_bytes(RELEASES,8000000))
    if not isinstance(records,list) or len(records)>100:raise ValueError('Unexpected native release catalog')
    candidates=[]
    for record in records:
        if not isinstance(record,dict) or record.get('draft') is not False or type(record.get('prerelease')) is not bool or not record.get('published_at'):continue
        tag=record.get('tag_name')
        if not isinstance(tag,str) or not tag.startswith(('v0.','v8.')):continue
        candidate=tag[1:]
        try:identity=parts(candidate)
        except ValueError:continue
        if record['prerelease']!=(identity[3] is not None) or (channel=='stable' and identity[3] is not None):continue
        candidates.append(candidate)
    if not candidates:raise ValueError('No published native release exists in the selected channel')
    return max(candidates,key=order)


def artifact(version,target,*,offline_dir=None):
    parts(version)
    if target not in TARGETS:raise ValueError('No native release recipe for this platform/ABI')
    name='aikya-terminal-'+version+'-'+target+'.zip'
    base=download.REPOSITORY+'/releases/download/v'+version+'/'
    def read(filename,limit):
        return _read(state.safe(Path(offline_dir)/filename),limit) if offline_dir is not None else download.https_bytes(base+filename,limit)
    sums=download.parse_checksums(read('SHA256SUMS',128000))
    if name not in sums:raise ValueError('Release checksums do not cover this native platform')
    raw=read(name,256000000)
    if hashlib.sha256(raw).hexdigest()!=sums[name]:raise ValueError('Native release integrity checksum mismatch')
    return raw
