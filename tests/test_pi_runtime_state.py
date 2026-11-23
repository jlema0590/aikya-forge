"""Trusted runtime state entry point keeps accounting separate from model tools."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class RuntimeStateTests(unittest.TestCase):
    def test_installed_host_entrypoint_reserves_records_and_reads_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            def invoke(action, arguments):
                result = subprocess.run([sys.executable, '-I', '-B', '-m', 'aikya.services.runtime_state', '--root', str(root)],
                    input=json.dumps(dict(action=action, arguments=arguments)), text=True, capture_output=True,
                    env={**os.environ, 'AIKYA_TRUSTED_RUNTIME': '1'}, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            self.assertEqual(invoke('status', {})['result']['status'], 'unconfigured')
            self.assertFalse((root / '.aikya').exists())
            self.assertTrue(invoke('configure', dict(tokens=100, calls=3, approved=True))['ok'])
            context=dict(session='a', role='author', phase='implement', provider='fixture', model='fixture')
            self.assertTrue(invoke('admit', dict(call_id='one', context=context))['ok'])
            self.assertTrue(invoke('record', dict(call_id='one', counts=dict(input=1, output=2, cacheRead=0, cacheWrite=0)))['ok'])
            self.assertEqual(invoke('status', {})['result']['recorded_tokens'], 3)


if __name__ == '__main__': unittest.main()
