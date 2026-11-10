"""Private release staging must not version or execute an unselected source tree."""
import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class PrivateWheelTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_wheel'),'Private core wheel staging is absent')
        self.builder=importlib.import_module('aikya.installation.managed_wheel')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve()

    @unittest.skipUnless(importlib.util.find_spec('build'),'Build frontend is a contributor prerequisite')
    def test_real_private_wheel_has_coherent_metadata_and_preserves_stable_version(self):
        before=(ROOT/'VERSION').read_bytes();destination=self.base/'private core áikya'
        value=self.builder.build(ROOT,destination,'8.0.0-alpha.0')
        wheel=Path(value['wheel']);self.assertEqual(wheel.name,'aikya_forge-8.0.0a0-py3-none-any.whl')
        with zipfile.ZipFile(wheel) as archive:
            metadata=archive.read('aikya_forge-8.0.0a0.dist-info/METADATA').decode()
            self.assertIn('\nName: aikya-forge\n',metadata);self.assertIn('\nVersion: 8.0.0a0\n',metadata)
            self.assertEqual(archive.read('aikya/resources/distribution/VERSION'),b'8.0.0a0\n')
            self.assertIn('aikya/installation/managed_runtime.py',archive.namelist())
        self.assertEqual((ROOT/'VERSION').read_bytes(),before)
        self.assertEqual(value['runtime_version'],'8.0.0-alpha.0');self.assertEqual(value['python_version'],'8.0.0a0')
        self.assertTrue((destination/'source-inputs.json').is_file())

    def test_invalid_version_is_refused_before_creating_output(self):
        for version in ('7.2.2','8.0.0+local','8.0.0-alpha.00','8.0.0; echo unsafe'):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):self.builder.build(ROOT,self.base/'output',version)
        self.assertEqual(list(self.base.iterdir()),[])

    def test_existing_build_output_is_preserved_without_adopting_its_files(self):
        destination=self.base/'existing';destination.mkdir();custom=destination/'custom.txt';custom.write_text('Keep my output')
        with self.assertRaises(ValueError):self.builder.build(ROOT,destination,'8.0.0-alpha.0')
        self.assertEqual(custom.read_text(),'Keep my output');self.assertEqual(sorted(p.name for p in destination.iterdir()),['custom.txt'])


if __name__=='__main__':unittest.main()
