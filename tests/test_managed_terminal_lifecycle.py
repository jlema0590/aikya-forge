"""Native terminal promotion retains old versions, user data and exact ownership."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation import managed_runtime
from managed_terminal_support import payload,snapshot


class ManagedLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_install'),'Native managed installation lifecycle is absent')
        self.install=importlib.import_module('aikya.installation.managed_install');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve();self.root=self.base/'application áikya'
        self.first=self.base/'first';payload(self.first);self.second=self.base/'second';payload(self.second,'8.0.0-alpha.1')
        platform=patch.object(managed_runtime,'host_platform',return_value='darwin-arm64');platform.start();self.addCleanup(platform.stop)
        self.probe=patch('aikya.installation.managed_probe.check',return_value={'status':'passed'});self.mock_probe=self.probe.start();self.addCleanup(self.probe.stop)

    def promote(self,source,action='install'):
        plan=self.install.preview(self.root,source,action=action);return self.install.apply(plan,approved=True)

    def test_preview_and_missing_approval_have_no_application_effects(self):
        plan=self.install.preview(self.root,self.first);self.assertFalse(self.root.exists())
        self.assertEqual(plan['version'],'8.0.0-alpha.0');self.assertFalse(plan['writes'])
        with self.assertRaises(ValueError):self.install.apply(plan)
        self.assertFalse(self.root.exists());self.mock_probe.assert_not_called()

    def test_install_update_rollback_and_uninstall_preserve_global_skills_and_projects(self):
        project=self.base/'project';project.mkdir();(project/'user.md').write_text('Project-owned memory')
        initial=self.promote(self.first);self.assertEqual(initial['status'],'installed');self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.0')
        skills=self.root/'skills/user';skills.mkdir(parents=True);(skills/'SKILL.md').write_text('Chosen skill')
        wrappers={name:(self.root/'bin'/name).read_bytes() for name in ('aikya','aikya-manage','aikya-setup')}
        self.promote(self.second,'update');self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.1')
        plan=self.install.preview(self.root,action='rollback');self.install.apply(plan,approved=True)
        self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.0')
        self.assertEqual(wrappers,{name:(self.root/'bin'/name).read_bytes() for name in wrappers})
        self.install.apply(self.install.preview(self.root,action='uninstall'),approved=True)
        self.assertFalse((self.root/'terminal/current.json').exists());self.assertFalse((self.root/'bin/aikya').exists())
        self.assertEqual((skills/'SKILL.md').read_text(),'Chosen skill');self.assertEqual((project/'user.md').read_text(),'Project-owned memory')
        self.assertEqual(len(list((self.root/'terminal/versions').iterdir())),2)

    def test_changed_source_or_custom_launcher_blocks_promotion_and_preserves_active_version(self):
        self.promote(self.first);plan=self.install.preview(self.root,self.second,action='update')
        source=self.second/'runtime/src/launcher.ts';source.write_text('// changed')
        before=snapshot(self.root)
        with self.assertRaises(ValueError):self.install.apply(plan,approved=True)
        self.assertEqual(snapshot(self.root),before);self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.0')
        wrapper=self.root/'bin/aikya';wrapper.write_text('User launcher')
        with self.assertRaises(ValueError):self.install.preview(self.root,action='uninstall')
        self.assertEqual(wrapper.read_text(),'User launcher');self.assertTrue((self.root/'terminal/current.json').exists())

    def test_unowned_root_and_existing_launcher_are_never_adopted(self):
        self.root.mkdir();custom=self.root/'custom';custom.write_text('User data')
        with self.assertRaises(ValueError):self.install.preview(self.root,self.first)
        self.assertEqual(snapshot(self.root),{'custom':b'User data'})

    def test_stale_update_cannot_replace_a_newly_activated_version(self):
        self.promote(self.first);stale=self.install.preview(self.root,self.second,action='update');self.promote(self.second,'update');before=snapshot(self.root)
        with self.assertRaises(ValueError):self.install.apply(stale,approved=True)
        self.assertEqual(snapshot(self.root),before)

    def test_launcher_customized_during_preflight_is_preserved_before_promotion(self):
        self.promote(self.first);wrapper=self.root/'bin/aikya'
        def customize(*args,**kwargs):wrapper.write_text('User change during preparation');return {'status':'passed'}
        self.mock_probe.side_effect=customize
        with self.assertRaises(ValueError):self.promote(self.second,'update')
        self.assertEqual(wrapper.read_text(),'User change during preparation')
        self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.0')

    def test_payload_changed_by_preflight_cannot_become_active(self):
        self.promote(self.first)
        def customize(value,*args,**kwargs):
            (Path(value['runtime'])/'src/launcher.ts').write_text('// unexpected generated change');return {'status':'passed'}
        self.mock_probe.side_effect=customize
        with self.assertRaises(ValueError):self.promote(self.second,'update')
        self.assertEqual(managed_runtime.resolve(self.root)['version'],'8.0.0-alpha.0')

    def test_update_refuses_replaced_same_version_bytes_and_requires_explicit_rollback_for_downgrade(self):
        from aikya.installation.managed_payload import seal
        self.promote(self.first);original=json.loads((self.first/'manifest.json').read_bytes())
        source=self.first/'runtime/src/launcher.ts';source.write_text('// different payload under the same release version');(self.first/'manifest.json').unlink()
        seal(self.first,version=original['version'],target=original['platform'],versions=original['versions'],python=original['python'],node=original['node'],runtime=original['runtime'])
        before=snapshot(self.root)
        with self.assertRaises(ValueError):self.install.preview(self.root,self.first,action='update')
        self.assertEqual(snapshot(self.root),before);self.promote(self.second,'update');before=snapshot(self.root)
        with self.assertRaises(ValueError):self.install.preview(self.root,self.first,action='update')
        self.assertEqual(snapshot(self.root),before)


if __name__=='__main__':unittest.main()
