"""A timed-out native test retains partial output and the failing step without success claims."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from managed_terminal_support import payload

ROOT=Path(__file__).resolve().parents[1]


class NativeAcceptanceDiagnostics(unittest.TestCase):
    def test_timeout_keeps_the_step_and_partial_process_output(self):
        script=ROOT/'scripts/ci/native_terminal_acceptance.py';spec=importlib.util.spec_from_file_location('native_acceptance_diagnostics',script)
        service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();bundle=root/'bundle';bundle.mkdir();sealed=payload(bundle/'payload','0.2.0')
            (bundle/'result.json').write_text(json.dumps(dict(version='0.2.0',platform='darwin-arm64',manifest_hash=sealed['manifest_hash'])))
            output=root/'acceptance.json';error=subprocess.TimeoutExpired(['synthetic-install'],1,output=b'partial build',stderr=b'partial error')
            with patch.object(service.managed_runtime,'host_platform',return_value='darwin-arm64'),patch.object(service.subprocess,'run',side_effect=error):
                with self.assertRaisesRegex(ValueError,'timed out'):service.run(bundle,output,work=root)
            value=json.loads(output.read_bytes());self.assertFalse(value['passed']);self.assertTrue(value['steps'][0]['timed_out'])
            self.assertEqual(value['steps'][0]['name'],'install');self.assertIsNone(value['steps'][0]['exit_code'])
            self.assertIn('partial error',(Path(value['work'])/'install.log').read_text(encoding='utf8'))


if __name__=='__main__':unittest.main()
