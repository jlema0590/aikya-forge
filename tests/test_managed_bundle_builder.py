"""Native artifact preparation rejects incompatible or corrupt inputs before staging."""
import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from aikya.installation.managed_inputs import load
from aikya.installation.managed_runtime import host_platform

ROOT=Path(__file__).resolve().parents[1]


class BundleBuilderTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_bundle'),'Self-contained bundle builder is absent')
        self.builder=importlib.import_module('aikya.installation.managed_bundle');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def test_corrupt_official_assets_are_preserved_and_never_executed(self):
        assets=self.root/'assets';assets.mkdir();recipe=load()
        for component in ('python','node'):(assets/recipe[component]['file']).write_bytes(b'Not an official interpreter')
        with self.assertRaises(ValueError):self.builder.build(ROOT,self.root/'output','8.0.0-alpha.0',assets=assets)
        self.assertFalse((self.root/'output').exists());self.assertTrue(all(p.read_bytes()==b'Not an official interpreter' for p in assets.iterdir()))

    def test_missing_assets_do_not_implicitly_download_or_create_output(self):
        with self.assertRaises(ValueError):self.builder.build(ROOT,self.root/'output','8.0.0-alpha.0',assets=self.root/'absent')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_cross_platform_and_noncanonical_versions_fail_before_staging(self):
        foreign='win32-x64' if not host_platform().startswith('win32') else 'darwin-arm64'
        for version,target in [('8.0.0-alpha.00',host_platform()),('8.0.0-alpha.0',foreign)]:
            with self.subTest(version=version,target=target):
                with self.assertRaises(ValueError):self.builder.build(ROOT,self.root/'output',version,assets=self.root/'assets',target=target)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_existing_output_is_never_adopted(self):
        output=self.root/'output';output.mkdir();custom=output/'custom';custom.write_text('Keep me')
        with self.assertRaises(ValueError):self.builder.build(ROOT,output,'8.0.0-alpha.0',assets=self.root/'assets')
        self.assertEqual(custom.read_text(),'Keep me');self.assertEqual(len(list(output.iterdir())),1)


if __name__=='__main__':unittest.main()
