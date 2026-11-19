"""Offline terminal tools are pinned data and never a project-provided executable."""
import hashlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from aikya.installation.managed_inputs import TARGETS


class ManagedToolInputs(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_tools'), 'Pinned offline terminal tools are absent')
        self.tools=importlib.import_module('aikya.installation.managed_tools')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def fixture(self):
        value=json.loads(self.tools.path().read_bytes());target='win32-x64';assets=self.root/'assets';assets.mkdir()
        for name,item in value['platforms'][target].items():
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w') as archive:
                archive.writestr(item['prefix']+'/'+item['executable'],b'Inert tool fixture')
                for license in ('LICENSE-MIT','LICENSE-APACHE','UNLICENSE','COPYING'):archive.writestr(item['prefix']+'/'+license,b'Retained license')
            raw=stream.getvalue();item['sha256']=hashlib.sha256(raw).hexdigest();(assets/item['file']).write_bytes(raw)
        source=self.root/'catalog.json';source.write_text(json.dumps(value))
        return target,assets,source,value

    def test_catalog_selects_exact_official_native_targets(self):
        for target in TARGETS:
            recipe=self.tools.load(target)
            self.assertEqual(set(recipe),{'fd','rg'})
            for name,item in recipe.items():
                self.assertEqual(item['version'],{'fd':'10.5.2','rg':'15.2.0'}[name])
                self.assertTrue(item['url'].startswith('https://github.com/'+{'fd':'sharkdp/fd','rg':'BurntSushi/ripgrep'}[name]+'/releases/download/'))
                if target.startswith('linux-'):self.assertIn('-unknown-linux-musl.',item['file'])
                if target.startswith('win32'):self.assertIn('-pc-windows-msvc.zip',item['file'])

    def test_official_version_output_accepts_revision_but_not_prefix_spoofing(self):
        self.assertTrue(callable(getattr(self.tools,'matches_version',None)), 'Bounded official tool version parsing is absent')
        for name,text,want in [('fd','fd 10.5.2\n',True),('rg','ripgrep 15.2.0 (rev e89fff89ac)\nfeatures\n',True),
                ('rg','ripgrep 15.2.0\n',True),('rg','ripgrep 15.2.00\n',False),('fd','fd 10.5.2evil\n',False),
                ('rg','ripgrep 15.2.0 (rev unsafe-code)\n',False),('fd','',False)]:
            with self.subTest(name=name,text=text):self.assertEqual(self.tools.matches_version(name,text),want)

    def test_changed_origin_architecture_and_hash_format_are_refused(self):
        target,assets,source,value=self.fixture()
        for field,bad in [('url','https://evil.invalid/tool.zip'),('file','fd-v10.5.2-aarch64-pc-windows-msvc.zip'),('sha256','bad'),('version','latest')]:
            original=value['platforms'][target]['fd'][field];value['platforms'][target]['fd'][field]=bad;source.write_text(json.dumps(value))
            with self.subTest(field=field),self.assertRaises(ValueError):self.tools.load(target,source=source)
            value['platforms'][target]['fd'][field]=original

    def test_verified_offline_tools_retain_binary_and_licenses(self):
        target,assets,source,_=self.fixture()
        recipe,raws=self.tools.prepare(target,assets,source=source)
        payload=self.root/'payload';payload.mkdir();downloads=self.root/'downloads';downloads.mkdir()
        observed=self.tools.install(recipe,raws,downloads,payload)
        self.assertEqual(set(observed),{'fd','rg'})
        for name in ('fd','rg'):
            self.assertEqual((payload/'tools'/name/(name+'.exe')).read_bytes(),b'Inert tool fixture')
            self.assertEqual((payload/'tools'/name/'LICENSE-MIT').read_bytes(),b'Retained license')
            self.assertEqual((downloads/recipe[name]['file']).read_bytes(),raws[name])

    def test_missing_corrupt_and_linked_offline_assets_never_download(self):
        target,assets,source,value=self.fixture();item=value['platforms'][target]['fd'];path=assets/item['file'];original=path.read_bytes()
        from aikya.installation import component_download
        with patch.object(component_download,'fetch',side_effect=AssertionError('No network')):
            path.write_bytes(b'Corrupt archive')
            with self.assertRaises(ValueError):self.tools.prepare(target,assets,source=source)
            path.unlink()
            with self.assertRaises(ValueError):self.tools.prepare(target,assets,source=source)
            outside=self.root/'outside';outside.write_bytes(original);path.symlink_to(outside)
            with self.assertRaises(ValueError):self.tools.prepare(target,assets,source=source)
        self.assertEqual(outside.read_bytes(),original)

    def test_managed_environment_uses_payload_tools_without_empty_path_entry(self):
        payload=self.root/'payload';runtime=payload/'runtime';runtime.mkdir(parents=True)
        ext='.exe' if os.name=='nt' else ''
        for name in ('fd','rg'):
            folder=payload/'tools'/name;folder.mkdir(parents=True);(folder/(name+ext)).write_bytes(b'Already verified fixture')
        before={'PATH':'','SENTINEL':'retained'};result=self.tools.environment({'runtime':str(runtime)},before)
        self.assertEqual(result['PATH'].split(os.pathsep),[str(payload/'tools/fd'),str(payload/'tools/rg')])
        self.assertEqual(before,{'PATH':'','SENTINEL':'retained'});self.assertEqual(result['SENTINEL'],'retained')
        self.assertEqual(result.get('NoDefaultCurrentDirectoryInExePath'),'1')
        (payload/'tools/fd'/('fd'+ext)).unlink()
        with self.assertRaises(ValueError):self.tools.environment({'runtime':str(runtime)},before)

    def test_path_delimiters_cannot_turn_verified_directories_into_other_search_entries(self):
        payload=self.root/('unsafe'+os.pathsep+'root');runtime=payload/'runtime';runtime.mkdir(parents=True)
        for name in ('fd','rg'):
            p=payload/'tools'/name/(name+('.exe' if os.name=='nt' else ''));p.parent.mkdir(parents=True);p.write_bytes(b'Preserved inert tool')
        with self.assertRaisesRegex(ValueError,'separator'):self.tools.environment({'runtime':str(runtime)},{'PATH':''})
        self.assertEqual(p.read_bytes(),b'Preserved inert tool')

    def test_corrupt_tool_input_stops_builder_before_output_creation(self):
        from aikya.installation import managed_bundle,managed_runtime
        assets=self.root/'assets';assets.mkdir()
        for item in self.tools.load(managed_runtime.host_platform()).values():(assets/item['file']).write_bytes(b'Corrupt tool')
        output=self.root/'output'
        with patch.object(managed_bundle,'_components',return_value={'python':b'Not executed','node':b'Not executed'}):
            with self.assertRaises(ValueError):managed_bundle.build(Path(__file__).resolve().parents[1],output,'0.2.0',assets=assets,code_index='none')
        self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
