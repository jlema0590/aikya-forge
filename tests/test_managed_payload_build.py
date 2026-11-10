"""Sealed bundle data must survive relocation and reject unknown mutable input."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from aikya.installation import managed_runtime
from aikya.installation.managed_archives import extract


class PayloadBuildTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_payload'),'Portable payload sealing is absent')
        self.payload=importlib.import_module('aikya.installation.managed_payload')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.folder=self.root/'staging';self.folder.mkdir()
        entries={'python/bin/python3':b'Not executable test fixture','node/bin/node':b'Not executable test fixture',
                 'runtime/src/launcher.ts':b'// fixture', 'runtime/package.json':json.dumps(dict(name='@aikya/pi-runtime',version='8.0.0-alpha.0',dependencies={'@earendil-works/pi-coding-agent':'1.5.0'})).encode()}
        for name,raw in entries.items():
            path=self.folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o700 if '/bin/' in name else 0o600)
        self.arguments=dict(version='8.0.0-alpha.0',target='darwin-arm64',versions=dict(python='3.13.18',node='26.13.0',pi='1.5.0'),python='python/bin/python3',node='node/bin/node',runtime='runtime')

    def test_sealed_manifest_and_archive_are_relocatable_and_reproducible(self):
        value=self.payload.seal(self.folder,**self.arguments)
        self.assertEqual(value['manifest_hash'],hashlib.sha256((self.folder/'manifest.json').read_bytes()).hexdigest())
        first=self.payload.archive(self.folder,self.root/'first.zip');second=self.payload.archive(self.folder,self.root/'second.zip')
        self.assertEqual(first['sha256'],second['sha256'])
        moved=self.root/'relocated áikya';extract(first['archive'],moved,first['sha256'],'.')
        checked=managed_runtime.inspect(moved,version='8.0.0-alpha.0',target='darwin-arm64')
        self.assertEqual(checked['manifest_hash'],value['manifest_hash']);self.assertEqual(checked['python'],str(moved/'python/bin/python3'))
        self.assertEqual(len(checked['manifest']['files']),4)

    def test_custom_manifest_or_archive_is_preserved(self):
        manifest=self.folder/'manifest.json';manifest.write_text('Custom manifest')
        with self.assertRaises(ValueError):self.payload.seal(self.folder,**self.arguments)
        self.assertEqual(manifest.read_text(),'Custom manifest');manifest.unlink();self.payload.seal(self.folder,**self.arguments)
        output=self.root/'custom.zip';output.write_bytes(b'User data')
        with self.assertRaises(ValueError):self.payload.archive(self.folder,output)
        self.assertEqual(output.read_bytes(),b'User data')

    def test_changed_and_unlisted_data_block_archiving_without_deleting_anything(self):
        self.payload.seal(self.folder,**self.arguments)
        custom=self.folder/'custom.txt';custom.write_text('Keep this')
        with self.assertRaises(ValueError):self.payload.archive(self.folder,self.root/'output.zip')
        self.assertEqual(custom.read_text(),'Keep this');self.assertFalse((self.root/'output.zip').exists());custom.unlink()
        source=self.folder/'runtime/src/launcher.ts';source.write_bytes(b'// changed')
        with self.assertRaises(ValueError):self.payload.archive(self.folder,self.root/'output.zip')
        self.assertEqual(source.read_bytes(),b'// changed')

    def test_links_and_noncanonical_roles_are_rejected_before_sealing(self):
        link=self.folder/'external';link.symlink_to(self.root)
        with self.assertRaises(ValueError):self.payload.seal(self.folder,**self.arguments)
        self.assertFalse((self.folder/'manifest.json').exists());link.unlink()
        self.arguments['node']='../outside'
        with self.assertRaises(ValueError):self.payload.seal(self.folder,**self.arguments)
        self.assertFalse((self.folder/'manifest.json').exists())

    def test_nonobject_package_metadata_is_a_bounded_refusal_before_sealing(self):
        (self.folder/'runtime/package.json').write_text('[]')
        with self.assertRaises(ValueError):self.payload.seal(self.folder,**self.arguments)
        self.assertFalse((self.folder/'manifest.json').exists())

    def test_posix_bootstrap_archive_uses_regular_tar_data_and_fixed_gzip_metadata(self):
        import tarfile
        self.payload.seal(self.folder,**self.arguments)
        first=self.payload.archive(self.folder,self.root/'first.tar.gz',format='tar.gz');second=self.payload.archive(self.folder,self.root/'second.tar.gz',format='tar.gz')
        self.assertEqual(first['sha256'],second['sha256'])
        with tarfile.open(first['archive']) as archive:self.assertTrue(all(p.isfile() for p in archive))
        moved=self.root/'tar extracted';extract(first['archive'],moved,first['sha256'],'.')
        self.assertEqual(managed_runtime.inspect(moved,version='8.0.0-alpha.0',target='darwin-arm64')['manifest_hash'],first['manifest_hash'])


if __name__=='__main__':unittest.main()
