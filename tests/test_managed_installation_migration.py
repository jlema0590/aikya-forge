"""Native installation migration backs up only owned v7 metadata and restores commands."""
import base64
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation import managed_install,managed_runtime
from aikya.installation.bootstrap import state
from managed_terminal_support import payload


class NativeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve();self.root=self.base/'application';self.root.mkdir();(self.root/'owner.json').write_text(json.dumps(state.OWNER))
        environment=self.root/'versions/7.2.2/retained';(environment/'bin').mkdir(parents=True);(environment/'bin/python').write_bytes(b'Never execute legacy interpreter')
        (self.root/'current.json').write_text(json.dumps(dict(version='7.2.2',environment=str(environment),python=str(environment/'bin/python'))))
        (self.root/'bin').mkdir();self.wrappers={name:('Original legacy '+name).encode() for name in ('aikya','aikya-manage','aikya-setup')}
        for name,raw in self.wrappers.items():(self.root/'bin'/name).write_bytes(raw)
        (self.root/'launchers.json').write_text(json.dumps({str(self.root/'bin'/name):base64.b64encode(raw).decode() for name,raw in self.wrappers.items()}))
        receipts=self.root/'receipts';receipts.mkdir();(receipts/('a'*64+'.json')).write_text(json.dumps(dict(schema=1,version='7.2.2',scope='global',before={},after={})))
        self.source=self.base/'source';payload(self.source)
        for item in (patch.object(managed_runtime,'host_platform',return_value='darwin-arm64'),patch('aikya.installation.managed_probe.check',return_value={'status':'passed'})):
            item.start();self.addCleanup(item.stop)

    def test_preview_names_legacy_identity_and_apply_keeps_exact_backup_and_original_metadata(self):
        plan=managed_install.preview(self.root,self.source);self.assertIn('legacy',plan,'Native installation migration has no reviewed metadata snapshot')
        self.assertEqual(plan['legacy']['version'],'7.2.2');before={name:(self.root/name).read_bytes() for name in plan['legacy']['files']}
        result=managed_install.apply(plan,approved=True)
        for name,raw in before.items():
            self.assertEqual((self.root/name).read_bytes(),raw)
            self.assertEqual((self.root/'terminal/operations'/result['operation']/'legacy'/name).read_bytes(),raw)
        managed_install.apply(managed_install.preview(self.root,action='uninstall'),approved=True)
        for name,raw in self.wrappers.items():self.assertEqual((self.root/'bin'/name).read_bytes(),raw)
        self.assertTrue((self.root/'current.json').exists());self.assertTrue((self.root/'versions/7.2.2/retained').exists())

    def test_changed_legacy_metadata_stales_the_preview_without_creating_a_native_operation(self):
        plan=managed_install.preview(self.root,self.source);self.assertIn('legacy',plan,'Native installation migration has no reviewed metadata snapshot')
        custom=self.root/'current.json';value=json.loads(custom.read_bytes());value['version']='7.2.1';custom.write_text(json.dumps(value));raw=custom.read_bytes()
        with self.assertRaises(ValueError):managed_install.apply(plan,approved=True)
        self.assertEqual(custom.read_bytes(),raw);self.assertFalse((self.root/'terminal/operations').exists())

    def test_realistic_embedded_runtime_receipt_larger_than_four_megabytes_gets_an_exact_backup(self):
        path=self.root/'receipts'/('a'*64+'.json');value=json.loads(path.read_bytes())
        value['after']={str(self.root/'public-runtime-data'):base64.b64encode(b'Public fixture data\n'*240000).decode()}
        raw=json.dumps(value).encode();self.assertGreater(len(raw),4_700_000);path.write_bytes(raw)
        plan=managed_install.preview(self.root,self.source);result=managed_install.apply(plan,approved=True)
        backup=self.root/'terminal/operations'/result['operation']/'legacy/receipts'/path.name
        self.assertEqual(backup.read_bytes(),raw);self.assertEqual(path.read_bytes(),raw)

    def test_excessive_legacy_receipt_is_refused_before_any_native_installation_effect(self):
        path=self.root/'receipts'/('a'*64+'.json')
        with path.open('wb') as stream:stream.truncate(16_000_001)
        with self.assertRaises(ValueError):managed_install.preview(self.root,self.source)
        self.assertEqual(path.stat().st_size,16_000_001);self.assertFalse((self.root/'terminal').exists())


if __name__=='__main__':unittest.main()
