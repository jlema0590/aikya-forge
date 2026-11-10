"""Global versions change only through reviewed promotion, with complete-effect recovery."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.services import skill_library as library,selected_skills
from aikya.storage import atomic_write


class LibraryChangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve()
        self.source=self.base/'example-skill';self.source.mkdir();self.original='---\nname: example-skill\ndescription: Selected conventions\n---\nOriginal conventions.\n'
        (self.source/'SKILL.md').write_text(self.original)
        self.app=self.base/'application';env=patch.dict('os.environ',{'AIKYA_INSTALL_ROOT':str(self.app)});env.start();self.addCleanup(env.stop)
        value=library.preview(str(self.source));self.first=library.apply(value['plan'],approved=True)['source_hash']
        self.assertTrue(callable(getattr(library,'change_preview',None)),'Reviewed library version changes are absent')

    def update(self):
        (self.source/'SKILL.md').write_text(self.original+'Updated conventions.\n')
        value=library.change_preview(action='update',source=str(self.source))
        return value,library.apply(value['plan'],approved=True)

    def test_global_update_retains_original_and_does_not_change_a_selected_project_copy(self):
        root=self.base/'project';root.mkdir();plan=selected_skills.preview(root,dict(kind='global',name='example-skill',source_hash=self.first))
        selected_skills.apply(root,plan['plan'],approved=True);old=selected_skills.verify(root,'example-skill')
        value,result=self.update();self.assertEqual(value['review']['before'],self.first)
        self.assertNotEqual(result['source_hash'],self.first);self.assertEqual(selected_skills.verify(root,'example-skill'),old)
        self.assertEqual(library.package('example-skill',self.first)['raws']['SKILL.md'],self.original.encode())
        self.assertEqual(library.status()['skills'][0]['source_hash'],result['source_hash'])

    def test_rollback_requires_confirmation_and_only_uses_a_retained_version(self):
        _,second=self.update();value=library.change_preview(action='rollback',name='example-skill',source_hash=self.first)
        with self.assertRaises(ValueError):library.apply(value['plan'])
        self.assertEqual(library.status()['skills'][0]['source_hash'],second['source_hash'])
        library.apply(value['plan'],approved=True);self.assertEqual(library.status()['skills'][0]['source_hash'],self.first)
        with self.assertRaises(ValueError):library.change_preview(action='rollback',name='example-skill',source_hash='f'*64)

    def test_stale_preview_and_customized_old_version_never_promote(self):
        (self.source/'SKILL.md').write_text(self.original+'New\n');value=library.change_preview(action='update',source=str(self.source))
        (self.source/'SKILL.md').write_text(self.original+'Changed after review\n')
        with self.assertRaises(ValueError):library.apply(value['plan'],approved=True)
        target=self.app/'skills/packages'/self.first/'example-skill/files/SKILL.md';target.write_text('Customized original')
        with self.assertRaises(ValueError):library.change_preview(action='update',source=str(self.source))
        self.assertEqual(target.read_text(),'Customized original')

    def test_complete_copy_can_be_promoted_after_interruption_without_copying_again(self):
        (self.source/'SKILL.md').write_text(self.original+'New\n');value=library.change_preview(action='update',source=str(self.source))
        def interrupt(target,*a,**kw):
            if target.name=='registry.json':raise OSError('Interrupted before registry promotion')
            return atomic_write(target,*a,**kw)
        with patch.object(library,'atomic_write',side_effect=interrupt):
            with self.assertRaises(OSError):library.apply(value['plan'],approved=True)
        self.assertEqual(library.status()['skills'][0]['source_hash'],self.first)
        recover=library.recovery_preview()
        with self.assertRaises(ValueError):library.recover(recover['plan'])
        from aikya.services import skill_packages
        with patch.object(skill_packages,'write',side_effect=AssertionError('Must not repeat package effects')):
            library.recover(recover['plan'],approved=True)
        self.assertEqual(library.status()['skills'][0]['source_hash'],value['plan']['source_hash'])
        self.assertEqual(library.status()['status'],'available')

    def test_partial_package_remains_pending_and_is_not_replayed(self):
        from aikya.services import skill_packages
        (self.source/'SKILL.md').write_text(self.original+'New\n');value=library.change_preview(action='update',source=str(self.source))
        with patch.object(skill_packages,'manifest',side_effect=OSError('Interrupted partial capture')):
            with self.assertRaises(OSError):library.apply(value['plan'],approved=True)
        with self.assertRaises(ValueError):library.recovery_preview()
        with self.assertRaises(ValueError):library.change_preview(action='update',source=str(self.source))
        self.assertEqual(library.status()['skills'][0]['source_hash'],self.first)


if __name__=='__main__':unittest.main()
