"""Release event policy and immutable retry behavior; no remote writes."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/ci'))


class ForgeReleasePlanTests(unittest.TestCase):
    def setUp(self):
        script=ROOT/'scripts/ci/forge_release_plan.py'
        self.assertTrue(script.is_file(),'Automatic release planner is absent')
        spec=importlib.util.spec_from_file_location('forge_release_plan',script)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.sha='a'*40;self.other='b'*40;self.calls=[]
        self.release=dict(tag_name='v0.2.0',draft=False,prerelease=False,published_at='2026-11-23T10:00:00Z',
            assets=[dict(name=n) for n in ('install.sh','install.ps1','SHA256SUMS','terminal-bootstrap.json','release.json')])

    def run_plan(self,*,table=None,**changes):
        def lookup(path,missing):
            self.calls.append((path,missing))
            return (table or {}).get(path)
        args=dict(repository='jlema0590/aikya-forge',event='push',ref='refs/heads/main',
                  sha=self.sha,version='0.2.0',publish=False,lookup=lookup,publication_ready=True)
        return self.module.plan(**{**args,**changes})

    def existing(self,sha=None):
        return {'releases/tags/v0.2.0':self.release,'git/ref/tags/v0.2.0':{'object':{'type':'commit','sha':sha or self.sha}},'releases/latest':self.release}

    def test_main_push_publishes_new_version_and_manual_prepare_is_offline(self):
        self.assertEqual('publish',self.run_plan()['mode'])
        self.calls=[]
        self.assertEqual('prepare',self.run_plan(event='workflow_dispatch',ref='refs/heads/develop')['mode'])
        self.assertEqual([],self.calls)
        self.assertEqual('publish',self.run_plan(event='workflow_dispatch',publish=True)['mode'])

    def test_pending_trials_prepare_main_artifacts_without_publishing(self):
        result=self.run_plan(publication_ready=False)
        self.assertEqual(result['mode'],'prepare');self.assertEqual(result['source_commit'],self.sha)
        with self.assertRaises(ValueError):
            self.run_plan(event='workflow_dispatch',publish=True,publication_ready=False)

    def test_published_pages_recovery_does_not_reapprove_changed_source(self):
        result=self.run_plan(table=self.existing(),event='workflow_dispatch',publish=True,publication_ready=False)
        self.assertEqual(result['mode'],'pages');self.assertEqual(result['source_commit'],self.sha)

    def test_nonmain_and_forks_cannot_publish_and_bad_versions_fail(self):
        for change in (dict(ref='refs/heads/develop'),dict(repository='other/aikya-forge'),dict(event='pull_request'),dict(version='0.2.0\nnext'),dict(version='v0.2.0')):
            with self.subTest(change=change),self.assertRaises(ValueError):self.run_plan(**change)
        with self.assertRaises(ValueError):self.run_plan(event='workflow_dispatch',ref='refs/heads/develop',publish=True)

    def test_rerun_recovers_pages_without_rebuilding_or_replacing_release(self):
        result=self.run_plan(table=self.existing())
        self.assertEqual('pages',result['mode']);self.assertEqual(self.sha,result['source_commit'])
        # A later docs-only main push retains the published version without replacing it.
        self.assertEqual('skip',self.run_plan(table=self.existing(self.other))['mode'])
        repaired=self.run_plan(table=self.existing(self.other),event='workflow_dispatch',publish=True)
        self.assertEqual('pages',repaired['mode']);self.assertEqual(self.other,repaired['source_commit'])

    def test_preexisting_tags_drafts_and_partial_releases_are_not_overwritten(self):
        self.assertEqual('publish',self.run_plan(table={'git/ref/tags/v0.2.0':{'object':{'type':'commit','sha':self.sha}}})['mode'])
        with self.assertRaises(ValueError):self.run_plan(table={'git/ref/tags/v0.2.0':{'object':{'type':'commit','sha':self.other}}})
        for key,value in (('draft',True),('prerelease',True),('assets',[]),('tag_name','v0.1.0')):
            table=self.existing();table['releases/tags/v0.2.0']={**self.release,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_plan(table=table)
        table=self.existing();table['git/ref/tags/v0.2.0']=None
        with self.assertRaises(ValueError):self.run_plan(table=table)

    def test_pages_retry_cannot_roll_back_a_newer_stable_release(self):
        table=self.existing();table['releases/latest']={**self.release,'tag_name':'v0.3.0'}
        with self.assertRaises(ValueError):self.run_plan(table=table,event='workflow_dispatch',publish=True)

    def test_api_failure_cannot_be_mistaken_for_an_unpublished_version(self):
        def denied(path,missing):raise ValueError('GitHub API HTTP 403')
        with self.assertRaisesRegex(ValueError,'403'):self.run_plan(lookup=denied)

    def test_real_manual_preview_writes_outputs_without_a_token(self):
        import json,os,subprocess,tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'VERSION').write_text('0.2.0\n')
            output=root/'output';summary=root/'summary'
            env={**os.environ,'GITHUB_REPOSITORY':'jlema0590/aikya-forge',
                 'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_REF':'refs/heads/develop',
                 'GITHUB_SHA':self.sha,'FORGE_PUBLISH':'false','GITHUB_OUTPUT':str(output),
                 'GITHUB_STEP_SUMMARY':str(summary)}
            env.pop('GH_TOKEN',None);env.pop('GITHUB_TOKEN',None)
            command=[sys.executable,'-B',str(ROOT/'scripts/ci/forge_release_plan.py'),'--source',str(root)]
            result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual('prepare',json.loads(result.stdout)['mode'])
            self.assertIn('mode=prepare\n',output.read_text());self.assertIn('v0.2.0',summary.read_text())
            output.unlink();summary.unlink();env['FORGE_PUBLISH']='true'
            result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2);self.assertFalse(output.exists());self.assertFalse(summary.exists())

    def test_workflow_connects_main_manual_checks_and_pages_recovery(self):
        text=(ROOT/'.github/workflows/forge-release.yml').read_text()
        self.assertIn('branches: [main]',text);self.assertIn('workflow_dispatch:',text)
        self.assertIn('forge_release_plan.py',text);self.assertIn('queue: max',text)
        self.assertIn('needs.plan.outputs.mode',text);self.assertIn('needs.plan.outputs.source_commit',text)
        self.assertIn('forge_release_gate.py',text);self.assertIn('forge-native.yml',text)
        self.assertIn('Verify public installer bytes',text)
        self.assertIn('always()',text);self.assertNotIn('contents: write\n  pages:',text)


if __name__=='__main__':unittest.main()
