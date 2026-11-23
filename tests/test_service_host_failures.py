"""Host failure evidence is actionable without exposing exception content or paths."""
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO,StringIO
from aikya.services import runtime_state


class HostFailureEvidence(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.services.host_diagnostics'),'Bounded host diagnostics are absent')
        self.diagnostics=importlib.import_module('aikya.services.host_diagnostics')

    def test_permission_failure_records_only_safe_category_and_first_party_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            from aikya.storage import write_new
            path=Path(tmp)/'private-secret-file';path.write_text('Secret document')
            try:write_new(path,b'Never written')
            except OSError as error:result=self.diagnostics.describe(error)
            self.assertEqual(result['category'],'filesystem_conflict')
            self.assertEqual(result['stage'],'aikya.storage.write_new')
            self.assertNotIn(tmp,json.dumps(result));self.assertNotIn('private-secret',json.dumps(result))
            self.assertEqual(path.read_text(),'Secret document')
        result=self.diagnostics.describe(PermissionError(13,'SECRET_KEY=do-not-disclose','private-path'))
        self.assertEqual(result,{'category':'filesystem_permission','stage':None})

    def test_policy_and_invalid_inputs_do_not_echo_exception_text(self):
        for error,category in [(ValueError('private source text'),'policy_refused'),(TypeError('private arguments'),'invalid_request'),(RecursionError('private stack'),'invalid_request')]:
            self.assertEqual(self.diagnostics.describe(error),{'category':category,'stage':None})

    def test_real_host_refusal_preserves_generic_error_and_bounded_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            request=json.dumps({'action':'status','arguments':{'private-secret-argument':'x'}}).encode()
            class Input:
                buffer=BytesIO(request)
            output=StringIO()
            with patch.object(runtime_state.sys,'stdin',Input()),patch.object(runtime_state.sys,'stdout',output):
                self.assertEqual(runtime_state.main(['--root',tmp]),0)
            reply=json.loads(output.getvalue());self.assertFalse(reply['ok'])
            self.assertEqual(reply['error'],'runtime_state_unavailable')
            self.assertEqual(reply['diagnostic']['category'],'invalid_request')
            self.assertNotIn('private-secret',output.getvalue())
            self.assertNotIn(tmp,json.dumps(reply['diagnostic']))


if __name__=='__main__':unittest.main()
