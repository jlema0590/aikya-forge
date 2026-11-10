"""Bounded verified runtime archives materialize data, never imported archive code."""
from pathlib import Path
import hashlib,importlib,importlib.util,io,tarfile,tempfile,unittest,zipfile


class ComponentArchiveTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_archives'),'Managed component archive inspection is absent')
        self.archives=importlib.import_module('aikya.installation.managed_archives')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def tar(self,rows):
        target=self.root/'component.tar.gz'
        with tarfile.open(target,'w:gz') as arc:
            for name,kind,data in rows:
                member=tarfile.TarInfo(name);member.mode=0o755 if name.endswith('/python3') else 0o644
                if kind=='file':member.size=len(data);arc.addfile(member,io.BytesIO(data))
                else:member.type=tarfile.SYMTYPE if kind=='link' else tarfile.DIRTYPE;member.linkname=data;arc.addfile(member)
        return target,hashlib.sha256(target.read_bytes()).hexdigest()

    def test_contained_file_links_become_independent_regular_files_without_execution(self):
        path,digest=self.tar([('python/bin/python3','file',b'NOT EXECUTED'),('python/bin/python','link','python3'),('python/LICENSE','file',b'License')])
        destination=self.root/'result';result=self.archives.extract(path,destination,digest,'python')
        self.assertEqual((destination/'bin/python').read_bytes(),b'NOT EXECUTED');self.assertFalse((destination/'bin/python').is_symlink())
        self.assertEqual((destination/'bin/python3').read_bytes(),b'NOT EXECUTED');self.assertEqual(result['files'],3)

    def test_zip_component_prefix_is_selected_and_original_file_bytes_are_preserved(self):
        path=self.root/'component.zip'
        with zipfile.ZipFile(path,'w') as arc:arc.writestr('node/bin/node.exe',b'NODE FIXTURE');arc.writestr('node/LICENSE',b'License')
        self.archives.extract(path,self.root/'result',hashlib.sha256(path.read_bytes()).hexdigest(),'node')
        self.assertEqual((self.root/'result/bin/node.exe').read_bytes(),b'NODE FIXTURE')

    def test_root_wheel_data_can_merge_into_owned_staging_without_overwriting_existing_files(self):
        path=self.root/'core.whl'
        with zipfile.ZipFile(path,'w') as arc:arc.writestr('aikya/__init__.py',b'# Core');arc.writestr('metadata.txt',b'Core metadata')
        destination=self.root/'site-packages';destination.mkdir();existing=destination/'existing.txt';existing.write_text('Preserved dependency')
        self.archives.extract(path,destination,hashlib.sha256(path.read_bytes()).hexdigest(),'.',merge=True)
        self.assertEqual(existing.read_text(),'Preserved dependency');self.assertEqual((destination/'aikya/__init__.py').read_bytes(),b'# Core')
        before={p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()}
        with self.assertRaises(ValueError):self.archives.extract(path,destination,hashlib.sha256(path.read_bytes()).hexdigest(),'.',merge=True)
        self.assertEqual({p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()},before)

    def test_bad_checksum_does_not_create_a_destination(self):
        path,digest=self.tar([('python/bin/python3','file',b'Raw')])
        with self.assertRaises(ValueError):self.archives.extract(path,self.root/'result','0'*64,'python')
        self.assertFalse((self.root/'result').exists())

    def test_escape_links_cycles_or_unknown_prefixes_are_refused_before_effects(self):
        for rows in [[('python/escape','link','../../outside')],[('python/a','link','b'),('python/b','link','a')],
                     [('outside/file','file',b'Foreign')],[('python/../escape','file',b'Escaped')]]:
            with self.subTest(rows=rows):
                path,digest=self.tar(rows)
                with self.assertRaises(ValueError):self.archives.extract(path,self.root/'result',digest,'python')
                self.assertFalse((self.root/'result').exists())

    def test_case_aliases_devices_and_file_parent_collisions_are_refused(self):
        for names in [('pkg/A/file','pkg/a/other'),('pkg/CON.txt',),('pkg/a','pkg/a/b'),('pkg/'+'字'*100+'.txt',)]:
            with self.subTest(names=names):
                path,digest=self.tar([(name,'file',b'Data') for name in names])
                with self.assertRaises(ValueError):self.archives.extract(path,self.root/'result',digest,'pkg')
                self.assertFalse((self.root/'result').exists())

    def test_preexisting_output_remains_untouched(self):
        path,digest=self.tar([('python/bin/python3','file',b'Raw')]);destination=self.root/'result';destination.mkdir()
        target=destination/'custom.txt';target.write_text('User data')
        with self.assertRaises(ValueError):self.archives.extract(path,destination,digest,'python')
        self.assertEqual(target.read_text(),'User data')

    def test_duplicate_tar_members_are_not_silently_overwritten(self):
        path,digest=self.tar([('python/a','file',b'First'),('python/a','file',b'Second')])
        with self.assertRaises(ValueError):self.archives.extract(path,self.root/'result',digest,'python')
        self.assertFalse((self.root/'result').exists())


if __name__=='__main__':unittest.main()
