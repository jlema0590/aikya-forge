"""Forge Pages copies only checksum-bound entries of the expected published source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from aikya.installation.managed_inputs import TARGETS

ROOT=Path(__file__).resolve().parents[1]


class ForgeInstallPagesTests(unittest.TestCase):
    def test_exact_entries_and_source_are_required_before_any_output(self):
        script=ROOT/'scripts/ci/forge_install_pages.py'
        self.assertTrue(script.is_file(),'Forge-specific native Pages builder absent')
        spec=importlib.util.spec_from_file_location('forge_install_pages',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();assets=root/'assets';assets.mkdir();hashes={}
            values={'install.sh':b'#!/bin/sh\nexit 0\n','install.ps1':b"Write-Output 'native'\n",
                'release.json':json.dumps(dict(version='0.2.0',source_commit='a'*40)).encode(),
                'terminal-bootstrap.json':json.dumps(dict(version='0.2.0',channel='stable',platforms={p:{} for p in TARGETS},
                    entries={n:hashlib.sha256(v).hexdigest() for n,v in {'install.sh':b'#!/bin/sh\nexit 0\n','install.ps1':b"Write-Output 'native'\n"}.items()})).encode()}
            for name,raw in values.items():(assets/name).write_bytes(raw);hashes[name]=hashlib.sha256(raw).hexdigest()
            (assets/'SHA256SUMS').write_text(''.join(v+'  '+n+'\n' for n,v in hashes.items()))
            with self.assertRaises(ValueError):module.build('0.2.0',assets,root/'bad','b'*40)
            self.assertFalse((root/'bad').exists())
            module.build('0.2.0',assets,root/'site','a'*40)
            self.assertEqual((root/'site/install.ps1.txt').read_bytes(),values['install.ps1'])
            self.assertEqual((root/'site/install.sh').read_bytes(),values['install.sh'])
            self.assertIn('Aikya Forge',(root/'site/index.html').read_text())
            (assets/'install.sh').write_bytes(b'changed')
            with self.assertRaises(ValueError):module.build('0.2.0',assets,root/'corrupt','a'*40)
            self.assertFalse((root/'corrupt').exists())


if __name__=='__main__':unittest.main()
