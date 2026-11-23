"""A reviewed local migration preserves source/memory and has guarded metadata rollback."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from aikya.installation.profile import validated
try:migration=importlib.import_module('aikya.installation.migration_v8')
except ModuleNotFoundError:migration=None


class V8MigrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(migration,'Reviewed v8 migration is absent')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();(self.root/'.harness').mkdir()
        self.profile=self.root/'.harness/project-profile.json'
        old=dict(_generated_by='claude-dev-harness-interactive',schema_version=1,
                 decisions=validated(dict(backend='python',methodology='odd'),self.root),detected={'modules':[]})
        self.original=(json.dumps(old,ensure_ascii=False,indent=2)+'\n').encode();self.profile.write_bytes(self.original)
        (self.root/'source.py').write_text('class Preserved: pass\n')
        note=self.root/'aikya/docs/memory/team.md';note.parent.mkdir(parents=True);note.write_text('Team notes\n')
        policy=self.root/'.aikya/code-index.json';policy.parent.mkdir();policy.write_text('custom-policy-preserved')

    def test_preview_denial_and_foreign_profiles_do_not_write(self):
        plan=migration.preview(self.root,'odd')
        self.assertFalse((self.root/'.aikya/pi').exists())
        with self.assertRaises(ValueError):migration.apply(self.root,plan)
        self.assertEqual(self.profile.read_bytes(),self.original)
        self.profile.write_text('{"custom":true}')
        with self.assertRaises(ValueError):migration.preview(self.root,'odd')
        self.assertEqual(self.profile.read_text(),'{"custom":true}')

    def test_apply_and_exact_rollback_preserve_memory_source_and_custom_metadata(self):
        plan=migration.preview(self.root,'odd');result=migration.apply(self.root,plan,approved=True)
        self.assertEqual(result['status'],'migrated')
        value=json.loads(self.profile.read_text())
        self.assertEqual(value['_generated_by'],'aikya-pi-onboarding')
        self.assertEqual(value['decisions']['mode'],'existing')
        self.assertEqual(migration.apply(self.root,plan,approved=True),result)
        with self.assertRaises(ValueError):migration.rollback(self.root,plan['id'])
        migration.rollback(self.root,plan['id'],approved=True)
        self.assertEqual(self.profile.read_bytes(),self.original)
        self.assertFalse((self.root/'.aikya/runtime-selection.json').exists())
        self.assertEqual((self.root/'source.py').read_text(),'class Preserved: pass\n')
        self.assertEqual((self.root/'aikya/docs/memory/team.md').read_text(),'Team notes\n')
        self.assertEqual((self.root/'.aikya/code-index.json').read_text(),'custom-policy-preserved')

    def test_source_drift_and_postmigration_customization_block_replay_or_rollback(self):
        plan=migration.preview(self.root,'odd')
        (self.root/'source.py').write_text('class Changed: pass\n')
        with self.assertRaises(ValueError):migration.apply(self.root,plan,approved=True)
        self.assertFalse((self.root/'.aikya/pi').exists())
        plan=migration.preview(self.root,'odd');migration.apply(self.root,plan,approved=True)
        self.profile.write_text('{"custom":true}')
        with self.assertRaises(ValueError):migration.rollback(self.root,plan['id'],approved=True)
        self.assertEqual(self.profile.read_text(),'{"custom":true}')

    def test_interrupted_metadata_commit_can_restore_originals_without_replaying(self):
        from unittest.mock import patch
        plan=migration.preview(self.root,'odd');write=migration.atomic_write
        def fail_selection(path,body,**kwargs):
            if Path(path)==self.root/'.aikya/runtime-selection.json':raise OSError('simulated interruption')
            return write(path,body,**kwargs)
        with patch.object(migration,'atomic_write',side_effect=fail_selection):
            with self.assertRaises(OSError):migration.apply(self.root,plan,approved=True)
        with self.assertRaises(ValueError):migration.apply(self.root,plan,approved=True)
        self.assertEqual(migration.rollback_preview(self.root,plan['id'])['status'],'pending')
        migration.rollback(self.root,plan['id'],approved=True)
        self.assertEqual(self.profile.read_bytes(),self.original)

    def test_changed_backups_or_custom_audit_report_are_preserved(self):
        plan=migration.preview(self.root,'odd');migration.apply(self.root,plan,approved=True)
        report=self.root/plan['report'];report.write_text('Team audit report')
        with self.assertRaises(ValueError):migration.rollback(self.root,plan['id'],approved=True)
        self.assertEqual(report.read_text(),'Team audit report')
        report.write_text(migration._report(migration._record(self.root,plan['id']),'migrated'))
        backup=self.root/plan['backup_path']/'0.before';backup.write_bytes(b'changed backup')
        current=self.profile.read_bytes()
        with self.assertRaises(ValueError):migration.rollback(self.root,plan['id'],approved=True)
        self.assertEqual(self.profile.read_bytes(),current)

    def test_custom_backup_folder_is_not_adopted_or_overwritten(self):
        plan=migration.preview(self.root,'odd')
        folder=self.root/plan['backup_path'];folder.mkdir(parents=True)
        marker=folder/'0.before';marker.write_bytes(b'unknown backup')
        with self.assertRaises(ValueError):migration.apply(self.root,plan,approved=True)
        self.assertEqual(marker.read_bytes(),b'unknown backup')
        self.assertEqual(self.profile.read_bytes(),self.original)

    def test_actual_installer_profile_can_migrate_and_restore_in_both_methods(self):
        from aikya.installation import facade
        source=Path(__file__).resolve().parents[1]
        for kind,example in [('development','next-react'),('infrastructure','infra-terraform-only'),('devops','devops-kustomize')]:
            for method in ('odd','sdd'):
                with self.subTest(kind=kind,method=method),tempfile.TemporaryDirectory() as folder:
                    root=Path(folder).resolve()
                    raw=json.loads((source/'examples'/example/'answers.json').read_text())
                    profile=facade.validated({**raw,'methodology':method},root)
                    facade.install(root,profile,{'modules':[]},docs_lang='es' if method=='sdd' else 'en')
                    original=(root/'.harness/project-profile.json').read_bytes()
                    policy=(root/'.aikya/code-index.json').read_bytes()
                    before={p.relative_to(root).as_posix():p.read_bytes() for p in (root/'aikya/docs').rglob('*.md') if p.name!='indice.md'}
                    plan=migration.preview(root,method);migration.apply(root,plan,approved=True)
                    migration.rollback(root,plan['id'],approved=True)
                    self.assertEqual((root/'.harness/project-profile.json').read_bytes(),original)
                    self.assertEqual((root/'.aikya/code-index.json').read_bytes(),policy)
                    for path,body in before.items():self.assertEqual((root/path).read_bytes(),body)

    def test_methodology_is_explicit_and_unknown_selection_is_preserved(self):
        with self.assertRaises(ValueError):migration.preview(self.root,None)
        with self.assertRaises(ValueError):migration.preview(self.root,'sdd')
        path=self.root/'.aikya/runtime-selection.json';path.write_text('{"custom":true}')
        with self.assertRaises(ValueError):migration.preview(self.root,'odd')
        self.assertEqual(path.read_text(),'{"custom":true}')


if __name__=='__main__':unittest.main()
