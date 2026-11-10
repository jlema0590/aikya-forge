"""Native diagnostics reuse canonical contracts without inference or project effects."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
try:diagnostics=importlib.import_module('aikya.services.diagnostics')
except ModuleNotFoundError:diagnostics=None


class LocalDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(diagnostics,'Native local diagnostics are absent')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()

    def profile(self,**fields):
        path=self.root/'.harness/project-profile.json';path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(dict(decisions=dict(project_type='development',methodology='odd',backend='python',**fields))))

    def test_doctor_distinguishes_missing_profile_presence_and_unverified_compatibility(self):
        with patch('subprocess.run',side_effect=AssertionError('No executable may run')):
            empty=diagnostics.doctor(self.root)
        self.assertEqual(empty['profile']['status'],'unconfigured')
        self.assertEqual(empty['compatibility'],'not_verified');self.assertIsNone(empty['ready'])
        self.assertEqual(list(self.root.iterdir()),[])
        self.profile(mobile='android',mobile_framework='flutter')
        with patch('subprocess.run',side_effect=AssertionError('No executable may run')):
            value=diagnostics.doctor(self.root)
        self.assertIn('flutter',[item['tool'] for item in value['toolchains']])
        self.assertTrue(all(item['version'] is None for item in value['toolchains']))
        self.assertEqual(value['effects'],'none')
        self.assertEqual(sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()),['.harness/project-profile.json'])

    def test_doctor_uses_profile_requirements_without_exposing_environment_or_paths(self):
        self.profile(mobile='ios',mobile_framework='native')
        with patch('aikya.services.diagnostics.shutil.which',return_value='/private/FAKE_PRIVATE/bin/tool'),patch('aikya.services.diagnostics.platform.system',return_value='Linux'):
            result=diagnostics.doctor(self.root)
        items={item['tool']:item for item in result['toolchains']}
        self.assertEqual(items['git']['presence'],'found');self.assertEqual(items['xcodebuild']['presence'],'unsupported_host')
        self.assertNotIn('FAKE_PRIVATE',json.dumps(result));self.assertNotIn('environ',json.dumps(result))

    def test_custom_or_malformed_profile_is_preserved_and_not_reported_healthy(self):
        path=self.root/'.harness/project-profile.json';path.parent.mkdir();path.write_text('{"decisions": {"backend":"unknown","methodology":"odd"}}')
        result=diagnostics.doctor(self.root)
        self.assertEqual(result['profile']['status'],'invalid');self.assertIsNone(result['ready'])
        path.write_text('{"decisions":{},"decisions":{}}')
        self.assertEqual(diagnostics.doctor(self.root)['profile']['status'],'invalid')
        self.assertEqual(path.read_text(),'{"decisions":{},"decisions":{}}')

    def test_static_quality_reuses_python_syntax_and_file_size_checks_with_hashes(self):
        (self.root/'bad.py').write_text('def broken(:\n pass\n')
        (self.root/'large.dart').write_text('// comment\n'*1001)
        before={p.name:p.read_bytes() for p in self.root.iterdir()}
        value=diagnostics.quality(self.root,['bad.py','large.dart'])
        self.assertEqual(value['status'],'issues_found');self.assertEqual(value['files'],2)
        self.assertEqual({item['code'] for item in value['errors']},{'python_syntax','file_too_large'})
        self.assertEqual(value['coverage']['large.dart'],'physical_lines_only')
        self.assertEqual(value['coverage']['bad.py'],'python_ast_and_physical_lines')
        self.assertEqual(len(value['scope_revision']),64)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
        self.assertEqual(value['security'],'not_run');self.assertEqual(value['tests'],'not_run')

    def test_unknown_empty_duplicate_secret_link_and_oversize_inputs_are_refused(self):
        (self.root/'good.py').write_text('pass\n');(self.root/'.env.py').write_text('PRIVATE_MARKER')
        (self.root/'linked.py').symlink_to(self.root/'good.py')
        (self.root/'large.py').write_bytes(b'x'*1000001)
        for paths in ([],['good.py','good.py'],['.env.py'],['linked.py'],['large.py'],['missing.py'],['../good.py'],['good.py']*21):
            with self.subTest(paths=paths):
                with self.assertRaises((ValueError,OSError)):diagnostics.quality(self.root,paths)
        (self.root/'a.txt').write_text('not source')
        with self.assertRaises(ValueError):diagnostics.quality(self.root,['a.txt'])

    def test_static_quality_preserves_reviewed_exceptions_without_claiming_security(self):
        import hashlib
        (self.root/'large.ts').write_text('// comment\n'*1001)
        path=self.root/'.aikya/code-quality-exceptions.json';path.parent.mkdir()
        path.write_text(json.dumps(dict(schema=1,exceptions=[dict(path='large.ts',sha256=hashlib.sha256((self.root/'large.ts').read_bytes()).hexdigest(),reason='Reviewed generated client; preserved for compatibility.')])) )
        value=diagnostics.quality(self.root,['large.ts'])
        self.assertEqual(value['errors'],[]);self.assertEqual(value['warnings'][0]['code'],'reviewed_size_exception')
        self.assertEqual(value['status'],'issues_found');self.assertFalse(value['truncated'])
        (self.root/'large.ts').write_text('// changed\n'*1001)
        self.assertEqual(diagnostics.quality(self.root,['large.ts'])['errors'][0]['code'],'file_too_large')

    def test_findings_and_aggregate_inputs_are_bounded(self):
        paths=[]
        for n in range(20):
            name=str(n)+'.py';paths.append(name)
            (self.root/name).write_text('def many():\n'+'    pass\n'*101+'\ndef broken(:\n')
        result=diagnostics.quality(self.root,paths)
        self.assertLessEqual(len(result['errors'])+len(result['warnings']),20)
        for path in paths[:3]:(self.root/path).write_bytes(b'x'*700000)
        with self.assertRaises(ValueError):diagnostics.quality(self.root,paths[:3])

    def test_quality_inspects_frozen_bytes_despite_later_source_changes(self):
        (self.root/'candidate.py').write_text('def broken(:\n')
        from aikya.quality import source
        original=source.inspect_paths
        def inspect(root,paths):
            (self.root/'candidate.py').write_text('pass\n')
            return original(root,paths)
        with patch.object(source,'inspect_paths',side_effect=inspect):
            result=diagnostics.quality(self.root,['candidate.py'])
        self.assertEqual(result['errors'][0]['code'],'python_syntax')
        self.assertEqual((self.root/'candidate.py').read_text(),'pass\n')

    def test_every_indexed_language_has_explicit_static_coverage(self):
        from aikya.code_index.policy import CODE_SUFFIXES
        for suffix in sorted(CODE_SUFFIXES):
            with self.subTest(suffix=suffix):
                name='example'+suffix;(self.root/name).write_text('pass\n' if suffix in ('.py','.pyi') else '// fixture\n')
                value=diagnostics.quality(self.root,[name])
                self.assertEqual(value['files'],1);self.assertEqual(value['status'],'no_static_findings')
        (self.root/'bad.pyi').write_text('def broken(:\n')
        self.assertEqual(diagnostics.quality(self.root,['bad.pyi'])['errors'][0]['code'],'python_syntax')

    def test_duplicate_location_output_does_not_overflow_the_host_bridge(self):
        paths=[]
        for n in range(20):
            name=('x'*185)+str(n)+'.py';paths.append(name)
            text=''
            for group in range(20):
                text+='def function_'+str(group)+'():\n'+''.join('    value = '+str(group*10+i)+'\n' for i in range(11))+'    return value\n\n'
            (self.root/name).write_text(text)
        value=diagnostics.quality(self.root,paths)
        self.assertLess(len(json.dumps(value).encode()),50000)
        self.assertTrue(value['truncated'])
        self.assertEqual(value['warning_count'],20)
        self.assertTrue(all(item['locations_total']==20 for item in value['warnings']))

    def test_python_support_uses_the_packaged_minimum_not_legacy_sdk_minimum(self):
        with patch('aikya.services.diagnostics.sys.version_info',(3,9,20)):
            self.assertFalse(diagnostics.doctor(self.root)['host']['python_supported'])
