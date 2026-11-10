"""Version-pinned native entry scripts can preview and refuse corruption without Python."""
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import io
import tarfile
import unittest
from aikya.installation.managed_runtime import host_platform


class NativeBootstrapEntryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_entries'),'Native no-Python bootstrap generation is absent')
        self.entries=importlib.import_module('aikya.installation.managed_entries');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.assets=self.root/'assets';self.assets.mkdir()
        self.name='aikya-terminal-8.0.0-alpha.0-'+host_platform()+('.zip' if os.name=='nt' else '.tar.gz');self.raw=b'Transport fixture, never executed';(self.assets/self.name).write_bytes(self.raw)
        (self.assets/'SHA256SUMS').write_text(hashlib.sha256(self.raw).hexdigest()+'  '+self.name+'\n')

    @unittest.skipIf(os.name=='nt','Shell entry acceptance runs on POSIX')
    def test_shell_preview_needs_no_python_node_git_or_application_files(self):
        output=self.root/'entries';self.entries.build('8.0.0-alpha.0',self.assets,output)
        result=subprocess.run(['/bin/sh',str(output/'install.sh'),'--dry-run'],env={'PATH':'/nonexistent','AIKYA_INSTALL_ROOT':str(self.root/'app')},capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);value=json.loads(result.stdout);self.assertFalse(value['writes']);self.assertFalse(value['network']);self.assertEqual(value['version'],'8.0.0-alpha.0');self.assertFalse((self.root/'app').exists())

    @unittest.skipIf(os.name=='nt','Shell entry acceptance runs on POSIX')
    def test_corrupt_offline_payload_fails_before_extraction_or_interpreter_execution(self):
        output=self.root/'entries';self.entries.build('8.0.0-alpha.0',self.assets,output);(self.assets/self.name).write_bytes(b'Corrupt data')
        result=subprocess.run(['/bin/sh',str(output/'install.sh'),'--offline-dir',str(self.assets),'--no-path'],env={**os.environ,'AIKYA_INSTALL_ROOT':str(self.root/'app')},capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('checksum',result.stderr.lower());self.assertFalse((self.root/'app').exists());self.assertEqual((self.assets/self.name).read_bytes(),b'Corrupt data')

    @unittest.skipIf(os.name=='nt','Shell temporary-directory behavior runs on POSIX')
    def test_os_temporary_directory_alias_is_canonicalized_before_calling_the_installer(self):
        from aikya.installation.managed_inputs import load
        interpreter='python/'+load()['python']['executable'];raw=b'#!/bin/sh\nprintf "%s\\n" "$0"\n'
        archive=self.assets/self.name
        with tarfile.open(archive,'w:gz') as container:
            member=tarfile.TarInfo(interpreter);member.size=len(raw);member.mode=0o700;container.addfile(member,io.BytesIO(raw))
        (self.assets/'SHA256SUMS').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+self.name+'\n')
        output=self.root/'entries';self.entries.build('8.0.0-alpha.0',self.assets,output)
        physical=self.root/'physical temporary';physical.mkdir();alias=self.root/'alias';alias.symlink_to(physical,target_is_directory=True)
        result=subprocess.run(['/bin/sh',str(output/'install.sh'),'--offline-dir',str(self.assets),'--no-path'],env={**os.environ,'TMPDIR':str(alias)},capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(result.stdout.startswith(str(physical)),result.stdout);self.assertEqual(list(physical.iterdir()),[])

    def test_modified_assets_or_custom_entry_output_are_preserved(self):
        output=self.root/'entries';(self.assets/self.name).write_bytes(b'Changed')
        with self.assertRaises(ValueError):self.entries.build('8.0.0-alpha.0',self.assets,output)
        self.assertFalse(output.exists());(self.assets/self.name).write_bytes(self.raw);output.mkdir();custom=output/'custom';custom.write_text('User data')
        with self.assertRaises(ValueError):self.entries.build('8.0.0-alpha.0',self.assets,output)
        self.assertEqual(custom.read_text(),'User data')

    def test_windows_entry_contains_only_available_pinned_platforms_and_no_python_discovery(self):
        name='aikya-terminal-8.0.0-alpha.0-win32-x64.zip'
        if not (self.assets/name).exists():
            (self.assets/name).write_bytes(self.raw)
            with (self.assets/'SHA256SUMS').open('a') as stream:stream.write(hashlib.sha256(self.raw).hexdigest()+'  '+name+'\n')
        output=self.root/'entries';self.entries.build('8.0.0-alpha.0',self.assets,output);script=(output/'install.ps1').read_text()
        self.assertIn(name,script);self.assertEqual('win32-arm64.zip' in script,self.name.endswith('win32-arm64.zip'));self.assertNotIn('Get-Command python',script);self.assertIn(hashlib.sha256(self.raw).hexdigest(),script)


if __name__=='__main__':unittest.main()
