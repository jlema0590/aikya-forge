"""Usage exports preserve unknowns and privacy; observations never certify a provider."""
import importlib
import importlib.util
import json
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.routing import pi_usage


class ProviderAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.acceptance'),'Privacy-bounded provider acceptance export is absent')
        self.service=importlib.import_module('aikya.services.acceptance');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()

    def test_unconfigured_export_is_read_only_and_does_not_claim_acceptance(self):
        with patch('aikya.installation.managed_runtime.resolve',side_effect=ValueError('Not installed')):
            value=self.service.snapshot(self.root)
        self.assertIsNone(value['recorded_tokens']);self.assertFalse(value['provider_verified']);self.assertIsNone(value['runtime_fingerprint'])
        self.assertEqual(list(self.root.iterdir()),[])

    def test_observed_usage_is_aggregated_without_source_paths_or_raw_identifiers(self):
        pi_usage.configure(self.root,tokens=100,calls=10,approved=True)
        context=dict(session='private-session',role='author',phase='implement',provider='private-provider',model='private-model')
        pi_usage.admit(self.root,'call-1',context);pi_usage.record(self.root,'call-1',dict(input=7,output=3,cacheRead=2,cacheWrite=1))
        with patch('aikya.installation.managed_runtime.resolve',side_effect=ValueError('Not installed')):
            value=self.service.snapshot(self.root)
        self.assertEqual(value['recorded_tokens'],13);self.assertEqual(value['calls'],1);self.assertFalse(value['provider_verified'])
        serialized=json.dumps(value)
        for private in (str(self.root),'private-session','private-provider','private-model'):self.assertNotIn(private,serialized)
        self.assertIsNone(value['quota_savings']);self.assertIsNone(value['quota_windows'])

    def test_unknown_usage_is_not_exported_as_zero_or_accepted(self):
        pi_usage.configure(self.root,tokens=100,calls=10,approved=True)
        pi_usage.admit(self.root,'call-1',dict(session='s',role='author',phase='plan',provider='fixture',model='fixture'))
        pi_usage.record(self.root,'call-1',None)
        with patch('aikya.installation.managed_runtime.resolve',side_effect=ValueError('Not installed')):
            value=self.service.snapshot(self.root)
        self.assertIsNone(value['recorded_tokens']);self.assertEqual(value['status'],'unknown_usage');self.assertEqual(value['uncertain_calls'],1)
        self.assertFalse(value['groups'][0]['usage_complete']);self.assertFalse(value['provider_verified'])

    def test_cli_exports_only_new_dossier_json_without_overwriting_evidence(self):
        from aikya.cli.dispatch import dispatch
        destination=self.root/'aikya/docs/validation/observation.json'
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(dispatch(['acceptance','export','--target',str(self.root),'--output',str(destination)]),(True,0))
            before=destination.read_bytes()
            self.assertEqual(dispatch(['acceptance','export','--target',str(self.root),'--output',str(destination)]),(True,2))
            self.assertEqual(destination.read_bytes(),before)
            self.assertEqual(dispatch(['acceptance','export','--target',str(self.root),'--output','../escape.json']),(True,2))
        self.assertFalse(json.loads(before)['provider_verified'])


if __name__=='__main__':unittest.main()
