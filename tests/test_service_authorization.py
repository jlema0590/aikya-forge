"""Host-issued one-use grants bind every write to source, content and session."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

try: auth = importlib.import_module('aikya.services.authorization')
except ModuleNotFoundError: auth = None


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(auth, 'Host authorization boundary is absent')
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'value.py').write_text('VALUE = 1\n')
        self.key = os.urandom(32)
        self.args = dict(path='value.py', content='VALUE = 2\n')

    def grant(self, **kwargs):
        return auth.issue(self.root, 'session-a', self.args, self.key, **kwargs)

    def test_real_write_requires_a_host_grant_and_consumes_it_once(self):
        token = self.grant()
        result = auth.apply_write(self.root, 'session-a', self.args, token, self.key)
        self.assertEqual((self.root / 'value.py').read_text(), 'VALUE = 2\n')
        self.assertEqual(result['after'], hashlib.sha256(b'VALUE = 2\n').hexdigest())
        with self.assertRaises(ValueError): auth.apply_write(self.root, 'session-a', self.args, token, self.key)

    def test_wrong_authority_session_content_and_source_are_rejected_before_effect(self):
        token = self.grant()
        for session, args, key in [('session-b', self.args, self.key),
                ('session-a', {**self.args, 'content': 'VALUE = 3\n'}, self.key),
                ('session-a', self.args, os.urandom(32))]:
            with self.assertRaises(ValueError): auth.apply_write(self.root, session, args, token, key)
        (self.root / 'value.py').write_text('USER_EDIT = 1\n')
        with self.assertRaises(ValueError): auth.apply_write(self.root, 'session-a', self.args, token, self.key)
        self.assertEqual((self.root / 'value.py').read_text(), 'USER_EDIT = 1\n')

    def test_expired_and_cross_project_grants_are_refused(self):
        token = self.grant(now=100, ttl=10)
        with self.assertRaises(ValueError): auth.apply_write(self.root, 'session-a', self.args, token, self.key, now=111)
        with tempfile.TemporaryDirectory() as other:
            Path(other, 'value.py').write_text('VALUE = 1\n')
            with self.assertRaises(ValueError): auth.apply_write(Path(other), 'session-a', self.args, self.grant(), self.key)

    def test_new_files_permissions_and_control_paths(self):
        self.args = dict(path='new.py', content='NEW = True\n')
        auth.apply_write(self.root, 'session-a', self.args, self.grant(), self.key)
        self.assertEqual((self.root / 'new.py').read_text(), 'NEW = True\n')
        for path in ('../outside', '.aikya/pi/agent/auth.json', '.codex/config.toml', 'AGENTS.md', 'x/CLAUDE.md', 'aikya/docs/overview.md'):
            with self.assertRaises(ValueError): auth.preview(self.root, dict(path=path, content='bad'))
        with self.assertRaises(ValueError): auth.preview(self.root, dict(path='report.md', content='Missing footer'))

    def test_preview_and_denial_do_not_initialize_state(self):
        result = auth.preview(self.root, self.args)
        self.assertEqual(result['before'], hashlib.sha256(b'VALUE = 1\n').hexdigest())
        self.assertFalse((self.root / '.aikya').exists())
        with self.assertRaises(ValueError): auth.apply_write(self.root, 'session-a', self.args, 'forged', self.key)
        self.assertFalse((self.root / '.aikya').exists())

    def test_oversized_source_is_refused_before_grant_and_write(self):
        self.args['content']='x\n'*1001
        with self.assertRaises(ValueError):self.grant()
        self.assertEqual((self.root/'value.py').read_text(),'VALUE = 1\n')
        self.assertFalse((self.root/'.aikya').exists())

    def test_exactly_one_thousand_source_lines_can_be_written(self):
        self.args['content']='x\n'*1000
        auth.apply_write(self.root,'session-a',self.args,self.grant(),self.key)
        self.assertEqual(len((self.root/'value.py').read_text().splitlines()),1000)

    def test_size_exception_is_content_bound_and_rechecked_at_execution(self):
        self.args['content']='x\n'*1001
        folder=self.root/'.aikya';folder.mkdir()
        exception=folder/'code-quality-exceptions.json'
        exception.write_text(json.dumps(dict(schema=1,exceptions=[dict(path='value.py',
            sha256=hashlib.sha256(self.args['content'].encode()).hexdigest(),
            reason='Reviewed migration fixture; replace with focused modules next.') ])))
        token=self.grant();exception.unlink()
        with self.assertRaises(ValueError):auth.apply_write(self.root,'session-a',self.args,token,self.key)
        self.assertEqual((self.root/'value.py').read_text(),'VALUE = 1\n')

    def test_duplicate_markdown_footer_is_refused_before_grant(self):
        intent=dict(path='report.md',content='GENERATED BY AIKYA HARNESS\n\nGENERATED BY AIKYA HARNESS\n')
        with self.assertRaises(ValueError):auth.issue(self.root,'session-a',intent,self.key)
        self.assertFalse((self.root/'report.md').exists())

    def test_concurrent_replay_has_only_one_effect(self):
        token = self.grant()
        def apply():
            try: auth.apply_write(self.root, 'session-a', self.args, token, self.key); return 'written'
            except ValueError: return 'refused'
        with ThreadPoolExecutor(2) as pool: results = list(pool.map(lambda _: apply(), range(2)))
        self.assertEqual(sorted(results), ['refused', 'written'])

    def test_symlinked_state_and_destination_are_refused(self):
        (self.root / 'linked.py').symlink_to(self.root / 'value.py')
        with self.assertRaises(ValueError): auth.preview(self.root, dict(path='linked.py', content='bad'))
        token = self.grant()
        (self.root / '.aikya').symlink_to(self.root / 'redirect', target_is_directory=True)
        with self.assertRaises(ValueError): auth.apply_write(self.root, 'session-a', self.args, token, self.key)
        self.assertEqual((self.root / 'value.py').read_text(), 'VALUE = 1\n')

    def test_isolated_bridge_rechecks_grants_and_does_not_echo_secrets(self):
        token = self.grant()
        env = dict(os.environ, AIKYA_HOST_KEY=self.key.hex())
        request = dict(schema=1, id='write-1', project=str(self.root), operation='write',
                       arguments=dict(session='session-a', intent=self.args, grant=token))
        result = subprocess.run([sys.executable, '-I', '-B', '-m', 'aikya.services.bridge', '--root', str(self.root)],
                                input=json.dumps(request), text=True, capture_output=True, env=env, timeout=10)
        response = json.loads(result.stdout)
        self.assertTrue(response['ok'], response)
        self.assertNotIn(self.key.hex(), result.stdout); self.assertNotIn(token, result.stdout)
        self.assertEqual((self.root / 'value.py').read_text(), 'VALUE = 2\n')


if __name__ == '__main__': unittest.main()
