"""A new Forge installation must not adopt or mutate a previous Harness root."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation.bootstrap import options,state,user_path
from aikya.installation import managed_cli


class ForgeApplicationRoot(unittest.TestCase):
    def test_default_preview_uses_a_distinct_application_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp).resolve();legacy=home/'Library/Application Support/Aikya';legacy.mkdir(parents=True)
            marker=legacy/'current.json';marker.write_bytes(b'Unmodified existing Harness installation')
            env={'HOME':str(home),'USERPROFILE':str(home)}
            with patch.dict(os.environ,env),patch.dict(os.environ,{},clear=False),patch('aikya.installation.bootstrap.options.sys.platform','darwin'):
                # Explicit overrides are intentionally absent in this default-path check.
                with patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':''}):
                    output=io.StringIO()
                    with contextlib.redirect_stdout(output):code=managed_cli.main(['install'])
                    self.assertEqual(code,0)
                    self.assertEqual(json.loads(output.getvalue())['root'],str(home/'Library/Application Support/AikyaForge'))
                    self.assertFalse((home/'Library/Application Support/AikyaForge').exists())
            self.assertEqual(marker.read_bytes(),b'Unmodified existing Harness installation')

    def test_explicit_legacy_root_is_refused_before_native_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'owner.json').write_text(json.dumps(state.OWNER))
            (root/'current.json').write_text(json.dumps({'version':'7.2.2','environment':'legacy','python':'legacy'}))
            before={p.name:p.read_bytes() for p in root.iterdir()}
            with patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(root)}):
                with patch('aikya.installation.managed_releases.download.https_bytes',side_effect=AssertionError('No legacy discovery network')):
                    with contextlib.redirect_stderr(io.StringIO()):code=managed_cli.main(['install','--yes'])
            self.assertEqual(code,2);self.assertEqual({p.name:p.read_bytes() for p in root.iterdir()},before)

    @unittest.skipIf(os.name=='nt','POSIX profile; Windows registry ownership has separate contracts')
    def test_forge_path_entry_preserves_a_previous_harness_shell_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp).resolve();profile=home/'.zshrc'
            old=b'# >>> Aikya managed PATH >>>\nexport PATH=/old/harness:"$PATH"\n# <<< Aikya managed PATH <<<\n'
            profile.write_bytes(old)
            with patch.dict(os.environ,{'HOME':str(home),'SHELL':'/bin/zsh'}):
                root=home/'forge';root.mkdir()
                user_path.ensure_user_path(root/'bin',root=root)
                self.assertIn(old,profile.read_bytes())
                user_path.remove_user_path(root)
                self.assertEqual(profile.read_bytes(),old)


if __name__=='__main__':unittest.main()
