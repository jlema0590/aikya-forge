"""TDD needs a failed executed ancestor and unchanged tests, not a claimed Red."""
from pathlib import Path
import sys
import tempfile
import unittest
from aikya.review.candidates import freeze_candidate,store_candidate
from aikya.review.executor import check_binding,run_check
from aikya.review.controller import assess_candidate


class TddEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        (self.root/'value.txt').write_text('wrong')
        (self.root/'check.py').write_text('from pathlib import Path\nok=Path("value.txt").read_text()=="correct"\nprint("TAP version 13")\nprint("1..1")\nprint(("ok" if ok else "not ok")+" 1 - value")\nraise SystemExit(0 if ok else 1)\n')
        self.definition=dict(name='tests',argv=[sys.executable,'-I','-B','check.py'],cwd='.',report_format='tap',timeout_seconds=3,max_output_bytes=65536)
        self.policy=dict(checks=['tests'],review_required=True,definitions={'tests':check_binding(self.root,self.definition)},
                         tdd=dict(check='tests',paths=['check.py']))

    def candidate(self,parent=None):
        value=freeze_candidate(self.root,'tdd-change',['value.txt','check.py'],session_id='author',policy=self.policy,parent=parent)
        store_candidate(self.root,value,approved=True)
        return value

    def test_green_without_executed_red_is_not_ready_for_review(self):
        (self.root/'value.txt').write_text('correct');self.candidate()
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='green',approved=True)
        result=assess_candidate(self.root,'tdd-change')
        self.assertEqual(result['status'],'tdd_red_required');self.assertFalse(result['can_close'])

    def test_red_then_green_with_identical_tests_can_enter_review(self):
        red=self.candidate()
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='red',approved=True)
        (self.root/'value.txt').write_text('correct');self.candidate(red['id'])
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='green',approved=True)
        self.assertEqual(assess_candidate(self.root,'tdd-change')['status'],'review_required')

    def test_process_failure_without_a_test_report_does_not_become_red_or_crash_assessment(self):
        (self.root/'check.py').write_text('from pathlib import Path\nif Path("value.txt").read_text()!="correct":raise SystemExit(1)\nprint("TAP version 13")\nprint("1..1")\nprint("ok 1 - value")\n')
        red=self.candidate()
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='not-red',approved=True)
        (self.root/'value.txt').write_text('correct');self.candidate(red['id'])
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='green',approved=True)
        self.assertEqual(assess_candidate(self.root,'tdd-change')['status'],'tdd_red_required')

    def test_changed_test_invalidates_red_even_if_new_test_passes(self):
        red=self.candidate()
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='red',approved=True)
        (self.root/'value.txt').write_text('correct')
        with (self.root/'check.py').open('a') as stream:stream.write('# changed test\n')
        self.candidate(red['id'])
        run_check(self.root,'tdd-change',self.definition,session_id='author',run_id='green',approved=True)
        self.assertEqual(assess_candidate(self.root,'tdd-change')['status'],'tdd_red_required')


if __name__=='__main__':unittest.main()
