"""Publishable installers require complete same-commit native evidence and exact archives."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import tarfile
from managed_terminal_support import payload
import unittest
import zipfile
from aikya.installation.managed_inputs import TARGETS

ROOT=Path(__file__).resolve().parents[1]


class TerminalReleaseAssemblyTests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'scripts/ci/assemble_terminal_release.py'
        self.assertTrue(path.is_file(),'Native release assembly is absent')
        spec=importlib.util.spec_from_file_location('terminal_release_assembly',path);self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.inputs=self.root/'inputs';self.inputs.mkdir()
        self.version='0.2.0';self.commit='a'*40
        for target in TARGETS:self.fixture(target)

    def fixture(self,target):
        folder=self.inputs/('forge-native-'+target);folder.mkdir()
        staged=self.root/('payload-'+target);payload(staged,self.version)
        data=json.loads((staged/'manifest.json').read_bytes());data['platform']=target
        manifest=json.dumps(data).encode();(staged/'manifest.json').write_bytes(manifest)
        name='aikya-terminal-'+self.version+'-'+target+'.zip'
        with zipfile.ZipFile(folder/name,'w') as archive:
            for path in staged.rglob('*'):
                if path.is_file():archive.write(path,path.relative_to(staged).as_posix())
        hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest()}
        if not target.startswith('win32'):
            tarname=name[:-4]+'.tar.gz'
            with tarfile.open(folder/tarname,'w:gz') as archive:
                for path in staged.rglob('*'):
                    if path.is_file():archive.add(path,arcname=path.relative_to(staged).as_posix(),recursive=False)
            hashes[tarname]=hashlib.sha256((folder/tarname).read_bytes()).hexdigest()
        (folder/'SHA256SUMS').write_text(''.join(value+'  '+name+'\n' for name,value in hashes.items()))
        (folder/'result.json').write_text(json.dumps(dict(version=self.version,platform=target,sha256=hashes[name],manifest_hash=hashlib.sha256(manifest).hexdigest())))
        (folder/'acceptance.json').write_text(json.dumps(dict(passed=True,version=self.version,platform=target,
            manifest_hash=hashlib.sha256(manifest).hexdigest(),next_version='0.2.1',provider_calls=0)))
        (folder/'build-origin.json').write_text(json.dumps(dict(version=self.version,platform=target,source_commit=self.commit)))

    def test_complete_native_set_builds_version_pinned_universal_entries(self):
        output=self.root/'release';self.module.assemble(self.inputs,output,self.version,self.commit)
        from aikya.installation.bootstrap.download import parse_checksums
        checksums=parse_checksums((output/'SHA256SUMS').read_bytes())
        self.assertEqual(set(json.loads((output/'terminal-bootstrap.json').read_bytes())['platforms']),set(TARGETS))
        for name,expected in checksums.items():self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(),expected)
        if Path('/bin/sh').exists():
            result=subprocess.run(['/bin/sh',str(output/'install.sh'),'--dry-run'],env={'PATH':'/not-present'},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['version'],'0.2.0')

    def test_wrong_commit_failed_acceptance_and_corruption_cannot_create_release(self):
        folder=self.inputs/'forge-native-darwin-arm64'
        for file,field,value in [('build-origin.json','source_commit','b'*40),('acceptance.json','passed',False),('result.json','manifest_hash','0'*64)]:
            path=folder/file;before=path.read_bytes();item=json.loads(before);item[field]=value;path.write_text(json.dumps(item))
            with self.subTest(field=field),self.assertRaises(ValueError):self.module.assemble(self.inputs,self.root/'release',self.version,self.commit)
            self.assertFalse((self.root/'release').exists());path.write_bytes(before)
        archive=next(folder.glob('*.zip'));archive.write_bytes(b'Corrupted native asset')
        with self.assertRaises(ValueError):self.module.assemble(self.inputs,self.root/'release',self.version,self.commit)
        self.assertFalse((self.root/'release').exists())

    def test_missing_platform_and_custom_release_output_are_preserved(self):
        import shutil
        shutil.rmtree(self.inputs/'forge-native-win32-arm64')
        with self.assertRaises(ValueError):self.module.assemble(self.inputs,self.root/'release',self.version,self.commit)
        existing=self.root/'existing';existing.mkdir();(existing/'custom').write_bytes(b'Keep')
        with self.assertRaises(ValueError):self.module.assemble(self.inputs,existing,self.version,self.commit)
        self.assertEqual((existing/'custom').read_bytes(),b'Keep')


if __name__=='__main__':unittest.main()
