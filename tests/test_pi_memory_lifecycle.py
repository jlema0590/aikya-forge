"""Pi lifecycle reuses the project observer and does not start a model or second store."""
import json
import hashlib
from pathlib import Path
import tempfile
import time
import threading
import unittest
from unittest.mock import patch
from aikya.code_index.policy import configure
from aikya.services import maintenance
from test_memory_integration import completed_observers


class PiMemoryLifecycleTests(unittest.TestCase):
    def test_session_end_waits_for_a_concurrent_observer_lease_read(self):
        from aikya.code_index import hooks
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();configure(root,approved=True)
            path=root/hooks.LEASES;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({hashlib.sha256(b'author').hexdigest():time.time()}))
            reading=threading.Event();release=threading.Event();writing=threading.Event();done=threading.Event()
            errors=[];observed=[];read=hooks.read_source

            def held_read(project,relative,limit):
                if relative==hooks.LEASES and threading.current_thread().name=='lease-reader':
                    # A real open file denies replacement on Windows. Readers and
                    # writers must coordinate rather than drop a failed SessionEnd.
                    with path.open('rb'):
                        reading.set()
                        if not release.wait(2):raise AssertionError('Reader barrier not released')
                        return read(project,relative,limit)
                return read(project,relative,limit)

            def reader():
                try:observed.append(hooks.active_sessions(root))
                except Exception as error:errors.append(error)

            def writer():
                writing.set()
                try:maintenance.session_event(root,'author','end')
                except Exception as error:errors.append(error)
                finally:done.set()

            with patch.object(hooks,'read_source',side_effect=held_read):
                first=threading.Thread(target=reader,name='lease-reader');second=threading.Thread(target=writer)
                first.start()
                try:
                    self.assertTrue(reading.wait(1))
                    second.start();self.assertTrue(writing.wait(1))
                    self.assertFalse(done.wait(.2),'SessionEnd replaced leases during an active observer read')
                finally:
                    release.set();first.join(3)
                    if second.ident is not None:second.join(3)
            self.assertFalse(first.is_alive());self.assertFalse(second.is_alive())
            self.assertEqual(errors,[]);self.assertEqual(observed,[True])
            self.assertEqual(json.loads(path.read_text()),{})

    def test_disabled_observation_and_unknown_events_have_no_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            self.assertEqual(maintenance.session_event(root,'pi-session','start')['status'],'disabled')
            with self.assertRaises(ValueError):maintenance.session_event(root,'pi-session','run_shell')
            self.assertEqual(list(root.iterdir()),[])

    def test_external_changes_refresh_html_until_the_final_owned_session_closes(self):
        with tempfile.TemporaryDirectory() as folder,completed_observers() as wait_for_exit:
            root=Path(folder).resolve();configure(root,approved=True)
            (root/'entity.py').write_text('class OriginalEntity: pass\n')
            path=root/'aikya/docs/memory/view/index.html'
            try:
                maintenance.session_event(root,'pi-author','start')
                maintenance.session_event(root,'pi-second','start')
                deadline=time.monotonic()+10
                while not path.exists() and time.monotonic()<deadline:time.sleep(.05)
                self.assertTrue(path.exists())
                maintenance.session_event(root,'pi-author','end')
                (root/'entity.py').write_text('class ExternallyEditedEntity: pass\n')
                deadline=time.monotonic()+10;html=''
                while time.monotonic()<deadline:
                    try:html=path.read_text(encoding='utf8')
                    except (PermissionError,FileNotFoundError):pass
                    if 'ExternallyEditedEntity' in html:break
                    time.sleep(.05)
                self.assertIn('ExternallyEditedEntity',html)
            finally:
                maintenance.session_event(root,'pi-author','end')
                maintenance.session_event(root,'pi-second','end')
                wait_for_exit()
                status=root/'.harness/state/memory-view/status.json'
                self.assertEqual(json.loads(status.read_text(encoding='utf8'))['state'],'Stopped')


if __name__=='__main__':unittest.main()
