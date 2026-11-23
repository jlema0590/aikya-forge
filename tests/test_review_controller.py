"""A local success claim never substitutes for current checks and review."""
import importlib
from pathlib import Path
import tempfile
import unittest
from aikya.review.candidates import freeze_candidate, store_candidate
from aikya.review.receipts import record_process

try:
    controller = importlib.import_module('aikya.review.controller')
except ModuleNotFoundError:
    controller = None


class ReviewControllerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(controller, 'RDD assessment is not implemented')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'code.py').write_text('VALUE = 1\n')
        self.candidate = freeze_candidate(self.root, 'change-1', ['code.py'], session_id='author')
        store_candidate(self.root, self.candidate, approved=True)

    def record(self, **kwargs):
        path = 'aikya/docs/validation/change-1/checks/tests.log'
        target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('Observed execution\n')
        args = dict(receipt_id='test-run', check='tests', argv=['python', '-m', 'unittest'],
                    exit_code=0, executed=1, skipped=0, evidence=path)
        args.update(kwargs)
        return record_process(self.root, self.candidate, **args)

    def test_arbitrary_markdown_does_not_satisfy_checks_or_review(self):
        (self.root / 'aikya/docs/validation/change-1/review.md').write_text('All checks and reviews PASSED')
        result = controller.assess_candidate(self.root, 'change-1')
        self.assertEqual(result['status'], 'pending_checks')
        self.assertFalse(result['can_close'])

    def test_process_success_requires_a_separate_review(self):
        self.record()
        result = controller.assess_candidate(self.root, 'change-1')
        self.assertEqual(result['status'], 'review_required')
        self.assertFalse(result['can_close'])
        self.assertFalse(result['delivery_authorized'])

    def test_zero_tests_or_skips_never_become_passing_evidence(self):
        self.record(executed=0, skipped=1)
        result = controller.assess_candidate(self.root, 'change-1')
        self.assertEqual(result['status'], 'unverified')
        self.assertFalse(result['can_close'])

    def test_failure_is_not_converted_to_pending_or_success(self):
        self.record(exit_code=1)
        self.assertEqual(controller.assess_candidate(self.root, 'change-1')['status'], 'failed')

    def test_windows_failure_status_remains_a_failure(self):
        self.record(exit_code=3221225477)
        self.assertEqual(controller.assess_candidate(self.root, 'change-1')['status'], 'failed')

    def test_changed_source_invalidates_successful_process_receipts(self):
        self.record()
        (self.root / 'code.py').write_text('VALUE = 2\n')
        self.assertEqual(controller.assess_candidate(self.root, 'change-1')['status'], 'stale')

    def test_unknown_checks_cannot_enter_the_approved_policy(self):
        with self.assertRaises(ValueError): self.record(check='unplanned-check')

    def test_checks_only_policy_does_not_grant_workflow_or_delivery_authority(self):
        self.candidate = freeze_candidate(self.root, 'change-1', ['code.py'], session_id='author',
            parent=self.candidate['id'], policy={'checks': ['tests'], 'review_required': False})
        store_candidate(self.root, self.candidate, approved=True)
        self.record()
        result = controller.assess_candidate(self.root, 'change-1')
        self.assertEqual(result['status'], 'checks_passed')
        self.assertFalse(result['can_close'])
        self.assertFalse(result['delivery_authorized'])


if __name__ == '__main__': unittest.main()
