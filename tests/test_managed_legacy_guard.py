"""The v7 coordinator must not republish or remove native v8 application commands."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation.bootstrap import cli,state


class LegacyNativeGuardTests(unittest.TestCase):
    def test_legacy_mutations_refuse_native_activation_before_any_old_coordinator_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();(root/'terminal').mkdir();(root/'terminal/current.json').write_text('Native receipt requires native validation')
            for args in (['install','--mods','none','--version','7.2.2'],['update','--mods','none','--version','7.2.2'],['uninstall']):
                with self.subTest(args=args),patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(root)}),patch('aikya.installation.bootstrap.coordinator.execute',side_effect=AssertionError('Legacy mutation forbidden')):
                    errors=io.StringIO()
                    with contextlib.redirect_stderr(errors):result=cli.main(args)
                    self.assertEqual(result,2);self.assertIn('native',errors.getvalue().lower());self.assertEqual((root/'terminal/current.json').read_text(),'Native receipt requires native validation')


if __name__=='__main__':unittest.main()
