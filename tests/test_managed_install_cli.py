"""Administrative CLI previews stay inert; committed native actions use one root."""
import contextlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation import managed_runtime
from managed_terminal_support import payload,snapshot


class NativeInstallCliTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_cli'),'Native administrative CLI is absent')
        self.cli=importlib.import_module('aikya.installation.managed_cli');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve();self.root=self.base/'application';self.source=self.base/'source';payload(self.source)
        for item in (patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(self.root)}),patch.object(managed_runtime,'host_platform',return_value='darwin-arm64'),patch('aikya.installation.managed_probe.check',return_value={'status':'passed'})):
            item.start();self.addCleanup(item.stop)

    def invoke(self,args):
        output=io.StringIO();errors=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):code=self.cli.main(args)
        return code,output.getvalue(),errors.getvalue()

    def test_default_preview_and_dry_run_never_download_or_initialize_application(self):
        with patch('aikya.installation.bootstrap.download.https_bytes',side_effect=AssertionError('Network forbidden')):
            for args in (['install','--channel','preview'],['install','--dry-run','--version','8.0.0-alpha.0','--channel','preview'],['install','--payload',str(self.source)]):
                result=self.invoke(args);self.assertEqual(result[0],0,result[2]);self.assertFalse(json.loads(result[1])['writes']);self.assertFalse(self.root.exists())

    def test_local_install_doctor_and_uninstall_have_clear_observed_results(self):
        result=self.invoke(['install','--payload',str(self.source),'--yes','--no-path']);self.assertEqual(result[0],0,result[2]);self.assertEqual(json.loads(result[1])['status'],'installed')
        code,output,error=self.invoke(['doctor']);self.assertEqual(code,0,error);self.assertTrue(json.loads(output)['installed'])
        result=self.invoke(['uninstall','--yes']);self.assertEqual(result[0],0,result[2]);self.assertEqual(json.loads(result[1])['status'],'uninstalled')

    def test_payload_identity_mismatch_and_project_binary_scope_are_errors_without_effects(self):
        for args in (['install','--payload',str(self.source),'--version','8.0.0-alpha.1','--channel','preview','--yes','--no-path'],['install','--scope','project','--yes']):
            result=self.invoke(args);self.assertEqual(result[0],2);self.assertIn('ERROR:',result[2]);self.assertFalse(self.root.exists())

    def test_repeating_the_one_command_install_or_current_update_is_an_inert_success(self):
        command=['install','--payload',str(self.source),'--yes','--no-path']
        result=self.invoke(command);self.assertEqual(result[0],0,result[2]);before=snapshot(self.root)
        for action in ('install','update'):
            result=self.invoke([action,*command[1:]]);self.assertEqual(result[0],0,result[2]);self.assertEqual(json.loads(result[1])['status'],'up-to-date');self.assertEqual(snapshot(self.root),before)

    def test_installing_a_newer_private_release_uses_the_existing_owned_update_path(self):
        result=self.invoke(['install','--payload',str(self.source),'--yes','--no-path']);self.assertEqual(result[0],0,result[2])
        newer=self.base/'newer';payload(newer,'8.0.0-alpha.1')
        result=self.invoke(['install','--payload',str(newer),'--yes','--no-path']);self.assertEqual(result[0],0,result[2]);self.assertEqual(json.loads(result[1])['status'],'updated')


if __name__=='__main__':unittest.main()
