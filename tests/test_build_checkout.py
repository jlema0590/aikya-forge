"""Git checkout settings must not change packaged source identity across hosts."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from aikya.installation import managed_wheel

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('git'), 'Git is required for checkout acceptance')
class BuildCheckoutTests(unittest.TestCase):
    def test_autocrlf_checkout_keeps_runtime_identity_and_pinned_resource_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_ATTR_NOSYSTEM': '1',
                   'GIT_CONFIG_GLOBAL': 'NUL' if os.name == 'nt' else os.devnull}
            for key in tuple(env):
                if key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')) or key in (
                        'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_COUNT'):
                    env.pop(key)
            files = {name: b'canonical source\nsecond line\n' for name in managed_wheel.FILES}
            files.update({
                '.gitattributes': (ROOT / '.gitattributes').read_bytes(),
                'src/aikya/example.py': b'value = 1\n',
                'src/aikya/resources/pinned.md': b'pinned\r\nexact bytes\r\n',
                'src/aikya/resources/icon.bin': b'\x00\xff\r\n',
                'packages/aikya-pi/package.json': b'{"name":"fixture"}\n',
                'packages/aikya-pi/package-lock.json': b'{"lockfileVersion":3}\n',
                'packages/aikya-pi/src/project.ts': b'export const value = 1;\n',
            })
            for name, value in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
            spec = importlib.util.spec_from_file_location('checkout_release_gate', ROOT / 'scripts/ci/forge_release_gate.py')
            gate = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gate)
            expected = gate.runtime_fingerprint(root)
            for args in (['init', '--template='], ['-c', 'core.autocrlf=false', 'add', '--all'],
                         ['-c', 'core.autocrlf=true', 'checkout-index', '--all', '--force']):
                if 'checkout-index' in args:
                    for name in files:
                        (root / name).unlink()
                process = subprocess.run(['git', *args], cwd=root, env=env, capture_output=True, timeout=30)
                self.assertEqual(process.returncode, 0, process.stderr.decode(errors='replace'))
            self.assertEqual(gate.runtime_fingerprint(root), expected,
                             'Windows-style checkout changed the packaged runtime fingerprint')
            for name in ('src/aikya/resources/pinned.md', 'src/aikya/resources/icon.bin'):
                self.assertEqual((root / name).read_bytes(), files[name])


if __name__ == '__main__':
    unittest.main()
