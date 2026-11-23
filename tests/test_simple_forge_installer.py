"""The short entry delegates only a checksum-matched native installer."""
import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name=='nt','POSIX bootstrap acceptance; Windows has the PowerShell entry')
class SimpleForgeInstallerTests(unittest.TestCase):
    def run_entry(self,*args):
        path=ROOT/'install.sh';self.assertTrue(path.is_file(),'Simple Forge entry is absent')
        return subprocess.run(['/bin/sh',str(path),*map(str,args)],capture_output=True,text=True,timeout=10)

    def test_preview_has_no_network_or_application_effects(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp).resolve();before=list(p.iterdir())
            result=self.run_entry('--dry-run')
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(result.stdout);self.assertEqual(value['product'],'aikya-forge');self.assertEqual(value['release'],'latest')
            self.assertFalse(value['network']);self.assertFalse(value['writes']);self.assertEqual(list(p.iterdir()),before)

    def test_verified_offline_entry_receives_arguments_without_shell_interpretation(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp).resolve();raw=b'#!/bin/sh\nprintf "delegated:%s:%s\\n" "$1" "$2"\n'
            (p/'install.sh').write_bytes(raw);(p/'SHA256SUMS').write_text(hashlib.sha256(raw).hexdigest()+'  install.sh\n')
            result=self.run_entry('--offline-dir',p,'--no-path')
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('delegated:--offline-dir:',result.stdout)

    def test_short_entry_reaches_the_real_version_bound_native_entry(self):
        import io,shutil,tarfile
        from aikya.installation import managed_entries,managed_inputs,managed_runtime
        with tempfile.TemporaryDirectory(prefix='forge assets $() ') as temp:
            p=Path(temp).resolve();assets=p/'assets';assets.mkdir()
            target=managed_runtime.host_platform()
            name='aikya-terminal-0.2.0-'+target+'.tar.gz'
            interpreter='python/'+managed_inputs.load()['python']['executable']
            raw=b'#!/bin/sh\nprintf "native:%s\\n" "$@"\n'
            with tarfile.open(assets/name,'w:gz') as archive:
                member=tarfile.TarInfo(interpreter);member.size=len(raw);member.mode=0o700
                archive.addfile(member,io.BytesIO(raw))
            digest=hashlib.sha256((assets/name).read_bytes()).hexdigest()
            (assets/'SHA256SUMS').write_text(digest+'  '+name+'\n')
            entries=p/'entries';managed_entries.build('0.2.0',assets,entries)
            shutil.copyfile(entries/'install.sh',assets/'install.sh')
            digest=hashlib.sha256((assets/'install.sh').read_bytes()).hexdigest()
            with (assets/'SHA256SUMS').open('a') as stream:stream.write(digest+'  install.sh\n')
            result=self.run_entry('--offline-dir',assets,'--no-path')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('native:aikya.installation.managed_cli',result.stdout)
            self.assertIn('native:0.2.0',result.stdout)
            self.assertIn('native:'+str(assets),result.stdout)

    def test_corrupt_or_ambiguous_entry_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp).resolve();marker=p/'executed';raw=('#!/bin/sh\ntouch "'+str(marker)+'"\n').encode()
            (p/'install.sh').write_bytes(raw);(p/'SHA256SUMS').write_text('0'*64+'  install.sh\n')
            result=self.run_entry('--offline-dir',p);self.assertNotEqual(result.returncode,0);self.assertFalse(marker.exists())
            digest=hashlib.sha256(raw).hexdigest();(p/'SHA256SUMS').write_text((digest+'  install.sh\n')*2)
            result=self.run_entry('--offline-dir',p);self.assertNotEqual(result.returncode,0);self.assertFalse(marker.exists())


@unittest.skipUnless(__import__('shutil').which('pwsh') or os.name=='nt','PowerShell acceptance runs on Windows CI')
class SimpleForgePowerShellTests(unittest.TestCase):
    def run_entry(self,*args):
        import shutil
        path=ROOT/'install.ps1';self.assertTrue(path.is_file(),'Simple Windows entry is absent')
        return subprocess.run([shutil.which('pwsh') or 'powershell','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(path),*map(str,args)],capture_output=True,text=True,timeout=15)

    def test_preview_is_local(self):
        result=self.run_entry('-DryRun');self.assertEqual(result.returncode,0,result.stderr)
        value=json.loads(result.stdout);self.assertEqual(value['product'],'aikya-forge');self.assertFalse(value['network']);self.assertFalse(value['writes'])

    def test_only_verified_entry_runs_and_arguments_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp).resolve();marker=p/'executed';raw=b'param([string]$OfflineDir,[switch]$NoPath,[string]$Scope,[string]$Channel,[string]$Action)\nWrite-Output ("delegated:"+$OfflineDir+":"+$NoPath)\n'
            (p/'install.ps1').write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
            (p/'SHA256SUMS').write_text(digest+'  install.ps1\n')
            result=self.run_entry('-OfflineDir',p,'-NoPath');self.assertEqual(result.returncode,0,result.stderr);self.assertIn('delegated:'+str(p)+':True',result.stdout)
            raw=('New-Item -ItemType File -Path "'+str(marker)+'"\n').encode();(p/'install.ps1').write_bytes(raw)
            result=self.run_entry('-OfflineDir',p);self.assertNotEqual(result.returncode,0);self.assertFalse(marker.exists())
            digest=hashlib.sha256(raw).hexdigest();(p/'SHA256SUMS').write_text((digest+'  install.ps1\n')*2)
            result=self.run_entry('-OfflineDir',p);self.assertNotEqual(result.returncode,0);self.assertFalse(marker.exists())


if __name__=='__main__':unittest.main()
