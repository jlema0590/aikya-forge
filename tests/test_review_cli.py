"""The support CLI previews snapshots and persists only after explicit approval."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ReviewCliTests(unittest.TestCase):
    def test_malformed_check_definition_is_a_bounded_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); (root / 'definition.json').write_text('{}')
            result = subprocess.run([sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'review',
                'snapshot', '--root', str(root), '--id', 'case', '--session', 'author', '--file', 'x.py',
                '--check-definition', 'definition.json'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)

    def test_cli_executes_only_a_bound_explicitly_approved_check(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); (root / 'code.py').write_text('VALUE = 1\n')
            (root / '.aikya/checks').mkdir(parents=True)
            script = ('import os;from pathlib import Path;'
                'Path(os.environ["AIKYA_TEST_REPORT"]).write_text(\'<testsuite tests="1"><testcase name="actual"/></testsuite>\')')
            definition = dict(name='tests', argv=[sys.executable, '-I', '-c', script], cwd='.',
                              report_format='junit', timeout_seconds=2, max_output_bytes=65536)
            (root / '.aikya/checks/unit.json').write_text(json.dumps(definition))
            command = [sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'review']
            shared = ['--root', str(root), '--id', 'check-1', '--session', 'author',
                      '--check-definition', '.aikya/checks/unit.json']
            result = subprocess.run([*command, 'snapshot', *shared, '--file', 'code.py', '--approved'],
                                    cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            run = [*command, 'run', *shared, '--run-id', 'run-1']
            result = subprocess.run(run, cwd=root, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / 'aikya/docs/validation/check-1/checks/run-1').exists())
            result = subprocess.run([*run, '--approved'], cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'completed')

    def test_preview_storage_and_stale_status_use_the_installed_entrypoint(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); (root / 'code.py').write_text('VALUE = 1\n')
            args = [sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'review',
                    'snapshot', '--root', str(root), '--id', 'change-1', '--session', 'author', '--file', 'code.py']
            result = subprocess.run(args, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['persisted'])
            self.assertFalse((root / 'aikya').exists())
            result = subprocess.run([*args, '--approved'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['persisted'])
            status = [sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'review',
                      'status', '--root', str(root), '--id', 'change-1']
            result = subprocess.run(status, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'pending_checks')
            (root / 'code.py').write_text('VALUE = 2\n')
            result = subprocess.run(status, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'stale')


if __name__ == '__main__': unittest.main()
