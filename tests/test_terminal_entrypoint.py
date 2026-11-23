"""Development terminal launch is explicit and uses argument lists, never a shell."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(shutil.which('node'), 'Node is required for development terminal launch')
class TerminalEntrypointTests(unittest.TestCase):
    def test_preview_binds_project_python_and_explicit_runtime_without_writes(self):
        with tempfile.TemporaryDirectory(prefix='aikya terminal ') as folder:
            root = Path(folder).resolve(); runtime = root / 'runtime'; project = root / 'project'; project.mkdir()
            (runtime / 'src').mkdir(parents=True)
            (runtime / 'package.json').write_text(json.dumps({'name': '@aikya/pi-runtime', 'version': '8.0.0-alpha.0'}))
            (runtime / 'src/launcher.ts').write_text('// Operator-selected runtime fixture.\n')
            args = [sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'terminal',
                    '--runtime-dir', str(runtime), '--target', str(project), '--print-command']
            result = subprocess.run(args, cwd=project, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            command = json.loads(result.stdout)['command']
            self.assertEqual(command[1:3], ['--experimental-strip-types', str(runtime / 'src/launcher.ts')])
            self.assertEqual(command[3:], ['--target', str(project), '--python', sys.executable])
            self.assertEqual(list(project.iterdir()), [])

    def test_explicit_provider_and_model_are_forwarded_without_initializing_or_inference(self):
        from aikya.cli.terminal import command_for
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve(); runtime=root/'runtime'; project=root/'project'; project.mkdir()
            (runtime/'src').mkdir(parents=True)
            (runtime/'package.json').write_text(json.dumps({'name':'@aikya/pi-runtime','version':'8.0.0-alpha.0'}))
            (runtime/'src/launcher.ts').write_text('// Operator-selected runtime fixture.\n')
            command=command_for(project,runtime,provider='fixture',model='fixture-model')
            self.assertEqual(command[-4:],['--provider','fixture','--model','fixture-model'])
            with self.assertRaises(ValueError): command_for(project,runtime,provider='fixture')
            self.assertEqual(list(project.iterdir()),[])

    def test_canonical_private_development_versions_are_accepted_without_project_effects(self):
        from aikya.cli.terminal import command_for
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();runtime=root/'runtime';project=root/'project';project.mkdir()
            (runtime/'src').mkdir(parents=True)
            (runtime/'package.json').write_text(json.dumps({'name':'@aikya/pi-runtime','version':'8.0.0-beta.1'}))
            (runtime/'src/launcher.ts').write_text('// Explicit development source.\n')
            command=command_for(project,runtime)
            self.assertEqual(command[2],str(runtime/'src/launcher.ts'));self.assertEqual(list(project.iterdir()),[])

    def test_a_foreign_runtime_is_rejected_without_initializing_a_project(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); (root / 'package.json').write_text('{"name":"foreign"}')
            (root / 'src').mkdir(); (root / 'src/launcher.ts').write_text('// Not an Aikya runtime\n')
            result = subprocess.run([sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'terminal',
                '--runtime-dir', str(root), '--target', str(root), '--print-command'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse((root / '.aikya').exists())
            (root / 'package.json').write_text('[]')
            result = subprocess.run([sys.executable, '-I', '-B', '-m', 'aikya.cli.main', 'terminal',
                '--runtime-dir', str(root), '--target', str(root), '--print-command'], capture_output=True, text=True)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__': unittest.main()
