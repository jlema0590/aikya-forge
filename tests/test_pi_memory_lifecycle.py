"""Pi lifecycle reuses the project observer and does not start a model or second store."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from aikya.code_index.policy import configure
from aikya.services import maintenance
from test_memory_integration import completed_observers


class PiMemoryLifecycleTests(unittest.TestCase):
    def test_disabled_observation_and_unknown_events_have_no_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            self.assertEqual(maintenance.session_event(root,'pi-session','start')['status'],'disabled')
            with self.assertRaises(ValueError):maintenance.session_event(root,'pi-session','run_shell')
            self.assertEqual(list(root.iterdir()),[])

    def test_external_changes_refresh_html_until_the_final_owned_session_closes(self):
        with tempfile.TemporaryDirectory() as folder,completed_observers():
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
                deadline=time.monotonic()+10
                while 'ExternallyEditedEntity' not in path.read_text() and time.monotonic()<deadline:time.sleep(.05)
                self.assertIn('ExternallyEditedEntity',path.read_text())
            finally:
                maintenance.session_event(root,'pi-author','end')
                maintenance.session_event(root,'pi-second','end')
                status=root/'.harness/state/memory-view/status.json';deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    if status.exists() and json.loads(status.read_text()).get('state')=='Stopped':break
                    time.sleep(.05)
                self.assertEqual(json.loads(status.read_text())['state'],'Stopped')


if __name__=='__main__':unittest.main()
