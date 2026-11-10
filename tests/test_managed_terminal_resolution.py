"""A signed managed terminal can be resolved without running payload code."""
from pathlib import Path
import hashlib,importlib,importlib.util,json,os,tempfile,unittest
from unittest.mock import patch
from aikya.installation.bootstrap.state import OWNER
from aikya.review import authentication
from aikya.review.contracts import encoded

class ManagedResolutionTests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_runtime'),'Managed terminal resolution is absent')
  self.runtime=importlib.import_module('aikya.installation.managed_runtime')
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()/'application';self.root.mkdir()
  (self.root/'owner.json').write_text(json.dumps(OWNER));authentication.key(self.root,create=True)
  self.data={'node/bin/node':b'NOT EXECUTED NODE FIXTURE','python/bin/python3':b'NOT EXECUTED PYTHON FIXTURE',
    'runtime/src/launcher.ts':b'// Aikya terminal fixture.\n',
    'runtime/package.json':json.dumps({'name':'@aikya/pi-runtime','version':'8.0.0-alpha.0','dependencies':{'@earendil-works/pi-coding-agent':'1.5.0'}}).encode()}
  self.manifest=dict(schema=1,version='8.0.0-alpha.0',platform='darwin-arm64',python='python/bin/python3',node='node/bin/node',runtime='runtime',
    versions=dict(python='3.13.18',node='26.13.0',pi='1.5.0'),files={p:dict(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),executable=p in ('node/bin/node','python/bin/python3')) for p,raw in self.data.items()})
  self.publish()
  self.platform=patch.object(self.runtime,'host_platform',return_value='darwin-arm64');self.platform.start();self.addCleanup(self.platform.stop)
 def publish(self):
  raw=encoded(self.manifest).encode();sha=hashlib.sha256(raw).hexdigest();relative='terminal/versions/'+sha;self.payload=self.root/relative
  self.payload.mkdir(parents=True,exist_ok=True)
  for name,data in self.data.items():
   p=self.payload/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o755 if self.manifest['files'][name]['executable'] else 0o644)
  (self.payload/'manifest.json').write_bytes(raw)
  receipt=dict(schema=1,generated_by='aikya-managed-terminal',version=self.manifest['version'],platform='darwin-arm64',payload=relative,manifest_hash=sha)
  (self.root/'terminal/current.json').write_text(encoded(authentication.seal(self.root,receipt)))
 def test_linux_gnu_and_musl_are_not_treated_as_the_same_payload(self):
  self.platform.stop()
  with patch.object(self.runtime.sys,'platform','linux'),patch.object(self.runtime.platform,'machine',return_value='x86_64'):
   for libc,expected in [('glibc','linux-x64-gnu'),('musl','linux-x64-musl')]:
    with self.subTest(libc=libc),patch.object(self.runtime.platform,'libc_ver',return_value=(libc,'2.36')):
     self.assertEqual(self.runtime.host_platform(),expected)
   with patch.object(self.runtime.platform,'libc_ver',return_value=('','')):
    with self.assertRaises(ValueError):self.runtime.host_platform()
 def test_resolves_exact_owned_roles_without_executing_or_writing_anything(self):
  before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  value=self.runtime.resolve(self.root)
  self.assertEqual(value['python'],str(self.payload/'python/bin/python3'));self.assertEqual(value['node'],str(self.payload/'node/bin/node'))
  self.assertEqual(value['runtime'],str(self.payload/'runtime'));self.assertEqual(value['version'],'8.0.0-alpha.0')
  self.assertEqual(before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_modified_and_unlisted_payload_data_are_preserved_and_refused(self):
  target=self.payload/'runtime/src/launcher.ts';target.write_text('User changes')
  with self.assertRaises(ValueError):self.runtime.resolve(self.root)
  self.assertEqual(target.read_text(),'User changes');target.write_bytes(self.data['runtime/src/launcher.ts'])
  extra=self.payload/'runtime/extra.js';extra.write_text('Unknown code')
  with self.assertRaises(ValueError):self.runtime.resolve(self.root)
  self.assertEqual(extra.read_text(),'Unknown code')
 def test_unsigned_or_foreign_receipts_cannot_select_a_payload(self):
  current=self.root/'terminal/current.json';raw=json.loads(current.read_text());raw['payload']['payload']='../outside';current.write_text(json.dumps(raw))
  with self.assertRaises(ValueError):self.runtime.resolve(self.root)
 def test_a_correctly_sealed_platform_mismatch_still_cannot_execute(self):
  with patch.object(self.runtime,'host_platform',return_value='linux-x64'):
   with self.assertRaises(ValueError):self.runtime.resolve(self.root)
 def test_symlinked_payload_and_component_paths_are_preserved(self):
  target=self.payload/'node/bin/node';target.unlink();outside=self.root/'outside-node';outside.write_bytes(b'External user data');target.symlink_to(outside)
  with self.assertRaises(ValueError):self.runtime.resolve(self.root)
  self.assertEqual(outside.read_bytes(),b'External user data')
 def test_a_correctly_sealed_noncanonical_release_identity_is_refused(self):
  self.manifest['version']='8.00.0-alpha.0'
  package=json.loads(self.data['runtime/package.json']);package['version']='8.00.0-alpha.0'
  self.data['runtime/package.json']=json.dumps(package).encode()
  self.manifest['files']['runtime/package.json'].update(sha256=hashlib.sha256(self.data['runtime/package.json']).hexdigest(),size=len(self.data['runtime/package.json']))
  self.publish()
  with self.assertRaises(ValueError):self.runtime.resolve(self.root)
 def test_entrypoint_cannot_be_missing_from_the_sealed_file_inventory(self):
  del self.manifest['files']['runtime/src/launcher.ts'];del self.data['runtime/src/launcher.ts'];self.publish()
  with self.assertRaises(ValueError):self.runtime.resolve(self.root)
 def test_unknown_application_data_and_missing_runtime_are_read_only_failures(self):
  empty=self.root.parent/'empty';empty.mkdir()
  with self.assertRaises(ValueError):self.runtime.resolve(empty)
  self.assertEqual(list(empty.iterdir()),[])

if __name__=='__main__':unittest.main()
