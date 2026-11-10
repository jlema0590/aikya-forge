"""Actual check processes must match a frozen definition and produce fresh reports."""
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from aikya.review.candidates import freeze_candidate, store_candidate
from aikya.review.controller import assess_candidate
from aikya.review.receipts import load_receipts, record_process

try:
    executor = importlib.import_module('aikya.review.executor')
except ModuleNotFoundError:
    executor = None


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(executor, 'Approved check execution is not implemented')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'source.py').write_text('VALUE = 1\n')

    def definition(self, script=None, **extra):
        script = script or ('import os;from pathlib import Path;'
            'Path(os.environ["AIKYA_TEST_REPORT"]).write_text(\'<testsuite tests="1"><testcase name="pass"/></testsuite>\')')
        return dict(name='tests', argv=[sys.executable, '-I', '-B', '-c', script], cwd='.',
                    report_format='junit', timeout_seconds=2, max_output_bytes=65536, **extra)

    def prepare(self, definition):
        binding = executor.check_binding(self.root, definition)
        self.candidate = freeze_candidate(self.root, 'change-1', ['source.py'], session_id='author',
            policy={'checks': ['tests'], 'review_required': True, 'definitions': {'tests': binding}})
        store_candidate(self.root, self.candidate, approved=True)

    def run_check(self, definition, **kwargs):
        options = dict(session_id='author', run_id='run-1', approved=True)
        options.update(kwargs)
        return executor.run_check(self.root, 'change-1', definition, **options)

    def test_real_process_creates_counts_and_an_execution_bound_receipt(self):
        definition = self.definition(); self.prepare(definition)
        result = self.run_check(definition)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['counts'], {'executed': 1, 'failed': 0, 'skipped': 0})
        receipt = load_receipts(self.root, 'change-1')[0]['payload']
        self.assertEqual(receipt['definition_hash'], self.candidate['policy']['definitions']['tests'])
        self.assertEqual(receipt['executed'], 1)
        metadata = json.loads((self.root / result['evidence']).read_text())
        self.assertGreaterEqual(metadata['finished_ns'], metadata['started_ns'])
        self.assertGreaterEqual(metadata['duration_ns'], 0)
        self.assertEqual(assess_candidate(self.root, 'change-1')['status'], 'review_required')

    def test_refusal_happens_before_launch_when_approval_session_or_definition_differs(self):
        definition = self.definition('from pathlib import Path;Path("SIDE_EFFECT").write_text("bad")')
        self.prepare(definition)
        for options in ({'approved': False}, {'session_id': 'other'}):
            with self.assertRaises(ValueError): self.run_check(definition, **options)
        changed = {**definition, 'timeout_seconds': 3}
        with self.assertRaises(ValueError): self.run_check(changed)
        self.assertFalse((self.root / 'SIDE_EFFECT').exists())

    def test_same_run_id_never_spawns_a_second_process(self):
        definition = self.definition(); self.prepare(definition)
        self.run_check(definition)
        with self.assertRaises(ValueError): self.run_check(definition)
        self.assertEqual(len(load_receipts(self.root, 'change-1')), 1)

    def test_unknown_interrupted_attempt_blocks_a_new_run_identity(self):
        definition = self.definition(); self.prepare(definition)
        path = self.root / 'aikya/docs/validation/change-1/checks/old-run/execution.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'schema': 1, 'generated_by': 'aikya-check-executor',
            'candidate': self.candidate['id'], 'check': 'tests', 'status': 'pending'}))
        with self.assertRaises(ValueError): self.run_check(definition, run_id='new-run')
        self.assertFalse((path.parent.parent / 'new-run').exists())

    def test_a_manual_result_cannot_satisfy_an_execution_bound_check(self):
        definition = self.definition(); self.prepare(definition)
        path = self.root / 'aikya/docs/validation/change-1/checks/fake.log'
        path.parent.mkdir(); path.write_text('PASS')
        with self.assertRaises(ValueError):
            record_process(self.root, self.candidate, receipt_id='fake', check='tests', argv=['true'],
                           exit_code=0, executed=100, skipped=0, evidence=path.relative_to(self.root).as_posix())

    def test_zero_tests_and_a_missing_report_are_not_passing(self):
        for script, expected in [('import os;from pathlib import Path;Path(os.environ["AIKYA_TEST_REPORT"]).write_text(\'<testsuite tests="0"/>\')', 'unverified'),
                                 ('pass', 'invalid_report')]:
            with self.subTest(expected=expected):
                definition = self.definition(script)
                binding = executor.check_binding(self.root, definition)
                parent = getattr(self, 'candidate', {}).get('id')
                self.candidate = freeze_candidate(self.root, 'change-1', ['source.py'], session_id='author', parent=parent,
                    policy={'checks': ['tests'], 'review_required': True, 'definitions': {'tests': binding}})
                store_candidate(self.root, self.candidate, approved=True)
                result = self.run_check(definition, run_id='run-' + expected)
                self.assertEqual(result['status'], expected)
                self.assertFalse(assess_candidate(self.root, 'change-1')['can_close'])

    def test_timeout_cancellation_and_output_limit_are_durable_failures(self):
        definitions = [({**self.definition('import time;time.sleep(10)'), 'timeout_seconds': .1}, {}, 'timed_out'),
                       (self.definition('import time;time.sleep(10)'), {'cancel': lambda: True}, 'cancelled'),
                       ({**self.definition('print("x" * 1000000)'), 'max_output_bytes': 1024}, {}, 'output_limit')]
        for index, (definition, options, expected) in enumerate(definitions):
            parent = getattr(self, 'candidate', {}).get('id')
            binding = executor.check_binding(self.root, definition)
            self.candidate = freeze_candidate(self.root, 'change-1', ['source.py'], session_id='author', parent=parent,
                policy={'checks': ['tests'], 'review_required': True, 'definitions': {'tests': binding}})
            store_candidate(self.root, self.candidate, approved=True)
            result = self.run_check(definition, run_id='failure-' + str(index), **options)
            self.assertEqual(result['status'], expected)
            self.assertFalse(assess_candidate(self.root, 'change-1')['can_close'])

    def test_command_output_is_not_persisted_as_raw_text(self):
        definition = self.definition('print("PRIVATE_OUTPUT_TOKEN");' + self.definition()['argv'][-1])
        self.prepare(definition); self.run_check(definition)
        for path in (self.root / 'aikya/docs/validation/change-1').rglob('*'):
            if path.is_file(): self.assertNotIn(b'PRIVATE_OUTPUT_TOKEN', path.read_bytes())

    @unittest.skipIf(sys.platform=='win32','POSIX process-group lifecycle')
    def test_already_exited_unreaped_child_is_reaped_without_signalling_error(self):
        import time
        from aikya.review.process import _stop
        process=subprocess.Popen([sys.executable,'-I','-B','-c','print("finished")'],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:
            self.assertEqual(process.stdout.read(),b'finished\n')
            time.sleep(.05)  # EOF has closed both streams; retain the unreaped child.
            _stop(process)
            self.assertEqual(process.returncode,0)
        finally:
            process.wait(timeout=3);process.stdout.close();process.stderr.close()

    def test_process_definition_cannot_launch_under_an_implicit_test_policy(self):
        definition={**self.definition('from pathlib import Path;Path("SIDE_EFFECT").write_text("bad")'),
                    'report_format':'process'}
        self.prepare(definition)
        with self.assertRaises(ValueError):self.run_check(definition)
        self.assertFalse((self.root/'SIDE_EFFECT').exists())
        self.assertFalse((self.root/'aikya/docs/validation/change-1/checks').exists())

    def test_a_check_that_changes_source_cannot_publish_passing_evidence(self):
        definition = self.definition('from pathlib import Path;Path("source.py").write_text("VALUE = 2\\n");' + self.definition()['argv'][-1])
        self.prepare(definition)
        result = self.run_check(definition)
        self.assertEqual(result['status'], 'candidate_changed')
        self.assertEqual(load_receipts(self.root, 'change-1'), [])

    def test_keyboard_interrupt_is_recorded_as_cancellation(self):
        definition = self.definition('import time;time.sleep(10)'); self.prepare(definition)
        def interrupted(): raise KeyboardInterrupt
        self.assertEqual(self.run_check(definition, cancel=interrupted)['status'], 'cancelled')

    @unittest.skipUnless(shutil.which('node'), 'Node required for native TAP acceptance')
    def test_native_node_test_runner_produces_verified_tap_counts(self):
        (self.root / 'check.test.cjs').write_text('const t=require("node:test");t("actual test",()=>{});')
        definition = {**self.definition(), 'argv': [shutil.which('node'), '--test', '--test-reporter=tap', 'check.test.cjs'], 'report_format': 'tap'}
        self.prepare(definition)
        self.assertEqual(self.run_check(definition)['counts'], {'executed': 1, 'failed': 0, 'skipped': 0})

    @unittest.skipUnless(shutil.which('go'), 'Go required for native JSON acceptance')
    def test_native_go_test_runner_produces_verified_json_counts(self):
        (self.root / 'go.mod').write_text('module example.test/aikya\n\ngo 1.20\n')
        (self.root / 'value_test.go').write_text('package sample\nimport "testing"\nfunc TestValue(t *testing.T) {}\n')
        definition = {**self.definition(), 'argv': [shutil.which('go'), 'test', '-json', './...'],
                      'report_format': 'go-json', 'timeout_seconds': 120}
        environment = dict(GOCACHE=str(self.root / 'aikya/docs/validation/change-1/go-cache'),
                           GOTOOLCHAIN='local', GOPROXY='off', GOWORK='off', GOENV='off')
        self.candidate = freeze_candidate(self.root, 'change-1', ['value_test.go'], session_id='author',
            policy={'checks': ['tests'], 'review_required': True,
                    'definitions': {'tests': executor.check_binding(self.root, definition, environment)}})
        store_candidate(self.root, self.candidate, approved=True)
        result = self.run_check(definition, environment=environment)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['counts'], {'executed': 1, 'failed': 0, 'skipped': 0})


if __name__ == '__main__': unittest.main()
