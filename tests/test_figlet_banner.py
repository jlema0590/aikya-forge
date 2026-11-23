"""Real FIGlet output stays local, bounded and optional for dependency-free core users."""
import importlib
import unittest
from unittest.mock import patch


class FigletBannerTests(unittest.TestCase):
    def module(self):
        spec=importlib.util.find_spec('aikya.presentation')
        self.assertIsNotNone(spec,'Python banner presentation is absent')
        return importlib.import_module('aikya.presentation.banner')

    @unittest.skipUnless(importlib.util.find_spec('pyfiglet'),'Optional terminal extra is not installed')
    def test_real_pyfiglet_renders_single_word_variants_without_project_state(self):
        module=self.module();value=module.banner()
        self.assertEqual(value['generator'],'pyfiglet');self.assertEqual(value['version'],'1.0.4')
        self.assertEqual([v['font'] for v in value['variants']],['slant','small'])
        for variant in value['variants']:
            self.assertTrue(3<=len(variant['lines'])<=8)
            self.assertTrue(all(len(line)<=80 and all(32<=ord(c)<=126 for c in line) for line in variant['lines']))
        from pyfiglet import Figlet
        self.assertEqual(value['variants'][0]['lines'],[s.rstrip() for s in Figlet(font='slant',width=200).renderText('Aikya').splitlines()])

    def test_missing_optional_dependency_retains_plain_identity(self):
        module=self.module()
        with patch.dict('sys.modules',{'pyfiglet':None}):value=module.banner()
        self.assertEqual(value['generator'],'plain');self.assertEqual(value['variants'],[])

    @unittest.skipUnless(importlib.util.find_spec('pyfiglet'),'Optional terminal extra is not installed')
    def test_fresh_windows_import_without_appdata_renders_and_restores_environment(self):
        import subprocess,sys,json
        script=('import os,sys,json;from aikya.presentation.banner import banner;'
                'os.environ.pop("APPDATA",None);sys.platform="win32";'
                'v=banner();assert "APPDATA" not in os.environ;print(json.dumps(v))')
        result=subprocess.run([sys.executable,'-I','-B','-c',script],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['generator'],'pyfiglet')

    @unittest.skipUnless(importlib.util.find_spec('pyfiglet'),'Optional terminal extra is not installed')
    def test_bundled_fonts_do_not_read_project_font_files(self):
        import tempfile,subprocess,sys,json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve();font=folder/'slant.flf';font.write_text('Not a FIGlet font')
            result=subprocess.run([sys.executable,'-I','-B','-m','aikya.presentation.banner'],cwd=folder,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['generator'],'pyfiglet')
            self.assertEqual(font.read_text(),'Not a FIGlet font')

    def test_native_font_input_is_pinned_and_corruption_is_refused_before_staging(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_figlet'),'Native figlet inputs are absent')
        native=importlib.import_module('aikya.installation.managed_figlet')
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve();recipe=native.load()
            (folder/recipe['file']).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):native.prepare(folder)
            self.assertEqual(sorted(p.name for p in folder.iterdir()),[recipe['file']])


if __name__=='__main__':unittest.main()
