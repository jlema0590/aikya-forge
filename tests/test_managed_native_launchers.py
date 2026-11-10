"""Native executable wrappers bind one owned root and interpreter without a shell parser."""
import io
from pathlib import Path,PureWindowsPath
import tempfile
import unittest
import zipfile
from aikya.installation import managed_launchers


class NativeLauncherTests(unittest.TestCase):
    def test_owned_windows_manager_stays_bound_to_retained_bootstrap_during_updates(self):
        before={name:dict(before=None,after=managed_launchers._encode(b'Owned original manager')) for name in ('aikya.exe','aikya-manage.exe','aikya-setup.exe')}
        after={name:b'New interpreter binding' for name in before}
        result=managed_launchers.intended(before,after,retain_manager=True)
        self.assertEqual(result['aikya-manage.exe']['after'],before['aikya-manage.exe']['after'])
        self.assertEqual(managed_launchers._decode(result['aikya.exe']['after']),after['aikya.exe'])

    def test_windows_architectures_have_deterministic_exe_containers_and_literal_paths(self):
        self.assertTrue(callable(getattr(managed_launchers,'windows_contents',None)),'Native Windows command containers are absent')
        root=PureWindowsPath('C:/Users/Aikya user/áikya & tools');python=root/'terminal/versions'/(64*'a')/'python/python.exe'
        for target in ('win32-x64','win32-arm64'):
            with self.subTest(target=target):
                result=managed_launchers.windows_contents(root,python,target)
                self.assertEqual(set(result),{'aikya.exe','aikya-manage.exe','aikya-setup.exe'})
                self.assertEqual(result,managed_launchers.windows_contents(root,python,target))
                for name,raw in result.items():
                    self.assertTrue(raw.startswith(b'MZ'))
                    self.assertIn(('#!"'+str(python)+'" -I -B\n').encode(),raw)
                    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                        code=archive.read('__main__.py').decode();self.assertIn(repr(str(root)),code);compile(code,name,'exec')


if __name__=='__main__':unittest.main()
