"""Reconcile exact observed document effects without replay or inferred partial success."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.services import documentation as docs


class DocumentRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.documentation_recovery'),
                             'Native documentation reconciliation is absent')
        self.recovery=importlib.import_module('aikya.services.documentation_recovery')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        (self.root/'.harness').mkdir();(self.root/'.harness/project-profile.json').write_text(json.dumps(
            dict(decisions=dict(backend='python',methodology='odd',mode='existing'))))
        (self.root/'source.py').write_text('VALUE = 1\n')
        self.data=dict(action='write',sources=['source.py'],documents=[dict(document='architecture',payload=dict(
            title='Architecture',sections={'1-purpose-and-scope':'One local Python module.'}))])
        self.pending=self.root/'.aikya/pi/documentation/pending.json'

    def interrupted(self,data=None,command='aikya-docs'):
        value=docs.preview(self.root,command,data or self.data,'author')
        with patch.object(docs,'_still_owned',side_effect=OSError('Interrupted after effects')):
            with self.assertRaises(OSError):docs.apply(self.root,value['plan'],approved=True)
        self.assertTrue(self.pending.exists())

    def test_empty_recovery_is_read_only(self):
        self.assertEqual(self.recovery.preview(self.root,'author')['status'],'nothing_pending')
        self.assertFalse((self.root/'.aikya').exists())

    def test_complete_effects_reconcile_after_confirmation_without_rewriting_documents(self):
        self.interrupted();value=self.recovery.preview(self.root,'author')
        self.assertEqual(value['status'],'reconciliation_ready')
        with self.assertRaises(ValueError):self.recovery.apply(self.root,value['plan'])
        path=self.root/'aikya/docs/architecture/architecture-overview.md'
        before=(path.read_bytes(),path.stat().st_mtime_ns)
        with patch.object(docs,'write_document',side_effect=AssertionError('Must not replay')):
            result=self.recovery.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'documents_reconciled');self.assertEqual(result['checks'],'not_run')
        self.assertFalse(result['delivery_authorized']);self.assertFalse(self.pending.exists())
        self.assertEqual(before,(path.read_bytes(),path.stat().st_mtime_ns))
        self.assertEqual(docs.preview(self.root,'aikya-docs',self.data,'author')['status'],'up_to_date')
        with self.assertRaises(ValueError):self.recovery.apply(self.root,value['plan'],approved=True)

    def test_baseline_effect_can_be_reconciled_without_recreating_it(self):
        data=dict(action='baseline',change_id='REQ-20261109-b2000001',sources=['source.py'])
        self.interrupted(data,'aikya-docs-sync')
        value=self.recovery.preview(self.root,'author')
        result=self.recovery.apply(self.root,value['plan'],approved=True)
        self.assertEqual(result['status'],'baseline_reconciled');self.assertFalse(self.pending.exists())
        self.assertFalse((self.root/'aikya/docs').exists())

    def test_partial_batch_is_manual_and_never_replayed_or_deleted(self):
        item=dict(document='decision',slug='local-store',payload=dict(title='Local storage',sections={'decision':'Use project-local data.'}))
        # Use a real catalog section to keep this test about interrupted effects.
        section=next(iter(docs.catalog(self.root,'decision')['sections']))
        item['payload']['sections']={section:'Use project-local data.'}
        data={**self.data,'documents':[*self.data['documents'],item]}
        plan=docs.preview(self.root,'aikya-docs',data,'author')['plan'];original=docs.write_document
        def interrupted(*args,**kwargs):
            original(*args,**kwargs);raise OSError('Interrupted after first document')
        with patch.object(docs,'write_document',side_effect=interrupted):
            with self.assertRaises(OSError):docs.apply(self.root,plan,approved=True)
        value=self.recovery.preview(self.root,'author')
        self.assertEqual(value['status'],'manual_reconciliation');self.assertIsNone(value['plan'])
        self.assertTrue(self.pending.exists())
        self.assertTrue((self.root/'aikya/docs/architecture/architecture-overview.md').exists())
        self.assertFalse((self.root/'aikya/docs/decisions/local-store.md').exists())

    def test_changed_source_blocks_reconciliation(self):
        self.interrupted();(self.root/'source.py').write_text('VALUE = 2\n')
        value=self.recovery.preview(self.root,'author')
        self.assertEqual(value['status'],'manual_reconciliation');self.assertTrue(self.pending.exists())

    def test_changed_profile_or_language_blocks_reconciliation(self):
        self.interrupted();path=self.root/'.harness/project-profile.json';original=path.read_bytes()
        path.write_text(path.read_text().replace('odd','sdd'))
        self.assertEqual(self.recovery.preview(self.root,'author')['status'],'manual_reconciliation')
        path.write_bytes(original)
        (self.root/'.aikya/docs-policy.json').write_text('{"schema_version":1,"language":"es"}')
        self.assertEqual(self.recovery.preview(self.root,'author')['status'],'manual_reconciliation')

    def test_source_change_during_memory_maintenance_keeps_recovery_pending(self):
        self.interrupted();value=self.recovery.preview(self.root,'author')
        from aikya.services import maintenance
        def changed(root):
            (root/'source.py').write_text('VALUE = 9\n');return dict(status='changed')
        with patch.object(maintenance,'after_write',side_effect=changed):
            with self.assertRaises(ValueError):self.recovery.apply(self.root,value['plan'],approved=True)
        self.assertTrue(self.pending.exists());self.assertFalse((self.root/'.aikya/pi/documentation/operations').exists())

    def test_changed_effect_after_preview_invalidates_confirmation(self):
        self.interrupted();value=self.recovery.preview(self.root,'author')
        path=self.root/'aikya/docs/architecture/architecture-overview.md';path.write_text('Owner edit\n')
        with self.assertRaises(ValueError):self.recovery.apply(self.root,value['plan'],approved=True)
        self.assertEqual(path.read_text(),'Owner edit\n');self.assertTrue(self.pending.exists())

    def test_foreign_author_or_tampered_pending_cannot_reconcile(self):
        self.interrupted()
        with self.assertRaises(ValueError):self.recovery.preview(self.root,'other-author')
        record=json.loads(self.pending.read_text());record['mac']='0'*64;self.pending.write_text(json.dumps(record))
        with self.assertRaises(ValueError):self.recovery.preview(self.root,'author')
        self.assertTrue(self.pending.exists())

    def test_recovered_transition_is_available_to_the_current_tdd_iteration(self):
        import sys
        from aikya.services import checks
        (self.root/'check.py').write_text('from pathlib import Path\nok="2" in Path("source.py").read_text()\nprint("TAP version 13\\n1..1")\nprint(("ok" if ok else "not ok")+" 1 - value")\nraise SystemExit(0 if ok else 1)\n')
        args=dict(change_id='recovered',scope=['source.py','check.py'],session_id='author',objective='Use two',acceptance=['Value is two'],
            tdd_paths=['check.py'],definitions=[dict(name='tests',argv=[sys.executable,'-I','-B','check.py'],cwd='.',
            report_format='tap',timeout_seconds=3,max_output_bytes=65536)])
        plan=checks.preview_snapshot(self.root,**args);checks.apply_snapshot(self.root,plan,approved=True)
        run=checks.preview_run(self.root,'recovered','tests','author','red');checks.execute(self.root,run,approved=True)
        self.interrupted();value=self.recovery.preview(self.root,'author');self.recovery.apply(self.root,value['plan'],approved=True)
        (self.root/'source.py').write_text('VALUE = 2\n')
        plan=checks.refresh_preview(self.root,'recovered','author');checks.apply_snapshot(self.root,plan,approved=True)
        run=checks.preview_run(self.root,'recovered','tests','author','green');checks.execute(self.root,run,approved=True)
        self.assertEqual(checks.status(self.root,'recovered')['status'],'review_required')


if __name__=='__main__':unittest.main()
