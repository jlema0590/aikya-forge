"""Metadata edits cannot cancel full analysis or emit a required passing context."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/ci/pr_event.py'


class PullRequestEventTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(),'PR event routing is missing')
        spec=importlib.util.spec_from_file_location('pr_event',SCRIPT)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def event(self,action='edited',base='main',changes=None):
        return dict(action=action,number=9,pull_request={'base':{'ref':base}},changes=changes or {})

    def test_body_and_title_edits_are_separate_from_required_analysis(self):
        for changes in ({'body':{'from':'previous'}},{'title':{'from':'previous'}},{}):
            result=self.module.route(self.event(changes=changes))
            self.assertFalse(result['analyze']);self.assertEqual(result['group'],'forge-pr-9-metadata')
            self.assertEqual(result['context'],'PR metadata update')

    def test_source_reopen_and_base_changes_keep_full_target_specific_analysis(self):
        for base in ('develop','main'):
            for action,changes in (('opened',{}),('synchronize',{}),('reopened',{}),
                                   ('edited',{'base':{'ref':{'from':'other'}}})):
                result=self.module.route(self.event(action,base,changes))
                self.assertTrue(result['analyze']);self.assertEqual(result['group'],'forge-pr-9-analysis')
                self.assertEqual(result['context'],'Forge PR acceptance | '+base)

    def test_invalid_event_or_target_cannot_be_mistaken_for_metadata(self):
        for value in ({},None,self.event('unknown'),self.event(base='other'),{**self.event(),'changes':[]}):
            with self.subTest(value=value),self.assertRaises(ValueError):self.module.route(value)

    def test_cli_emits_only_bounded_control_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);event=root/'event.json';output=root/'output'
            event.write_text(json.dumps(self.event(changes={'body':{'from':'untrusted\ncontext=forged'}})))
            result=subprocess.run([sys.executable,'-B',SCRIPT,'--event',event],
                env={**os.environ,'GITHUB_OUTPUT':str(output)},capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(output.read_text(),'analyze=false\ncontext=PR metadata update\n')


if __name__=='__main__':unittest.main()
