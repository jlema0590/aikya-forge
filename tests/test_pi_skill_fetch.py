"""Confirmed public data capture is separate from installation and activation."""
from pathlib import Path
import importlib
import importlib.util
import tempfile
import unittest
from unittest.mock import patch
import test_github_skill_source as fixtures
from aikya.catalogs import github_source
from aikya.services import selected_skills,skill_library


class SkillFetchTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.skill_fetch'),'Confirmed source capture is absent')
        self.fetch=importlib.import_module('aikya.services.skill_fetch')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve()
        self.root=self.base/'project';self.root.mkdir();self.app=self.base/'application'
        env=patch.dict('os.environ',{'AIKYA_INSTALL_ROOT':str(self.app)});env.start();self.addCleanup(env.stop)
        self.fixture=fixtures.GithubSourceTests();self.fixture.setUp()
        network=patch.object(github_source,'read_url',side_effect=lambda url,*a,**kw:self.fixture.responses[url]);network.start();self.addCleanup(network.stop)
        self.source=dict(repo=self.fixture.repo,path='skills/example-skill',commit=self.fixture.commit,name='example-skill')

    def capture(self):
        value=self.fetch.preview(self.root,**self.source)
        return self.fetch.apply(self.root,value['plan'],approved=True)

    def test_preview_and_decline_do_not_download_or_create_any_project_file(self):
        with patch.object(github_source,'read_url',side_effect=AssertionError('No unapproved network')):
            value=self.fetch.preview(self.root,**self.source)
            with self.assertRaises(ValueError):self.fetch.apply(self.root,value['plan'])
        self.assertEqual(list(self.root.iterdir()),[]);self.assertFalse(self.app.exists())

    def test_capture_is_inert_and_project_selection_requires_its_own_confirmation(self):
        result=self.capture();self.assertEqual(result['activation'],'none')
        self.assertEqual(selected_skills.status(self.root)['skills'],[]);self.assertFalse(self.app.exists())
        value=selected_skills.preview(self.root,result['source'])
        self.assertIn('Use',value['review']['content'])
        with self.assertRaises(ValueError):selected_skills.apply(self.root,value['plan'])
        selected_skills.apply(self.root,value['plan'],approved=True)
        self.assertEqual(selected_skills.verify(self.root,'example-skill')['source_hash'],result['source']['source_hash'])

    def test_captured_data_can_be_installed_globally_without_project_activation(self):
        result=self.capture();value=skill_library.preview(result['source'])
        skill_library.apply(value['plan'],approved=True)
        self.assertEqual(skill_library.status()['skills'][0]['name'],'example-skill')
        self.assertEqual(selected_skills.status(self.root)['skills'],[])

    def test_captured_data_is_immutable_and_same_capture_never_overwrites_it(self):
        result=self.capture();target=Path(result['package'])/'files/SKILL.md';raw=target.read_bytes()
        again=self.capture();self.assertEqual(again['source'],result['source']);self.assertEqual(target.read_bytes(),raw)
        target.write_text('User changed capture')
        with self.assertRaises(ValueError):selected_skills.preview(self.root,result['source'])
        with self.assertRaises(ValueError):self.capture()
        self.assertEqual(target.read_text(),'User changed capture')

    def test_wrong_declared_name_or_cancelled_capture_creates_no_cache(self):
        value=self.fetch.preview(self.root,**{**self.source,'name':'other-name'})
        with self.assertRaises(ValueError):self.fetch.apply(self.root,value['plan'],approved=True)
        value=self.fetch.preview(self.root,**self.source)
        with self.assertRaises(ValueError):self.fetch.apply(self.root,value['plan'],approved=True,cancel=lambda:True)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_descriptor_cannot_be_rebound_to_another_project_or_version(self):
        result=self.capture();other=self.base/'other';other.mkdir()
        source={**result['source'],'project':str(other)}
        with self.assertRaises(ValueError):selected_skills.preview(self.root,source)
        with self.assertRaises(ValueError):selected_skills.preview(self.root,{**result['source'],'source_hash':'f'*64})
        self.assertEqual(list(other.iterdir()),[])


if __name__=='__main__':unittest.main()
