"""Durable replacement survives bounded Windows sharing conflicts, never replays work."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.storage import atomic_write


class AtomicStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.json';self.path.write_text('previous')

    def conflict(self,code):
        error=PermissionError(13,'Windows sharing conflict');error.winerror=code
        return error

    def assert_clean(self):
        self.assertEqual(sorted(p.name for p in self.path.parent.iterdir()),['state.json'])

    def test_transient_windows_sharing_conflict_replaces_only_the_prepared_bytes(self):
        replace=os.replace;attempts=[]
        def transient(source,destination):
            attempts.append(Path(source).read_bytes())
            if len(attempts)<3:
                self.assertEqual(self.path.read_text(),'previous')
                raise self.conflict(32)
            return replace(source,destination)
        with patch('aikya.storage.os.replace',side_effect=transient):atomic_write(self.path,'next')
        self.assertEqual(attempts,[b'next']*3);self.assertEqual(self.path.read_text(),'next');self.assert_clean()

    def test_persistent_windows_denial_is_bounded_preserves_previous_and_removes_temporary_file(self):
        failure=self.conflict(5);clock=[0.0]
        def advance(seconds):clock[0]+=seconds
        with patch('aikya.storage.time.monotonic',side_effect=lambda:clock[0]),patch('aikya.storage.time.sleep',side_effect=advance),patch('aikya.storage.os.replace',side_effect=failure) as replace:
            with self.assertRaises(PermissionError) as result:atomic_write(self.path,'next')
        self.assertIs(result.exception,failure);self.assertGreater(replace.call_count,1)
        self.assertLessEqual(replace.call_count,27);self.assertEqual(clock[0],.25)
        self.assertEqual(self.path.read_text(),'previous');self.assert_clean()

    def test_destination_redirected_during_conflict_is_refused_before_the_next_replace(self):
        other=self.path.parent/'user.txt';other.write_text('user content')
        probe=self.path.parent/'probe'
        try:probe.symlink_to(other)
        except OSError:self.skipTest('Symlink creation is unavailable')
        probe.unlink()
        def redirect(source,destination):
            self.path.unlink();self.path.symlink_to(other)
            raise self.conflict(33)
        with patch('aikya.storage.os.replace',side_effect=redirect) as replace:
            with self.assertRaises(ValueError):atomic_write(self.path,'next')
            self.assertEqual(replace.call_count,1)
        self.assertTrue(self.path.is_symlink());self.assertEqual(other.read_text(),'user content')
        self.assertEqual(sorted(p.name for p in self.path.parent.iterdir()),['state.json','user.txt'])

    def test_other_filesystem_failures_are_not_retried(self):
        for failure in [PermissionError(13,'Not a Windows sharing violation'),OSError(28,'No space')]:
            with self.subTest(type=type(failure).__name__),patch('aikya.storage.os.replace',side_effect=failure) as replace:
                with self.assertRaises(OSError):atomic_write(self.path,'next')
                self.assertEqual(replace.call_count,1)
            self.assertEqual(self.path.read_text(),'previous');self.assert_clean()

    @unittest.skipUnless(os.name=='nt','Requires actual Windows open-file replacement semantics')
    def test_actual_windows_reader_can_close_before_durable_replacement(self):
        descriptor=os.open(self.path,os.O_RDONLY);replace=os.replace;conflicts=[]
        def native_replace(source,destination):
            try:return replace(source,destination)
            except OSError as error:
                if not conflicts:os.close(descriptor)
                conflicts.append(getattr(error,'winerror',None))
                raise
        try:
            with patch('aikya.storage.os.replace',side_effect=native_replace):atomic_write(self.path,'next')
        finally:
            if not conflicts:os.close(descriptor)
        self.assertTrue(conflicts);self.assertIn(conflicts[0],(5,32,33))
        self.assertEqual(self.path.read_text(),'next');self.assert_clean()


if __name__=='__main__':unittest.main()
