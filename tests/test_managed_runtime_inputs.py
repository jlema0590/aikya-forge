"""A host recipe has explicit official origins and fixed component identities."""
import importlib,importlib.util,json
from pathlib import Path
import tempfile,unittest


class RuntimeInputTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_inputs'),'Pinned runtime component recipes are absent')
        self.inputs=importlib.import_module('aikya.installation.managed_inputs')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def test_platform_selection_is_explicit_read_only_and_never_falls_back_to_another_abi(self):
        recipe=self.inputs.load('darwin-arm64')
        self.assertEqual(recipe['platform'],'darwin-arm64');self.assertEqual(recipe['python']['executable'],'bin/python3.13')
        self.assertEqual(recipe['node']['executable'],'bin/node');self.assertEqual(len(recipe['python']['sha256']),64)
        self.assertEqual(self.inputs.load('win32-x64')['node']['executable'],'node.exe')
        with self.assertRaises(ValueError):self.inputs.load('linux-arm64-musl')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_untrusted_origins_credentials_and_missing_hashes_are_not_recipes(self):
        value=json.loads(self.inputs.path().read_text())
        for field,changed in [('url','https://evil.example/node.tar.gz'),('url','https://user:secret@nodejs.org/dist/file'),('sha256','')]:
            variant=json.loads(json.dumps(value));variant['platforms']['darwin-arm64']['node'][field]=changed
            file=self.root/'inputs.json';file.write_text(json.dumps(variant))
            with self.subTest(field=field,changed=changed),self.assertRaises(ValueError):self.inputs.load('darwin-arm64',file)

    def test_mismatched_archive_name_or_component_path_is_refused(self):
        value=json.loads(self.inputs.path().read_text())
        for field,changed in [('file','../foreign.tar.gz'),('executable','../outside'),('prefix','other-version')]:
            variant=json.loads(json.dumps(value));variant['platforms']['darwin-arm64']['node'][field]=changed
            file=self.root/'inputs.json';file.write_text(json.dumps(variant))
            with self.subTest(field=field),self.assertRaises(ValueError):self.inputs.load('darwin-arm64',file)

    def test_node_system_requirements_include_abi_specific_minima_and_external_linux_runtime(self):
        recipe=self.inputs.load('linux-x64-gnu');self.assertIn('requirements',recipe,'Pinned bundles lack reviewed upstream system requirements')
        self.assertEqual(recipe['requirements']['node']['glibc'],'2.28');self.assertIn('libatomic',recipe['requirements']['node']['libraries'])
        self.assertEqual(self.inputs.load('linux-x64-musl')['requirements']['node']['kernel'],'6.12')
        self.assertEqual(self.inputs.load('darwin-arm64')['requirements']['node']['macos'],'13.5')


if __name__=='__main__':unittest.main()
