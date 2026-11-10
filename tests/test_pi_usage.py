"""Durable project usage survives replay, resume and concurrent admission."""
import importlib
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
try: usage = importlib.import_module('aikya.routing.pi_usage')
except ModuleNotFoundError: usage = None


class PiUsageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(usage, 'Project Pi budget admission is absent')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.context = dict(session='author', role='author', phase='implement', provider='test', model='fixture')

    def configure(self, tokens=100):
        usage.configure(self.root, tokens=tokens, calls=10, approved=True)

    def test_budget_requires_explicit_configuration_and_approval(self):
        self.assertEqual(usage.status(self.root)['status'], 'unconfigured')
        with self.assertRaises(ValueError): usage.admit(self.root, 'call-1', self.context)
        with self.assertRaises(ValueError): usage.configure(self.root, tokens=100, calls=10)
        self.assertFalse((self.root / '.aikya').exists())

    def test_counts_are_durable_idempotent_and_not_provider_quota(self):
        self.configure(); usage.admit(self.root, 'call-1', self.context)
        counts = dict(input=10, output=20, cacheRead=30, cacheWrite=5)
        usage.record(self.root, 'call-1', counts); usage.record(self.root, 'call-1', counts)
        result = usage.status(self.root)
        self.assertEqual(result['recorded_tokens'], 65); self.assertEqual(result['calls'], 1)
        self.assertEqual(result['remaining_tokens'], 35)
        with self.assertRaises(ValueError): usage.record(self.root, 'call-1', {**counts, 'output': 21})
        self.assertNotIn('quota_percent', result)

    def test_unknown_or_interrupted_usage_blocks_further_inference(self):
        self.configure(); usage.admit(self.root, 'call-1', self.context)
        with self.assertRaises(ValueError): usage.admit(self.root, 'call-2', self.context)
        usage.record(self.root, 'call-1', None)
        self.assertEqual(usage.status(self.root)['status'], 'unknown_usage')
        with self.assertRaises(ValueError): usage.admit(self.root, 'call-2', self.context)

    def test_exhaustion_and_new_session_do_not_reset_accumulated_usage(self):
        self.configure(tokens=10); usage.admit(self.root, 'call-1', self.context)
        usage.record(self.root, 'call-1', dict(input=10, output=2, cacheRead=0, cacheWrite=0))
        with self.assertRaises(ValueError): usage.admit(self.root, 'call-2', {**self.context, 'session': 'resume'})
        with self.assertRaises(ValueError): self.configure(tokens=1000)
        self.assertEqual(usage.status(self.root)['recorded_tokens'], 12)

    def test_concurrent_admission_reserves_only_one_pending_call(self):
        self.configure()
        def admit(i):
            try: usage.admit(self.root, 'call-' + str(i), self.context); return 'admitted'
            except ValueError: return 'blocked'
        with ThreadPoolExecutor(2) as pool: values=list(pool.map(admit, range(2)))
        self.assertEqual(sorted(values), ['admitted', 'blocked'])

    def test_metadata_invalid_counts_and_custom_state_are_preserved(self):
        self.configure(); usage.admit(self.root, 'call-1', self.context)
        for counts in ({'input': 1}, dict(input=True, output=0, cacheRead=0, cacheWrite=0)):
            with self.assertRaises(ValueError): usage.record(self.root, 'call-1', counts)
        path=self.root / '.aikya/pi/usage.json'; path.write_text('{"custom":true}')
        with self.assertRaises(ValueError): usage.status(self.root)
        self.assertEqual(path.read_text(), '{"custom":true}')

    def test_explicit_limit_adjustment_preserves_recorded_and_unknown_usage(self):
        self.configure(tokens=10); usage.admit(self.root,'one',self.context)
        usage.record(self.root,'one',dict(input=10,output=1,cacheRead=0,cacheWrite=0))
        with self.assertRaises(ValueError): usage.adjust(self.root,tokens=100,calls=20)
        result=usage.adjust(self.root,tokens=100,calls=20,approved=True)
        self.assertEqual(result['recorded_tokens'],11); self.assertEqual(result['calls'],1)
        self.assertEqual(result['groups'][0]['phase'],'implement')
        usage.admit(self.root,'two',self.context); usage.record(self.root,'two',None)
        self.assertEqual(usage.adjust(self.root,tokens=1000,calls=30,approved=True)['status'],'unknown_usage')


if __name__ == '__main__': unittest.main()
