"""Owned skills can be withdrawn and restored without deleting user data or other scopes."""
import importlib
import json
import os
import subprocess
import sys
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from aikya.services import selected_skills,skill_library


def snapshot(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


class SkillRemovalTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.skill_removal'),'Native reversible skill removal is absent')
        self.removal=importlib.import_module('aikya.services.skill_removal')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve()
        self.root=self.base/'project';self.root.mkdir();self.app=self.base/'application'
        self.source=self.base/'example-skill';self.source.mkdir()
        self.original=b'---\r\nname: example-skill\r\ndescription: Selected project conventions\r\n---\r\nUse the selected conventions.\r\n'
        (self.source/'SKILL.md').write_bytes(self.original)
        self.env=patch.dict('os.environ',{'AIKYA_INSTALL_ROOT':str(self.app)});self.env.start();self.addCleanup(self.env.stop)

    def install(self,scope):
        if scope=='project':return selected_skills.apply(self.root,selected_skills.preview(self.root,str(self.source))['plan'],approved=True)
        return skill_library.apply(skill_library.preview(str(self.source))['plan'],approved=True)

    def preview(self,scope='project',**extra):
        return self.removal.preview(self.root,scope=scope,names=['example-skill'],**extra)

    def test_explicit_all_is_a_noop_when_no_owned_selection_exists(self):
        before=snapshot(self.root);value=self.removal.preview(self.root,names='all')
        self.assertIsNone(value['plan']);self.assertEqual(value['review']['names'],[])
        self.assertEqual(snapshot(self.root),before);self.assertFalse(self.app.exists())

    def test_multiple_selected_skills_are_withdrawn_and_restored_together(self):
        self.install('project');other=self.base/'second-skill';other.mkdir()
        (other/'SKILL.md').write_bytes(b'---\nname: second-skill\ndescription: Another chosen convention\n---\nSecond conventions.\n')
        selected_skills.apply(self.root,selected_skills.preview(self.root,str(other))['plan'],approved=True)
        result=self.removal.apply(self.root,self.removal.preview(self.root,names='all')['plan'],approved=True)
        self.assertEqual(result['names'],['example-skill','second-skill']);self.assertEqual(selected_skills.resolve(self.root)['skills'],[])
        plan=self.removal.preview(self.root,names='all',action='restore',operation_id=result['operation_id'])
        self.removal.apply(self.root,plan['plan'],approved=True)
        self.assertEqual(len(selected_skills.resolve(self.root)['skills']),2)

    def test_concurrent_apply_consumes_one_preview_once(self):
        self.install('project');plan=self.preview()['plan']
        def apply():
            try:return self.removal.apply(self.root,plan,approved=True)['status']
            except (ValueError,OSError):return 'refused'
        with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(lambda _:apply(),range(2)))
        self.assertEqual(sorted(results),['refused','removed']);self.assertEqual(selected_skills.resolve(self.root)['skills'],[])

    def test_global_interruption_preserves_a_recoverable_withdrawal(self):
        self.install('global');plan=self.preview('global')['plan'];actual=self.removal.atomic_write
        def interrupt(path,*args,**kwargs):
            if '/operations/' in path.as_posix():raise OSError('Interrupted global journal')
            return actual(path,*args,**kwargs)
        with patch.object(self.removal,'atomic_write',side_effect=interrupt):
            with self.assertRaises(OSError):self.removal.apply(self.root,plan,approved=True)
        self.assertEqual(skill_library.status()['status'],'pending')
        value=self.removal.recovery_preview(self.root,'global')
        self.assertEqual(self.removal.recover(self.root,value['plan'],approved=True)['status'],'removed')
        self.assertEqual(skill_library.status()['skills'],[])

    def test_cli_preview_removal_restore_and_local_alias(self):
        self.install('project');before=snapshot(self.root)
        command=[sys.executable,'-B','-m','aikya','skills']
        args=['--scope','local','--target',str(self.root),'--name','example-skill']
        def call(action,extra):
            process=subprocess.run([*command,action,*args,*extra],env=os.environ,capture_output=True,text=True,timeout=15)
            self.assertEqual(process.returncode,0,process.stderr);return json.loads(process.stdout)
        self.assertEqual(call('uninstall',[])['status'],'preview');self.assertEqual(snapshot(self.root),before)
        result=call('uninstall',['--yes']);self.assertEqual(result['status'],'removed')
        self.assertEqual(call('restore',['--operation',result['operation_id'],'--yes'])['status'],'restored')
        self.assertEqual(len(selected_skills.resolve(self.root)['skills']),1)

    def test_preview_and_denial_have_no_side_effects(self):
        self.install('project');before=snapshot(self.root);value=self.preview()
        self.assertEqual(value['review']['execution'],'none');self.assertEqual(snapshot(self.root),before)
        with self.assertRaises(ValueError):self.removal.apply(self.root,value['plan'])
        self.assertEqual(snapshot(self.root),before)

    def test_project_withdrawal_and_restore_keep_exact_original_packages(self):
        self.install('project');entry=selected_skills._entry(self.root,'example-skill');cached=snapshot(self.root/'.aikya/pi/skills/packages')
        result=self.removal.apply(self.root,self.preview()['plan'],approved=True)
        self.assertEqual(result['status'],'removed');self.assertTrue(result['restart_required'])
        self.assertEqual(selected_skills.resolve(self.root)['skills'],[])
        self.assertEqual(snapshot(self.root/'.aikya/pi/skills/packages'),cached)
        plan=self.preview(action='restore',operation_id=result['operation_id'])
        self.removal.apply(self.root,plan['plan'],approved=True)
        self.assertEqual(selected_skills._entry(self.root,'example-skill'),entry)
        self.assertEqual(snapshot(self.root/'.aikya/pi/skills/packages'),cached)
        self.assertTrue((self.source/'SKILL.md').read_bytes()==self.original)

    def test_global_withdrawal_does_not_deactivate_project_copies(self):
        self.install('global');self.install('project');before=snapshot(self.root)
        result=self.removal.apply(self.root,self.preview('global')['plan'],approved=True)
        self.assertEqual(skill_library.status()['skills'],[]);self.assertEqual(snapshot(self.root),before)
        self.assertEqual(len(selected_skills.resolve(self.root)['skills']),1)
        self.removal.apply(self.root,self.preview('global',action='restore',operation_id=result['operation_id'])['plan'],approved=True)
        self.assertEqual(skill_library.package('example-skill',skill_library.status()['skills'][0]['source_hash'])['raws']['SKILL.md'],self.original)

    def test_project_withdrawal_does_not_modify_global_library(self):
        self.install('global');self.install('project');before=snapshot(self.app)
        self.removal.apply(self.root,self.preview()['plan'],approved=True)
        self.assertEqual(snapshot(self.app),before);self.assertEqual(len(skill_library.status()['skills']),1)

    def test_changed_package_after_preview_is_preserved_without_registry_effects(self):
        self.install('project');plan=self.preview()['plan'];entry=selected_skills._entry(self.root,'example-skill')
        target=self.root/entry['file'];target.write_bytes(b'User edits must survive')
        before=snapshot(self.root)
        with self.assertRaises(ValueError):self.removal.apply(self.root,plan,approved=True)
        self.assertEqual(snapshot(self.root),before)

    def test_custom_comparison_is_preserved_and_blocks_project_removal(self):
        self.install('project');target=self.root/selected_skills.COMPARISON;target.write_bytes(b'Custom comparison')
        before=snapshot(self.root)
        with self.assertRaises(ValueError):self.preview()
        self.assertEqual(snapshot(self.root),before)

    def test_malformed_selection_is_rejected_without_type_errors(self):
        self.install('project');before=snapshot(self.root)
        for names in ([{}],[[]],[None]):
            with self.subTest(names=names),self.assertRaises(ValueError):self.removal.preview(self.root,names=names)
        self.assertEqual(snapshot(self.root),before)

    def test_protected_unknown_or_duplicate_names_never_delete_data(self):
        self.install('project');before=snapshot(self.root)
        for names in (['aikya-feature'],['missing'],['example-skill','example-skill'],['../escape'],[]):
            with self.subTest(names=names),self.assertRaises(ValueError):self.removal.preview(self.root,names=names)
        self.assertEqual(snapshot(self.root),before)

    def test_restore_refuses_a_new_selection_with_the_same_name(self):
        self.install('project');result=self.removal.apply(self.root,self.preview()['plan'],approved=True)
        (self.source/'SKILL.md').write_bytes(self.original+b'New explicit version.\n');self.install('project')
        before=snapshot(self.root)
        with self.assertRaises(ValueError):self.preview(action='restore',operation_id=result['operation_id'])
        self.assertEqual(snapshot(self.root),before)

    def test_repeated_apply_cannot_replay_or_reenable_the_skill(self):
        self.install('project');plan=self.preview()['plan'];self.removal.apply(self.root,plan,approved=True);before=snapshot(self.root)
        with self.assertRaises(ValueError):self.removal.apply(self.root,plan,approved=True)
        self.assertEqual(snapshot(self.root),before);self.assertEqual(selected_skills.resolve(self.root)['skills'],[])

    def test_interrupted_metadata_promotion_is_reconciled_without_package_copy(self):
        self.install('project');plan=self.preview()['plan'];actual=self.removal.atomic_write
        def interrupt(path,*args,**kwargs):
            if '/operations/' in path.as_posix():raise OSError('Interrupted before completed journal')
            return actual(path,*args,**kwargs)
        with patch.object(self.removal,'atomic_write',side_effect=interrupt):
            with self.assertRaises(OSError):self.removal.apply(self.root,plan,approved=True)
        with self.assertRaises(ValueError):self.preview()
        value=self.removal.recovery_preview(self.root,'project')
        self.assertEqual(self.removal.recover(self.root,value['plan'],approved=True)['status'],'removed')
        self.assertEqual(selected_skills.resolve(self.root)['skills'],[])


if __name__=='__main__':unittest.main()
