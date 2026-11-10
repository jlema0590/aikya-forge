"""Private Node staging retains lock provenance and never adopts executable links."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NodeStagingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_node'),'Managed Node staging is absent')
        self.builder=importlib.import_module('aikya.installation.managed_node');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def test_snapshot_versions_both_package_and_lock_without_mutating_source(self):
        source=ROOT/'packages/aikya-pi';before={p:(source/p).read_bytes() for p in ('package.json','package-lock.json')}
        stage=self.root/'runtime';value=self.builder.prepare(source,stage,'8.0.0-alpha.1')
        package=json.loads((stage/'package.json').read_bytes());lock=json.loads((stage/'package-lock.json').read_bytes())
        self.assertEqual(package['version'],'8.0.0-alpha.1');self.assertEqual(lock['version'],package['version']);self.assertEqual(lock['packages']['']['version'],package['version'])
        self.assertEqual(lock['packages']['']['dependencies'],package['dependencies']);self.assertEqual(package['dependencies']['@earendil-works/pi-coding-agent'],'1.5.0')
        self.assertEqual(before,{p:(source/p).read_bytes() for p in before});self.assertFalse((stage/'node_modules').exists());self.assertIn('src/launcher.ts',value['files'])
        self.assertTrue((stage/'src/identity.ts').is_file())

    def test_local_or_unpinned_lock_sources_fail_before_any_output(self):
        source=self.root/'source';source.mkdir();(source/'src').mkdir();(source/'src/launcher.ts').write_text('// fixture')
        for name in ('package.json','package-lock.json'):(source/name).write_bytes((ROOT/'packages/aikya-pi'/name).read_bytes())
        lock=json.loads((source/'package-lock.json').read_bytes());entry=next(v for k,v in lock['packages'].items() if k and v.get('resolved'));entry['resolved']='file:/private/custom-package'
        (source/'package-lock.json').write_text(json.dumps(lock))
        with self.assertRaises(ValueError):self.builder.prepare(source,self.root/'runtime','8.0.0-alpha.0')
        self.assertFalse((self.root/'runtime').exists())

    def test_only_contained_bin_file_links_are_flattened_as_exact_regular_files(self):
        runtime=self.root/'runtime';binary=runtime/'node_modules/package/tool.js';binary.parent.mkdir(parents=True);binary.write_bytes(b'#!/usr/bin/env node\n// verified fixture\n');binary.chmod(0o700)
        alias=runtime/'node_modules/.bin/tool';alias.parent.mkdir();alias.symlink_to('../package/tool.js')
        self.assertEqual(self.builder.flatten(runtime),1);self.assertFalse(alias.is_symlink());self.assertEqual(alias.read_bytes(),binary.read_bytes())

    def test_one_escaping_link_blocks_all_link_rewrites(self):
        runtime=self.root/'runtime';binary=runtime/'node_modules/package/tool.js';binary.parent.mkdir(parents=True);binary.write_bytes(b'Fixture')
        alias=runtime/'node_modules/.bin/tool';alias.parent.mkdir();alias.symlink_to('../package/tool.js');outside=self.root/'private';outside.write_text('User data')
        unsafe=alias.parent/'escape';unsafe.symlink_to(outside)
        with self.assertRaises(ValueError):self.builder.flatten(runtime)
        self.assertTrue(alias.is_symlink());self.assertTrue(unsafe.is_symlink());self.assertEqual(outside.read_text(),'User data')

    def test_nonobject_dependency_metadata_is_refused_without_creating_output(self):
        source=self.root/'source';source.mkdir();(source/'src').mkdir();(source/'src/launcher.ts').write_text('// fixture')
        for name in ('package.json','package-lock.json'):(source/name).write_bytes((ROOT/'packages/aikya-pi'/name).read_bytes())
        lock=json.loads((source/'package-lock.json').read_bytes());name=next(k for k in lock['packages'] if k);lock['packages'][name]=None
        (source/'package-lock.json').write_text(json.dumps(lock))
        with self.assertRaises(ValueError):self.builder.prepare(source,self.root/'output','8.0.0-alpha.0')
        self.assertFalse((self.root/'output').exists())


if __name__=='__main__':unittest.main()
