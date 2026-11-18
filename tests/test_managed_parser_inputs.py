"""Native binary parsers use reviewed platform/ABI pins without source builds."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class NativeParserInputs(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_parsers'),'Native pinned parser packaging is absent')
        self.parsers=importlib.import_module('aikya.installation.managed_parsers')

    def test_native_compatibility_rejects_other_architecture_abi_and_newer_libc(self):
        cases=[('tree_sitter_java-0.23.5-cp39-abi3-macosx_11_0_arm64.whl','darwin-arm64',True),
               ('tree_sitter_java-0.23.5-cp39-abi3-macosx_11_0_x86_64.whl','darwin-arm64',False),
               ('tree_sitter-0.25.2-cp313t-cp313t-win_amd64.whl','win32-x64',False),
               ('tree_sitter-0.25.2-cp313-cp313-win_amd64.whl','win32-x64',True),
               ('tree_sitter_java-0.23.5-cp39-abi3-manylinux_2_17_x86_64.whl','linux-x64-gnu',True),
               ('tree_sitter_java-0.23.5-cp39-abi3-manylinux_2_34_x86_64.whl','linux-x64-gnu',False),
               ('tree_sitter_java-0.23.5-cp39-abi3-manylinux_2_17_x86_64.whl','linux-x64-musl',False),
               ('tree_sitter_java-0.23.5-cp39-abi3-musllinux_1_2_x86_64.whl','linux-x64-musl',True)]
        for filename,target,want in cases:
            with self.subTest(filename=filename,target=target):self.assertEqual(self.parsers.compatible(filename,target),want)

    def test_reviewed_platforms_have_engine_or_honest_unavailable_capabilities(self):
        from aikya.installation.managed_inputs import TARGETS
        from aikya.installation.bootstrap.code_index import PINS
        for target in TARGETS:
            result=self.parsers.load(target)
            self.assertEqual(set(result['wheels'])|set(result['unavailable']),set(PINS))
            self.assertFalse(set(result['wheels'])&set(result['unavailable']))
            if len(result['wheels'])>0:self.assertIn('tree-sitter',result['wheels'])
            for name,item in result['wheels'].items():
                self.assertEqual(item['version'],PINS[name]);self.assertTrue(self.parsers.compatible(item['file'],target))

    def test_foreign_origins_or_unpinned_versions_fail_before_fetch(self):
        data=json.loads(self.parsers.path().read_text());target='darwin-arm64'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'inputs.json'
            for field,value in [('url','https://unreviewed.invalid/file.whl'),('url',{}),('url',1),('version','99.0.0'),('sha256','not-a-hash')]:
                copy=json.loads(json.dumps(data));copy['platforms'][target]['tree-sitter'][field]=value;path.write_text(json.dumps(copy))
                with self.subTest(field=field),self.assertRaises(ValueError):self.parsers.load(target,path)


if __name__=='__main__':unittest.main()
