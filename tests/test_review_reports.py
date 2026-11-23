"""Only complete, internally consistent runner reports become test counts."""
import importlib
import unittest

try:
    reports = importlib.import_module('aikya.review.reports')
except ModuleNotFoundError:
    reports = None


class ReportTests(unittest.TestCase):
    def parse(self, kind, raw):
        self.assertIsNotNone(reports, 'Runner report adapters are absent')
        return reports.parse_report(kind, raw.encode())

    def test_junit_counts_actual_cases_and_not_nested_summary_totals(self):
        value = self.parse('junit', '<testsuites tests="3"><testsuite tests="3">'
            '<testcase name="pass"/><testcase name="bad"><failure>private</failure></testcase>'
            '<testcase name="later"><skipped/></testcase></testsuite></testsuites>')
        self.assertEqual(value, {'executed': 2, 'failed': 1, 'skipped': 1})

    def test_junit_zero_tests_remains_zero(self):
        self.assertEqual(self.parse('junit', '<testsuite tests="0"/>'),
                         {'executed': 0, 'failed': 0, 'skipped': 0})

    def test_malformed_or_inconsistent_junit_is_rejected(self):
        for raw in ('<testsuite tests="2"><testcase name="only"/></testsuite>',
                    '<testsuites><testsuite tests="2"><testcase name="only"/></testsuite></testsuites>',
                    '<testsuite failures="1"><testcase name="a"/></testsuite>',
                    '<testsuite><testcase name="same"/><testcase name="same"/></testsuite>',
                    '<!DOCTYPE x [<!ENTITY a "hidden">]><testsuite>&a;</testsuite>',
                    '<testsuite>', '<unrelated/>'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): self.parse('junit', raw)

    def test_tap_plan_and_directives_are_not_false_passes(self):
        value = self.parse('tap', 'TAP version 13\nok 1 - yes\nnot ok 2 - broken\n'
                           'ok 3 - later # SKIP unavailable\nnot ok 4 - future # TODO\n1..4\n')
        self.assertEqual(value, {'executed': 2, 'failed': 1, 'skipped': 2})

    def test_tap_incomplete_duplicate_or_bailed_out_runs_are_rejected(self):
        for raw in ('1..2\nok 1\n', '1..2\nok 1\nok 1\n', '1..1\nBail out!\n', 'ok 1\n', 'ok 1\n1..2\nok 2\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): self.parse('tap', raw)

    def test_trx_uses_results_and_validates_counters(self):
        raw = '<TestRun xmlns="urn:example"><Results><UnitTestResult testId="a" outcome="Passed"/>'
        raw += '<UnitTestResult testId="b" outcome="NotExecuted"/></Results>'
        raw += '<ResultSummary outcome="Completed"><Counters total="2" passed="1" failed="0" notExecuted="1"/></ResultSummary></TestRun>'
        self.assertEqual(self.parse('trx', raw), {'executed': 1, 'failed': 0, 'skipped': 1})
        with self.assertRaises(ValueError): self.parse('trx', raw.replace('total="2"', 'total="3"'))

    def test_go_requires_terminal_package_events_and_counts_test_results(self):
        raw = '\n'.join(['{"Action":"run","Package":"demo","Test":"TestA"}',
                         '{"Action":"pass","Package":"demo","Test":"TestA"}',
                         '{"Action":"skip","Package":"demo","Test":"TestB"}',
                         '{"Action":"pass","Package":"demo"}'])
        self.assertEqual(self.parse('go-json', raw), {'executed': 1, 'failed': 0, 'skipped': 1})
        with self.assertRaises(ValueError): self.parse('go-json', raw.rsplit('\n', 1)[0])

    def test_unknown_format_or_oversized_reports_are_rejected(self):
        with self.assertRaises(ValueError): self.parse('unknown', '{}')
        with self.assertRaises(ValueError): self.parse('junit', 'x' * 1_048_577)


if __name__ == '__main__': unittest.main()
