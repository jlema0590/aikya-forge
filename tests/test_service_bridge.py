"""The Pi bridge must never interpret a model request as a process command."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ServiceBridgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()

    def invoke(self, raw=None, **overrides):
        request = dict(schema=1, id="test-1", project=str(self.root),
                       operation="status", arguments={})
        request.update(overrides)
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
        result = subprocess.run([sys.executable, "-B", "-m", "aikya.services.bridge",
                                 "--root", str(self.root)], input=raw if raw is not None else json.dumps(request),
                                text=True, capture_output=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_status_does_not_initialize_project_or_require_an_sdk(self):
        before = list(self.root.iterdir())
        result = self.invoke()
        self.assertTrue(result["ok"])
        self.assertEqual(result["id"], "test-1")
        self.assertEqual(result["result"], {"configured": False, "methodology": None,
                                          "project_type": None})
        self.assertEqual(list(self.root.iterdir()), before)

    def test_only_public_profile_fields_cross_the_bridge(self):
        folder = self.root / ".harness"
        folder.mkdir()
        (folder / "project-profile.json").write_text(json.dumps(
            {"methodology": "odd", "project_type": "development", "api_key": "SECRET"}))
        result = self.invoke()
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["methodology"], "odd")
        self.assertNotIn("SECRET", json.dumps(result))

    def test_cross_project_request_fails(self):
        result = self.invoke(project=str(self.root.parent))
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_request")

    def test_unknown_operations_and_extra_fields_are_rejected(self):
        for fields in ({"operation": "bash", "arguments": {"command": "touch owned"}},
                       {"schema": 2}, {"extra": True}, {"arguments": {"unexpected": True}}):
            with self.subTest(fields=fields):
                self.assertFalse(self.invoke(**fields)["ok"])
        self.assertFalse((self.root / "owned").exists())

    def test_symlinked_profile_is_rejected_without_disclosing_contents(self):
        external = self.root / "outside.json"
        external.write_text('{"methodology":"sdd"}')
        (self.root / ".harness").mkdir()
        (self.root / ".harness/project-profile.json").symlink_to(external)
        self.assertFalse(self.invoke()["ok"])

    def test_corrupt_or_oversized_profile_is_not_reported_as_unconfigured(self):
        (self.root / ".harness").mkdir()
        profile = self.root / ".harness/project-profile.json"
        for value in ("not json", "[]", "x" * 100_001):
            profile.write_text(value)
            self.assertFalse(self.invoke()["ok"])

    def test_capabilities_do_not_claim_mutation_or_model_execution(self):
        result = self.invoke(operation="capabilities")
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["operations"], ["capabilities", "status", "context"])
        self.assertFalse(result["result"]["writes"])
        self.assertFalse(result["result"]["model_execution"])

    def test_malformed_oversized_and_duplicate_key_requests_fail_closed(self):
        envelope = json.dumps(dict(schema=1, id='test-1', project=str(self.root),
                                   operation='status', arguments={}))
        duplicate = envelope[:-1] + ',"operation":"status"}'
        for raw in (duplicate, 'x' * 16_385,
                    '[' * 1200 + '0' + ']' * 1200, 'not JSON'):
            self.assertFalse(self.invoke(raw=raw)["ok"])

    def test_boolean_schema_is_not_a_version_number(self):
        self.assertFalse(self.invoke(schema=True)["ok"])

    def test_context_is_scoped_bounded_and_does_not_initialize_an_index(self):
        (self.root / "value.py").write_text('class ScopedValue: pass\n')
        (self.root / "other.py").write_text('class PrivateOther: pass\n')
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.invoke(operation="context", arguments=dict(query="ScopedValue", paths=["value.py"], max_chars=1000))
        self.assertTrue(result["ok"])
        self.assertIn("ScopedValue", json.dumps(result["result"]))
        self.assertNotIn("PrivateOther", json.dumps(result["result"]))
        self.assertLessEqual(len(json.dumps(result["result"], ensure_ascii=False)), 1000)
        self.assertEqual(before, {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_context_requires_explicit_safe_nonempty_scope(self):
        for paths in (None, [], ["../outside.py"], [".env"], [".aikya/auth.json"], ["x.py"] * 21):
            self.assertFalse(self.invoke(operation="context", arguments=dict(query="", paths=paths, max_chars=1000))["ok"])

    def test_context_never_refreshes_even_when_indexing_is_enabled(self):
        from aikya.code_index.policy import configure
        configure(self.root, approved=True)
        (self.root / "value.py").write_text('class ScopedValue: pass\n')
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertTrue(self.invoke(operation="context", arguments=dict(query="", paths=["value.py"], max_chars=1000))["ok"])
        self.assertEqual(before, {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_context_fallback_covers_every_registered_source_suffix(self):
        from aikya.code_index.policy import CODE_SUFFIXES
        for suffix in sorted(CODE_SUFFIXES):
            with self.subTest(suffix=suffix):
                name = 'source' + suffix
                (self.root / name).write_text('SCOPED_SOURCE_MARKER\n')
                reply = self.invoke(operation='context', arguments=dict(query='', paths=[name], max_chars=1000))
                self.assertTrue(reply['ok'])
                self.assertEqual(reply['result']['context'][0]['path'], name)
                self.assertIn('SCOPED_SOURCE_MARKER', reply['result']['context'][0]['text'])

    def test_stale_index_never_supplies_old_source_or_refreshes_itself(self):
        from aikya.code_index.policy import configure
        from aikya.code_index.sync import sync
        configure(self.root, approved=True)
        path = self.root / 'value.py'; path.write_text('class PreviousValue: pass\n')
        sync(self.root)
        index = self.root / '.harness/state/code-index/index.sqlite'; previous = index.read_bytes()
        path.write_text('class ReplacementValue: pass\n')
        reply = self.invoke(operation='context', arguments=dict(query='', paths=['value.py'], max_chars=1000))
        self.assertTrue(reply['ok'])
        self.assertNotIn('PreviousValue', json.dumps(reply['result']))
        self.assertIn('source_changed', reply['result']['diagnostics'])
        self.assertEqual(index.read_bytes(), previous)

    def test_installed_nested_profile_is_read_without_leaking_decisions(self):
        (self.root / ".harness").mkdir()
        (self.root / ".harness/project-profile.json").write_text(json.dumps(
            {"decisions": {"methodology": "sdd", "project_type": "devops", "private": "SECRET"}}))
        result = self.invoke()
        self.assertEqual(result["result"], dict(configured=True, methodology="sdd", project_type="devops"))
        self.assertNotIn("SECRET", json.dumps(result))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO required")
    def test_profile_fifo_cannot_block_the_service(self):
        (self.root / ".harness").mkdir()
        os.mkfifo(self.root / ".harness/project-profile.json")
        self.assertFalse(self.invoke()["ok"])


if __name__ == "__main__":
    unittest.main()
