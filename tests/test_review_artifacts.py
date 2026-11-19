"""Frozen check outputs stay private while actual bin/obj sources remain bound."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from aikya.review import executor
from aikya.review.candidates import freeze_candidate,store_candidate,is_current


class ArtifactChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();(self.root/'source.py').write_bytes(b'VALUE=1\n')

    def definition(self,script,args=None):
        return dict(name='build',argv=[sys.executable,'-I','-B','-c',script,*(args or [])],cwd='.',
                    report_format='process',timeout_seconds=20,max_output_bytes=65536)

    def freeze(self,definition,environment=None):
        binding=executor.check_binding(self.root,definition,environment)
        candidate=freeze_candidate(self.root,'artifact-check',['source.py'],session_id='author',
            policy=dict(checks=['build'],review_required=True,definitions={'build':binding},check_types={'build':'process'}))
        store_candidate(self.root,candidate,approved=True);return candidate

    def run_definition(self,definition,**extra):
        return executor.run_check(self.root,'artifact-check',definition,session_id='author',run_id='run-1',approved=True,**extra)

    def test_output_placeholder_expands_to_private_unique_execution_directory(self):
        definition=self.definition('import sys;from pathlib import Path;Path(sys.argv[1],"derived.cs").write_text("class Generated {}")',['{artifacts}'])
        candidate=self.freeze(definition);result=self.run_definition(definition)
        self.assertEqual(result['status'],'completed');self.assertIsNone(result['counts'])
        output=self.root/'.aikya/pi/check-artifacts/artifact-check/run-1/derived.cs'
        self.assertTrue(output.is_file());self.assertFalse((self.root/'{artifacts}').exists())
        self.assertTrue(is_current(self.root,candidate))

    def test_artifact_parent_symlink_is_refused_before_reserving_execution(self):
        definition=self.definition('raise AssertionError("Must not execute")',['{artifacts}']);self.freeze(definition)
        with tempfile.TemporaryDirectory() as outside:
            folder=self.root/'.aikya/pi/check-artifacts';folder.parent.mkdir(parents=True,exist_ok=True)
            try:folder.symlink_to(Path(outside),target_is_directory=True)
            except OSError:self.skipTest('Symlink creation unavailable')
            with self.assertRaises(ValueError):self.run_definition(definition)
            self.assertEqual(list(Path(outside).iterdir()),[])
            self.assertFalse((self.root/'aikya/docs/validation/artifact-check/checks/run-1').exists())

    def test_existing_artifact_data_is_preserved_before_launch(self):
        definition=self.definition('raise AssertionError("Must not execute")',['{artifacts}']);self.freeze(definition)
        folder=self.root/'.aikya/pi/check-artifacts/artifact-check/run-1';folder.mkdir(parents=True);(folder/'custom.txt').write_bytes(b'Keep')
        with self.assertRaises(ValueError):self.run_definition(definition)
        self.assertEqual((folder/'custom.txt').read_bytes(),b'Keep')

    def test_real_source_in_bin_and_obj_is_never_hidden(self):
        for name in ('bin/Business.cs','obj/ExplicitSource.cs'):
            path=self.root/name;path.parent.mkdir();path.write_bytes(b'class Business {}\n')
        definition=self.definition('pass');candidate=self.freeze(definition)
        self.assertIn('bin/Business.cs',candidate['files']);self.assertIn('obj/ExplicitSource.cs',candidate['files'])
        (self.root/'obj/ExplicitSource.cs').write_bytes(b'class Changed {}\n')
        self.assertFalse(is_current(self.root,candidate))

    def test_dotnet_build_without_owned_artifact_path_is_refused_read_only(self):
        definition=self.definition('pass');definition['argv']=['dotnet','build']
        with patch('aikya.review.definitions.shutil.which',return_value=sys.executable):
            with self.assertRaisesRegex(ValueError,'artifacts'):executor.check_binding(self.root,definition)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['source.py'])

    def test_conflicting_dotnet_output_flag_cannot_bypass_reviewed_path(self):
        definition=self.definition('pass');definition['argv']=['dotnet','build','--artifacts-path=elsewhere','{artifacts}']
        with patch('aikya.review.definitions.shutil.which',return_value=sys.executable):
            with self.assertRaisesRegex(ValueError,'artifacts'):executor.check_binding(self.root,definition)

    def test_windows_sdk_cache_directories_are_preserved_and_bound(self):
        from aikya.review.definitions import selected_environment
        values=dict(APPDATA=str(self.root/'Roaming'),LOCALAPPDATA=str(self.root/'Local'))
        definition=self.definition('pass')
        with patch.dict(os.environ,values):
            for name,value in values.items():self.assertEqual(selected_environment().get(name),value)
            before=executor.check_binding(self.root,definition)
            with patch.dict(os.environ,dict(LOCALAPPDATA=str(self.root/'Different'))):
                self.assertNotEqual(executor.check_binding(self.root,definition),before)

    def test_placeholder_suffix_cannot_escape_the_private_directory(self):
        definition=self.definition('pass',['{artifacts}/../../outside'])
        with self.assertRaisesRegex(ValueError,'artifacts'):executor.check_binding(self.root,definition)
        self.assertFalse((self.root/'.aikya').exists())

    @unittest.skipUnless(shutil.which('dotnet'),'A native .NET SDK is required')
    def test_actual_dotnet_build_preserves_the_source_candidate(self):
        dotnet=shutil.which('dotnet');home=self.root.parent/(self.root.name+'-sdk-home');home.mkdir();self.addCleanup(shutil.rmtree,home)
        local=home/'AppData/Local';roaming=home/'AppData/Roaming'
        local.mkdir(parents=True);roaming.mkdir(parents=True)
        environment=dict(HOME=str(home),USERPROFILE=str(home),LOCALAPPDATA=str(local),APPDATA=str(roaming),DOTNET_CLI_HOME=str(home),DOTNET_CLI_TELEMETRY_OPTOUT='1',
            DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_GENERATE_ASPNET_CERTIFICATE='false',DOTNET_NOLOGO='1',
            NUGET_PACKAGES=str(home/'packages'),MSBUILDDISABLENODEREUSE='1')
        sdks=subprocess.run([dotnet,'--list-sdks'],env={**os.environ,**environment},capture_output=True,text=True,timeout=15,check=True).stdout.splitlines()
        versions=[line.split()[0] for line in sdks if line.startswith('8.')]
        if not versions:self.skipTest('The offline acceptance requires an installed .NET 8 SDK/reference pack')
        (self.root/'global.json').write_text(json.dumps({'sdk':{'version':versions[-1],'rollForward':'disable'}}))
        (self.root/'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>')
        (self.root/'Evidence.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup></Project>')
        (self.root/'Value.cs').write_text('public class Value { public int Number => 1; }\n')
        definition=self.definition('pass');definition.update(argv=[dotnet,'build','Evidence.csproj','--artifacts-path','{artifacts}',
            '--disable-build-servers','--nologo','-p:UseSharedCompilation=false','-p:NuGetAudit=false',
            '-p:ImportDirectoryBuildProps=false','-p:ImportDirectoryBuildTargets=false'],timeout_seconds=90)
        candidate=self.freeze(definition,environment);captured=[];capture=executor.capture_process
        def observe(*args,**kwargs):
            observed,stdout=capture(*args,**kwargs);captured.append(dict(observed,stdout=stdout[:8192].decode('utf8',errors='replace')))
            return observed,stdout
        with patch.object(executor,'capture_process',side_effect=observe):
            result=self.run_definition(definition,environment=environment)
        fresh=freeze_candidate(self.root,'artifact-check',candidate['scope'],session_id='author',policy=candidate['policy'],parent=candidate['parent'])
        drift=sorted(p for p in candidate['files'].keys()|fresh['files'].keys() if candidate['files'].get(p)!=fresh['files'].get(p))
        self.assertEqual(result['status'],'completed',dict(result,changed_paths=drift,process=captured));self.assertIsNone(result['counts'])
        self.assertFalse((self.root/'bin').exists());self.assertFalse((self.root/'obj').exists())
        self.assertTrue(is_current(self.root,candidate))
        outputs=self.root/'.aikya/pi/check-artifacts/artifact-check/run-1'
        self.assertTrue(list(outputs.rglob('Evidence.dll')));self.assertTrue(list(outputs.rglob('*.g.cs')))


if __name__=='__main__':unittest.main()
