"""Interrupted native promotions may reconcile complete effects, never replay probes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation import managed_install,managed_runtime,managed_ownership
from managed_terminal_support import payload,snapshot


class ManagedRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(managed_install,'recover',None)),'Reviewed native reconciliation is absent')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve();self.root=self.base/'application';self.source=self.base/'source';payload(self.source)
        platform=patch.object(managed_runtime,'host_platform',return_value='darwin-arm64');platform.start();self.addCleanup(platform.stop)
        probe=patch('aikya.installation.managed_probe.check',return_value={'status':'passed'});self.probe=probe.start();self.addCleanup(probe.stop)

    def test_complete_promoted_effects_are_reconciled_without_executing_again(self):
        save=managed_ownership.save
        def interrupt(root,relative,value):
            if relative.startswith('terminal/operations/') and value.get('status')=='complete':raise OSError('Simulated final log storage failure')
            return save(root,relative,value)
        plan=managed_install.preview(self.root,self.source)
        with patch.object(managed_ownership,'save',side_effect=interrupt):
            with self.assertRaises(OSError):managed_install.apply(plan,approved=True)
        self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.0');calls=self.probe.call_count
        self.assertEqual(managed_install.recover(self.root,approved=True)['status'],'reconciled');self.assertEqual(self.probe.call_count,calls)
        self.assertFalse((self.root/'terminal/pending.json').exists());self.assertEqual(len(list((self.root/'terminal/operations').glob('*.json'))),1)

    def test_partial_or_customized_effects_are_preserved_without_replay(self):
        with patch('aikya.installation.managed_launchers.publish',side_effect=OSError('Simulated incomplete promotion')):
            with self.assertRaises(OSError):managed_install.apply(managed_install.preview(self.root,self.source),approved=True)
        self.assertFalse((self.root/'terminal/current.json').exists());before=snapshot(self.root);calls=self.probe.call_count
        with self.assertRaises(ValueError):managed_install.recover(self.root,approved=True)
        self.assertEqual(snapshot(self.root),before);self.assertEqual(self.probe.call_count,calls)
        with self.assertRaises(ValueError):managed_install.preview(self.root,self.source)

    def test_missing_approval_never_changes_an_interrupted_operation(self):
        with patch('aikya.installation.managed_launchers.publish',side_effect=OSError('Disk failure')):
            with self.assertRaises(OSError):managed_install.apply(managed_install.preview(self.root,self.source),approved=True)
        before=snapshot(self.root)
        with self.assertRaises(ValueError):managed_install.recover(self.root)
        self.assertEqual(snapshot(self.root),before)


if __name__=='__main__':unittest.main()
