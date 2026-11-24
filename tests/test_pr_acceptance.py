"""Technical PR acceptance remains mandatory; publication readiness stays truthful."""
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
        spec=importlib.util.spec_from_file_location('pr_acceptance',SCRIPT)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def results(self,base='main'):
        result={name:dict(result='success',outputs={}) for name in
                ('route','contracts','python','runtime','installers','native','publication')}
        result['route']['outputs']={'analyze':'true','context':'Forge PR acceptance | '+base}
        result['publication']['outputs']={'status':'blocked','ready':'false'}
        return result

    def test_every_technical_stage_and_readiness_report_must_complete(self):
        for name in self.results():
            for status in ('failure','cancelled','abandoned','skipped','unknown'):
                with self.subTest(stage=name,status=status):
                    values={**self.results(),name:dict(result=status,outputs={})}
                    self.assertEqual(self.module.evaluate(values,'main')['status'],'failed')

    def test_pending_trials_do_not_block_integration_or_claim_publication(self):
        for base in ('develop','main'):
            result=self.module.evaluate(self.results(base),base)
            self.assertEqual(result['status'],'passed');self.assertFalse(result['publication_ready'])
            self.assertFalse(result['publishes'])
        values=self.results();values['publication']['outputs']={'status':'ready','ready':'true'}
        result=self.module.evaluate(values,'main')
        self.assertTrue(result['publication_ready']);self.assertFalse(result['publishes'])

    def test_missing_or_inconsistent_metadata_never_passes(self):
        for values in ({},None,[],{**self.results(),'unreviewed':dict(result='success')},
                       {**self.results(),'native':None},{**self.results(),'python':dict(outputs={})}):
            with self.subTest(values=values),self.assertRaises(ValueError):self.module.evaluate(values,'main')
        for output in ({},{'status':'ready','ready':'false'},{'status':'unknown','ready':'true'}):
            values=self.results();values['publication']['outputs']=output
            with self.subTest(output=output),self.assertRaises(ValueError):self.module.evaluate(values,'main')
        values=self.results();values['route']['outputs']={'analyze':'false','context':'PR metadata update'}
        with self.assertRaises(ValueError):self.module.evaluate(values,'main')
        with self.assertRaises(ValueError):self.module.evaluate(self.results(),'other')

    def test_cli_distinguishes_failed_code_from_blocked_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            summary=Path(temporary)/'summary.md';values=self.results()
            values['installers']['result']='failure'
            env={**os.environ,'AIKYA_PR_NEEDS':json.dumps(values),'GITHUB_STEP_SUMMARY':str(summary)}
            result=subprocess.run([sys.executable,'-B',SCRIPT,'--base','main'],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'failed')
            values['installers']['result']='success';env['AIKYA_PR_NEEDS']=json.dumps(values)
            result=subprocess.run([sys.executable,'-B',SCRIPT,'--base','main'],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(json.loads(result.stdout)['publication_ready'])
            self.assertIn('blocked',summary.read_text());self.assertIn('publication',summary.read_text())


if __name__=='__main__':unittest.main()
