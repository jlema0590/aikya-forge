"""PR acceptance cannot hide incomplete checks or a main publication refusal."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/ci/pr_acceptance.py'


class PullRequestAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(),'A complete PR acceptance decision is missing')
        spec=importlib.util.spec_from_file_location('pr_acceptance',SCRIPT)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.results={name:dict(result='success',outputs={}) for name in
                      ('contracts','python','runtime','installers','native','publication')}

    def test_main_requires_success_from_every_stage(self):
        self.assertEqual(self.module.evaluate(self.results,'main')['status'],'passed')
        for name in self.results:
            for status in ('failure','cancelled','skipped','unknown'):
                with self.subTest(stage=name,status=status):
                    values={**self.results,name:dict(result=status)}
                    self.assertEqual(self.module.evaluate(values,'main')['status'],'failed')

    def test_develop_only_allows_publication_to_be_skipped(self):
        self.results['publication']['result']='skipped'
        result=self.module.evaluate(self.results,'develop')
        self.assertEqual(result['status'],'passed')
        failed={**self.results,'publication':dict(result='failure')}
        self.assertEqual(self.module.evaluate(failed,'develop')['status'],'failed')
        for name in ('contracts','python','runtime','installers','native'):
            with self.subTest(stage=name):
                values={**self.results,name:dict(result='skipped')}
                self.assertEqual(self.module.evaluate(values,'develop')['status'],'failed')

    def test_missing_extra_malformed_results_or_unknown_base_fail_closed(self):
        for values in ({},None,[],{**self.results,'unreviewed':dict(result='success')},
                       {**self.results,'native':None},{**self.results,'python':dict(outputs={})}):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):self.module.evaluate(values,'develop')
        with self.assertRaises(ValueError):self.module.evaluate(self.results,'other')

    def test_cli_records_real_failure_and_preserves_main_publication_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary=Path(temporary)/'summary.md'
            self.results['publication']['result']='failure'
            env={**os.environ,'AIKYA_PR_NEEDS':json.dumps(self.results),'GITHUB_STEP_SUMMARY':str(summary)}
            result=subprocess.run([sys.executable,'-B',SCRIPT,'--base','main'],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'failed')
            self.assertIn('publication',summary.read_text());self.assertIn('failure',summary.read_text())
            self.results['publication']['result']='skipped';env['AIKYA_PR_NEEDS']=json.dumps(self.results)
            result=subprocess.run([sys.executable,'-B',SCRIPT,'--base','develop'],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'passed')


if __name__=='__main__':unittest.main()
