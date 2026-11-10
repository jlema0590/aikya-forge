"""Pinned public Git objects are data; no checkout, auth import or installer execution."""
import hashlib
import importlib
import importlib.util
import json
import unittest
from unittest.mock import patch


def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


class GithubSourceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.catalogs.github_source'),'Shared pinned GitHub data capture is absent')
        self.module=importlib.import_module('aikya.catalogs.github_source')
        self.repo='https://github.com/example/conventions';self.api='https://api.github.com/repos/example/conventions'
        self.commit='a'*40;self.root='b'*40;self.parent='d'*40;self.tree='c'*40
        self.skill=b'---\nname: example-skill\ndescription: Use selected conventions\n---\nRead only reviewed facts.\n'
        self.guide=b'# Reference\n\nAn explicit bounded resource.\n'
        self.members=[dict(path='SKILL.md',mode='100644',type='blob',sha=blob(self.skill),size=len(self.skill)),
            dict(path='references',mode='040000',type='tree',sha='e'*40),
            dict(path='references/guide.md',mode='100644',type='blob',sha=blob(self.guide),size=len(self.guide))]
        def tree(sha,entries):return json.dumps(dict(sha=sha,truncated=False,tree=entries)).encode()
        self.responses={self.api+'/git/commits/'+self.commit:json.dumps(dict(sha=self.commit,tree=dict(sha=self.root))).encode(),
            self.api+'/git/trees/'+self.root:tree(self.root,[dict(path='skills',mode='040000',type='tree',sha=self.parent)]),
            self.api+'/git/trees/'+self.parent:tree(self.parent,[dict(path='example-skill',mode='040000',type='tree',sha=self.tree)]),
            self.api+'/git/trees/'+self.tree+'?recursive=1':tree(self.tree,self.members),
            'https://raw.githubusercontent.com/example/conventions/'+self.commit+'/skills/example-skill/SKILL.md':self.skill,
            'https://raw.githubusercontent.com/example/conventions/'+self.commit+'/skills/example-skill/references/guide.md':self.guide}

    def capture(self,**kwargs):
        with patch.object(self.module,'read_url',side_effect=lambda url,*args,**options:self.responses[url]):
            return self.module.capture(self.repo,'skills/example-skill',self.commit,**kwargs)

    def replace_members(self,members=None,**extra):
        self.responses[self.api+'/git/trees/'+self.tree+'?recursive=1']=json.dumps(dict(sha=self.tree,truncated=False,tree=self.members if members is None else members,**extra)).encode()

    def test_pinned_selected_files_are_captured_exactly_with_provenance(self):
        value=self.capture()
        self.assertEqual(value['repo'],self.repo);self.assertEqual(value['commit'],self.commit)
        self.assertEqual(value['tree'],self.tree);self.assertEqual(value['files'],{'SKILL.md':self.skill,'references/guide.md':self.guide})
        self.assertEqual(value['bytes'],len(self.skill)+len(self.guide));self.assertEqual(value['execution'],'none')

    def test_branch_names_and_untrusted_repository_urls_are_refused_before_network(self):
        with patch.object(self.module,'read_url',side_effect=AssertionError('No request for invalid input')):
            for repo,commit in ((self.repo,'main'),('https://other.example/repo',self.commit),('https://token@github.com/example/repo',self.commit),('https://github.com/../repo',self.commit)):
                with self.subTest(repo=repo,commit=commit),self.assertRaises(ValueError):self.module.capture(repo,'skills/example-skill',commit)
            with self.assertRaises(ValueError):self.module.capture(self.repo,'../private',self.commit)

    def test_wrong_commit_or_tree_identity_cannot_be_accepted(self):
        key=self.api+'/git/commits/'+self.commit
        self.responses[key]=json.dumps(dict(sha='f'*40,tree=dict(sha=self.root))).encode()
        with self.assertRaises(ValueError):self.capture()

    def test_truncated_tree_never_becomes_partial_success(self):
        value=json.loads(self.responses[self.api+'/git/trees/'+self.tree+'?recursive=1']);value['truncated']=True
        self.responses[self.api+'/git/trees/'+self.tree+'?recursive=1']=json.dumps(value).encode()
        with self.assertRaises(ValueError):self.capture()

    def test_symlink_submodule_secret_and_escaping_paths_are_refused(self):
        for name,mode,kind in (('link','120000','blob'),('submodule','160000','commit'),('.env','100644','blob'),('../outside','100644','blob')):
            self.replace_members([*self.members,dict(path=name,mode=mode,type=kind,sha='f'*40,size=1)])
            with self.subTest(name=name),self.assertRaises(ValueError):self.capture()

    def test_raw_bytes_must_match_the_recorded_git_blob(self):
        key='https://raw.githubusercontent.com/example/conventions/'+self.commit+'/skills/example-skill/SKILL.md'
        self.responses[key]=self.skill[:-1]
        with self.assertRaises(ValueError):self.capture()

    def test_case_aliases_and_duplicate_members_cannot_materialize_one_file_twice(self):
        for name in ('SKILL.md','skill.md'):
            self.replace_members([*self.members,dict(path=name,mode='100644',type='blob',sha='f'*40,size=1)])
            with self.subTest(name=name),self.assertRaises(ValueError):self.capture()

    def test_root_skill_folder_is_an_explicit_supported_selection(self):
        self.responses[self.api+'/git/trees/'+self.root+'?recursive=1']=json.dumps(dict(sha=self.root,truncated=False,tree=self.members)).encode()
        self.responses['https://raw.githubusercontent.com/example/conventions/'+self.commit+'/SKILL.md']=self.skill
        self.responses['https://raw.githubusercontent.com/example/conventions/'+self.commit+'/references/guide.md']=self.guide
        with patch.object(self.module,'read_url',side_effect=lambda url,*args,**options:self.responses[url]):value=self.module.capture(self.repo,'.',self.commit)
        self.assertEqual(value['files']['SKILL.md'],self.skill);self.assertEqual(value['path'],'.')

    def test_capture_honors_cancellation_before_reading_any_source(self):
        with patch.object(self.module,'read_url',side_effect=AssertionError('Cancelled request dispatched')):
            with self.assertRaises(ValueError):self.module.capture(self.repo,'skills/example-skill',self.commit,cancel=lambda:True)

    def test_nonportable_paths_and_file_parent_collisions_are_refused_before_download(self):
        cases=[[dict(path='CON.txt',mode='100644',type='blob',sha='f'*40,size=1)],
               [dict(path='a',mode='100644',type='blob',sha='f'*40,size=1),dict(path='a/b',mode='100644',type='blob',sha='f'*40,size=1)]]
        for extra in cases:
            self.replace_members([*self.members,*extra])
            with self.subTest(paths=[v['path'] for v in extra]),self.assertRaises(ValueError):self.capture()

    def test_a_lowercase_or_directory_skill_entry_is_not_the_required_skill_file(self):
        for member in (dict(path='skill.md',mode='100644',type='blob',sha='f'*40,size=1),
                       dict(path='SKILL.md',mode='040000',type='tree',sha='f'*40)):
            self.replace_members([member])
            with self.subTest(path=member['path']),self.assertRaises(ValueError):self.capture()


if __name__=='__main__':unittest.main()
