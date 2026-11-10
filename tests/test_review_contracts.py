"""RDD checks exercise real files and durable records, not model verdict text."""
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

try:
    candidates = importlib.import_module('aikya.review.candidates')
    receipts = importlib.import_module('aikya.review.receipts')
except ModuleNotFoundError:
    candidates = receipts = None


class ReviewContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(candidates, 'RDD candidate contracts are not implemented')
        self.assertIsNotNone(receipts, 'RDD durable receipts are not implemented')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'value.py').write_text('VALUE = 0\n')

    def freeze(self, **kwargs):
        return candidates.freeze_candidate(self.root, 'change-1', ['value.py'],
                                           session_id='session-1', **kwargs)

    def evidence(self, value='PASS\n'):
        path = 'aikya/docs/validation/change-1/checks/unit.log'
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
        return path

    def record(self, candidate, **kwargs):
        values = dict(receipt_id='run-1', check='tests', argv=['python', '-m', 'unittest'],
                      exit_code=0, evidence=self.evidence(), executed=1, skipped=0)
        values.update(kwargs)
        return receipts.record_process(self.root, candidate, **values)

    def test_snapshot_changes_when_an_untracked_file_is_added_or_removed(self):
        first = self.freeze()
        self.assertTrue(candidates.is_current(self.root, first))
        (self.root / 'new.java').write_text('class New {}')
        self.assertFalse(candidates.is_current(self.root, first))
        (self.root / 'new.java').unlink()
        self.assertTrue(candidates.is_current(self.root, first))
        self.assertFalse((self.root / '.git').exists())

    def test_test_and_configuration_changes_invalidate_the_snapshot(self):
        for name in ('test_value.py', 'package.json', 'package-lock.json'):
            with self.subTest(name=name):
                first = self.freeze()
                (self.root / name).write_text('{}')
                self.assertFalse(candidates.is_current(self.root, first))
                (self.root / name).unlink()

    def test_project_session_and_policy_are_bound(self):
        first = self.freeze()
        changed = candidates.freeze_candidate(self.root, 'change-1', ['value.py'], session_id='session-2')
        self.assertNotEqual(first['id'], changed['id'])
        self.assertNotEqual(first['id'], self.freeze(policy={'checks': ['lint'], 'review_required': True})['id'])
        with tempfile.TemporaryDirectory() as other:
            self.assertFalse(candidates.is_current(Path(other), first))

    def test_unsafe_scope_or_symlink_never_becomes_a_candidate(self):
        for scope in ([], ['../outside'], ['.env'], ['value.py', 'value.py']):
            with self.assertRaises(ValueError):
                candidates.freeze_candidate(self.root, 'change-1', scope, session_id='session-1')
        (self.root / 'linked.py').symlink_to(self.root / 'value.py')
        with self.assertRaises(ValueError): self.freeze()

    def test_candidate_storage_needs_authorization_and_preserves_custom_files(self):
        candidate = self.freeze()
        with self.assertRaises(ValueError): candidates.store_candidate(self.root, candidate)
        target = self.root / 'aikya/docs/validation/change-1/candidate.json'
        target.parent.mkdir(parents=True)
        target.write_text('User-owned custom document')
        with self.assertRaises(ValueError): candidates.store_candidate(self.root, candidate, approved=True)
        self.assertEqual(target.read_text(), 'User-owned custom document')

    def test_successor_cannot_hide_changed_source_outside_its_declared_review_scope(self):
        first=self.freeze();candidates.store_candidate(self.root,first,approved=True)
        (self.root/'hidden.py').write_text('HIDDEN_CHANGE=True\n')
        with self.assertRaises(ValueError):candidates.store_candidate(self.root,self.freeze(parent=first['id']),approved=True)
        expanded=candidates.freeze_candidate(self.root,'change-1',['value.py','hidden.py'],session_id='session-1',parent=first['id'])
        candidates.store_candidate(self.root,expanded,approved=True)
        self.assertEqual(candidates.load_candidate(self.root,'change-1')['scope'],['hidden.py','value.py'])

    def test_successor_preserves_history_and_requires_the_current_parent(self):
        first = self.freeze()
        candidates.store_candidate(self.root, first, approved=True)
        self.assertTrue(candidates.is_current(self.root, first))
        (self.root / 'value.py').write_text('VALUE = 1\n')
        with self.assertRaises(ValueError): candidates.store_candidate(self.root, self.freeze(), approved=True)
        second = self.freeze(parent=first['id'])
        candidates.store_candidate(self.root, second, approved=True)
        self.assertEqual(candidates.load_candidate(self.root, 'change-1')['id'], second['id'])
        archived = self.root / f"aikya/docs/validation/change-1/candidates/{first['id']}.json"
        self.assertEqual(json.loads(archived.read_text())['id'], first['id'])

    def test_process_receipt_is_durable_and_duplicate_submission_is_idempotent(self):
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        one = self.record(candidate)
        two = self.record(candidate)
        self.assertEqual(one, two)
        self.assertEqual(len(receipts.load_receipts(self.root, 'change-1')), 1)
        with self.assertRaises(ValueError): self.record(candidate, exit_code=1)
        self.assertTrue(candidates.is_current(self.root, candidate))

    def test_stale_or_unsaved_candidate_cannot_receive_evidence(self):
        candidate = self.freeze()
        with self.assertRaises(ValueError): self.record(candidate)
        candidates.store_candidate(self.root, candidate, approved=True)
        (self.root / 'value.py').write_text('VALUE = 1\n')
        with self.assertRaises(ValueError): self.record(candidate)

    def test_evidence_hash_and_journal_chain_are_checked_on_read(self):
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        self.record(candidate)
        self.evidence('Changed log\n')
        with self.assertRaises(ValueError): receipts.load_receipts(self.root, 'change-1')
        self.evidence()
        path = self.root / 'aikya/docs/validation/change-1/receipts.jsonl'
        value = path.read_text().replace('"exit_code":0', '"exit_code":1')
        self.assertNotEqual(value, path.read_text())
        path.write_text(value)
        with self.assertRaises(ValueError): receipts.load_receipts(self.root, 'change-1')

    def test_failed_and_empty_test_runs_are_recorded_without_fabricating_success(self):
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        value = self.record(candidate, exit_code=1, executed=0, skipped=1)
        self.assertEqual(value['payload']['exit_code'], 1)
        self.assertEqual(value['payload']['executed'], 0)

    def test_concurrent_duplicate_receipts_are_not_appended_twice(self):
        from concurrent.futures import ThreadPoolExecutor
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        evidence = self.evidence()
        def submit(_):
            return receipts.record_process(self.root, candidate, receipt_id='same-run', check='tests',
                argv=['python'], exit_code=0, evidence=evidence, executed=1, skipped=0)
        with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(submit, range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(receipts.load_receipts(self.root, 'change-1')), 1)

    def test_rehashed_but_semantically_invalid_receipt_is_rejected(self):
        from aikya.review.contracts import digest, encoded
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        self.record(candidate)
        path = self.root / 'aikya/docs/validation/change-1/receipts.jsonl'
        original = path.read_text()
        for key, value in [('session_id', 'other-session'), ('candidate', 'a' * 64),
                           ('executed', True), ('kind', 'review'), ('evidence', 'value.py')]:
            lines = original.splitlines()
            row = json.loads(lines[1]); row['payload'][key] = value
            row['hash'] = digest({k: row[k] for k in ('previous', 'payload')})
            path.write_text(lines[0] + '\n' + encoded(row) + '\n')
            with self.subTest(key=key), self.assertRaises(ValueError):
                receipts.load_receipts(self.root, 'change-1')
        path.write_text(original)

    def test_corrupt_candidate_scope_is_not_loaded_even_with_a_matching_digest(self):
        from aikya.review.contracts import digest
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        candidate['scope'] = []
        candidate['id'] = digest({k: v for k, v in candidate.items() if k != 'id'})
        (self.root / 'aikya/docs/validation/change-1/candidate.json').write_text(json.dumps(candidate))
        with self.assertRaises(ValueError): candidates.load_candidate(self.root, 'change-1')

    def test_receipts_bind_command_arguments_without_persisting_secrets(self):
        from aikya.review.contracts import digest
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        argv = ['python', 'check.py', '--token', 'PRIVATE_TOKEN_123']
        receipt = self.record(candidate, argv=argv)
        self.assertEqual(receipt['payload'].get('argv_hash'), digest(argv))
        self.assertNotIn('PRIVATE_TOKEN_123', (self.root / 'aikya/docs/validation/change-1/receipts.jsonl').read_text())

    def test_deleted_sources_and_oversized_files_do_not_reuse_a_candidate(self):
        first = self.freeze()
        (self.root / 'value.py').unlink()
        self.assertFalse(candidates.is_current(self.root, first))
        (self.root / 'value.py').write_bytes(b'x' * 10_000_001)
        with self.assertRaises(ValueError): self.freeze()

    def test_custom_journal_is_preserved(self):
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        path = self.root / 'aikya/docs/validation/change-1/receipts.jsonl'
        path.write_text('Custom team evidence')
        with self.assertRaises(ValueError): self.record(candidate)
        self.assertEqual(path.read_text(), 'Custom team evidence')

    def test_current_pointer_without_its_immutable_manifest_is_rejected(self):
        candidate = self.freeze()
        candidates.store_candidate(self.root, candidate, approved=True)
        history = self.root / f"aikya/docs/validation/change-1/candidates/{candidate['id']}.json"
        history.unlink()
        with self.assertRaises(ValueError): candidates.load_candidate(self.root, 'change-1')

    @unittest.skipUnless(shutil.which('git'), 'Git is required for base binding')
    def test_git_base_change_invalidates_an_unchanged_working_tree(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        hooks = self.root / 'empty-hooks'; hooks.mkdir()
        def git(*args):
            subprocess.run(['git', '-c', 'init.templateDir=', '-c', 'core.fsmonitor=false',
                '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                '-c', 'core.hooksPath=' + str(hooks), *args], cwd=self.root, env=env,
                check=True, capture_output=True)
        git('init')
        unborn = self.freeze()
        self.assertIsNone(unborn['base'])
        git('add', 'value.py'); git('commit', '--no-gpg-sign', '-m', 'Fixture')
        first = self.freeze()
        self.assertFalse(candidates.is_current(self.root, unborn))
        git('commit', '--no-gpg-sign', '--allow-empty', '-m', 'Next base')
        self.assertFalse(candidates.is_current(self.root, first))


if __name__ == '__main__': unittest.main()
