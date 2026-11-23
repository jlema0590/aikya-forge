"""The legacy chosen-skill entry reuses the same pinned data capture, without Git execution."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import test_github_skill_source as fixtures
from aikya.catalogs import external,github_source


class GithubLegacyTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.GithubSourceTests();self.fixture.setUp()
        self.responses=dict(self.fixture.responses);self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()

    def test_generic_legacy_entry_captures_the_pinned_source_without_git_or_checkout(self):
        with patch.object(github_source,'read_url',side_effect=lambda url,*args,**kwargs:self.responses[url]),\
             patch.object(external.shutil,'which',return_value=None),\
             patch.object(external,'_invoke',side_effect=AssertionError('Imported source must not run Git or checkout')):
            value=external.install_github_skill(self.root,name='example-skill',repo=self.fixture.repo,
                skill_path='skills/example-skill',ref=None,commit=self.fixture.commit,permission=True)
        self.assertEqual(value['state'],'installed');self.assertEqual(value['commit'],self.fixture.commit)
        self.assertEqual((self.root/'.claude/skills/example-skill/SKILL.md').read_bytes(),self.fixture.skill)
        self.assertEqual((self.root/'.claude/skills/example-skill/references/guide.md').read_bytes(),self.fixture.guide)

    def test_reference_resolution_returns_a_fixed_commit_without_downloading_files(self):
        self.assertTrue(callable(getattr(github_source,'resolve',None)),'Read-only ref resolution is absent')
        self.responses[self.fixture.api+'/commits/heads%2Fmain']=self.fixture.commit.encode()
        with patch.object(github_source,'read_url',side_effect=lambda url,*args,**kwargs:self.responses[url]):
            value=github_source.resolve(self.fixture.repo,'heads/main')
        self.assertEqual(value['commit'],self.fixture.commit);self.assertEqual(value['ref'],'heads/main')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_ref_that_differs_from_the_expected_commit_creates_no_legacy_skill(self):
        self.responses[self.fixture.api+'/commits/heads%2Fmain']=self.fixture.commit.encode()
        with patch.object(github_source,'read_url',side_effect=lambda url,*args,**kwargs:self.responses[url]):
            with self.assertRaises(ValueError):external.install_github_skill(self.root,name='example-skill',repo=self.fixture.repo,
                skill_path='skills/example-skill',ref='heads/main',commit='f'*40,permission=True)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_missing_permission_never_requests_repository_data(self):
        with patch.object(github_source,'read_url',side_effect=AssertionError('No unapproved source request')):
            with self.assertRaises(PermissionError):external.install_github_skill(self.root,name='example-skill',repo=self.fixture.repo,
                skill_path='skills/example-skill',ref=None,commit=self.fixture.commit,permission=False)
        self.assertEqual(list(self.root.iterdir()),[])


if __name__=='__main__':unittest.main()
