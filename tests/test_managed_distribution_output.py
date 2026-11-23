"""A private native release pairs transport hashes with a no-Python entry script."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from aikya.installation.bootstrap.download import parse_checksums
from managed_terminal_support import payload


class ManagedDistributionTests(unittest.TestCase):
    def test_native_assets_are_covered_by_one_manifest_and_matching_preview_entry(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_distribution'),'Native release asset assembly is absent')
        builder=importlib.import_module('aikya.installation.managed_distribution')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source=root/'payload';payload(source);output=root/'release';output.mkdir()
            result=builder.finish(source,output,'8.0.0-alpha.0','darwin-arm64');self.assertTrue(Path(result['archive']).is_file());self.assertTrue(Path(result['bootstrap_archive']).is_file())
            hashes=parse_checksums((output/'SHA256SUMS').read_bytes())
            for name,checksum in hashes.items():self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(),checksum)
            self.assertIn('install.sh',hashes);record=json.loads((output/'terminal-bootstrap.json').read_bytes());self.assertEqual(record['platforms']['darwin-arm64']['sha256'],hashes[Path(result['bootstrap_archive']).name])
            if Path('/bin/sh').exists():
                process=subprocess.run(['/bin/sh',str(output/'install.sh'),'--dry-run'],capture_output=True,text=True,env={'PATH':'/nonexistent'})
                self.assertEqual(process.returncode,0,process.stderr);self.assertEqual(json.loads(process.stdout)['version'],'8.0.0-alpha.0')


if __name__=='__main__':unittest.main()
