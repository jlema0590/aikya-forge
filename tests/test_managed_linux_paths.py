"""Linux terminfo keeps legitimate case variants; portable packages remain strict."""
import copy
from pathlib import Path
import tempfile
import unittest
from aikya.core.package_paths import validate
from aikya.installation import managed_archives,managed_runtime
from managed_terminal_support import payload


class LinuxComponentPaths(unittest.TestCase):
    def test_case_sensitive_native_names_do_not_disable_other_path_guards(self):
        paths=['share/terminfo/P/P12','share/terminfo/p/p12']
        validate(paths,case_sensitive=True)
        with self.assertRaises(ValueError):validate(paths)
        for names in ([paths[0],paths[0]],['A','A/child'],['CON.txt'],['../escape'],['cafe\u0301.txt','caf\u00e9.txt']):
            with self.subTest(names=names),self.assertRaises(ValueError):validate(names,case_sensitive=True)

    def test_archive_planning_preserves_all_case_variants_only_when_explicit(self):
        rows=[dict(name='python/'+name,kind='file',size=1,mode=0o644,target=None,member=None)
              for name in ('share/terminfo/P/P12','share/terminfo/p/p12')]
        table,resolved=managed_archives._plan(rows,'python',case_sensitive=True)
        self.assertEqual(set(table),{'share/terminfo/P/P12','share/terminfo/p/p12'});self.assertEqual(set(resolved),set(table))
        with self.assertRaises(ValueError):managed_archives._plan(rows,'python')

    def test_only_linux_payload_manifests_allow_native_case_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            import json
            folder=Path(tmp).resolve()/'payload';payload(folder,'0.2.0');value=json.loads((folder/'manifest.json').read_bytes())
            exemplar=copy.deepcopy(next(iter(value['files'].values())))
            value['files'].update({'python/share/terminfo/P/P12':exemplar,'python/share/terminfo/p/p12':exemplar})
            value['platform']='linux-x64-gnu';managed_runtime._manifest(value,dict(version='0.2.0',platform=value['platform']))
            value['platform']='darwin-arm64'
            with self.assertRaises(ValueError):managed_runtime._manifest(value,dict(version='0.2.0',platform=value['platform']))


if __name__=='__main__':unittest.main()
