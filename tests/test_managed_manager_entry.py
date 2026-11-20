"""A retained Windows manager launches the currently verified core without replay."""
import importlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class ManagerEntryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.manager_entry'),'Verified manager forwarding is absent')
        self.entry=importlib.import_module('aikya.installation.manager_entry')

    def test_verified_current_interpreter_receives_exact_arguments_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();target=root/'current python'
            with patch.object(self.entry,'windows',return_value=True),patch.object(self.entry,'application',return_value=root),\
                 patch.object(self.entry,'selected_python',return_value=str(target)),\
                 patch.object(self.entry.subprocess,'run',return_value=type('Result',(),{'returncode':4})()) as process:
                self.assertEqual(self.entry.main(['update','--version','0.3.0','--yes']),4)
                self.assertEqual(process.call_count,1)
                self.assertEqual(process.call_args.args[0],[str(target),'-I','-B','-m','aikya.installation.managed_cli','update','--version','0.3.0','--yes'])

    def test_windows_running_executable_uninstall_is_refused_before_effects(self):
        with patch.object(self.entry,'windows',return_value=True),patch.object(self.entry,'selected_python',side_effect=AssertionError('No payload effects')):
            with patch('sys.stderr',io.StringIO()):self.assertEqual(self.entry.main(['uninstall','--yes']),2)

    def test_unverified_current_payload_never_falls_back_to_old_core(self):
        with patch.object(self.entry,'windows',return_value=True),patch.object(self.entry,'application',return_value=Path('/unused')),\
             patch.object(self.entry,'selected_python',side_effect=ValueError('Changed payload')),patch.object(self.entry.subprocess,'run') as process:
            with patch('sys.stderr',io.StringIO()):self.assertEqual(self.entry.main(['doctor']),2)
            process.assert_not_called()


if __name__=='__main__':unittest.main()
