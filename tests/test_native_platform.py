"""Musl detection must inspect the active interpreter, never execute a PATH helper."""
import importlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch


def elf(loader):
    value=bytearray(256);value[:6]=b'\x7fELF\x02\x01'
    struct.pack_into('<Q',value,32,64);struct.pack_into('<H',value,54,56);struct.pack_into('<H',value,56,1)
    struct.pack_into('<I',value,64,3);struct.pack_into('<Q',value,72,128)
    raw=loader.encode()+b'\0';struct.pack_into('<Q',value,96,len(raw));value[128:128+len(raw)]=raw
    return value


class NativeLibcTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.native_platform'),'Safe native libc detection is absent')
        self.native=importlib.import_module('aikya.installation.native_platform')

    def test_musl_elf_loader_is_detected_without_running_ldd(self):
        with tempfile.TemporaryDirectory() as tmp:
            python=Path(tmp)/'python';python.write_bytes(elf('/lib/ld-musl-x86_64.so.1'))
            with patch.object(self.native.platform,'libc_ver',return_value=('','')),patch.object(self.native.sys,'executable',str(python)),\
                 patch('subprocess.run',side_effect=AssertionError('No external detection command')):
                self.assertEqual(self.native.linux_runtime(),'musl')

    def test_unknown_or_malformed_loaders_are_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            python=Path(tmp)/'python'
            for value in (b'Not ELF',elf('/project/ld-musl-x86_64.so.1'),elf('/lib/unknown.so')):
                python.write_bytes(value)
                with patch.object(self.native.platform,'libc_ver',return_value=('','')),patch.object(self.native.sys,'executable',str(python)):
                    self.assertEqual(self.native.linux_runtime(),'unknown')

    def test_static_python_requires_positive_system_loader_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            python=Path(tmp)/'python';value=elf('/lib/ignored');struct.pack_into('<I',value,64,1);python.write_bytes(value)
            with patch.object(self.native.platform,'libc_ver',return_value=('','')),patch.object(self.native.sys,'executable',str(python)):
                with patch.object(self.native,'_system_musl',return_value=True):self.assertEqual(self.native.linux_runtime(),'musl')
                with patch.object(self.native,'_system_musl',return_value=False):self.assertEqual(self.native.linux_runtime(),'unknown')

    def test_reported_glibc_keeps_its_existing_native_selection(self):
        with patch.object(self.native.platform,'libc_ver',return_value=('glibc','2.28')):
            self.assertEqual(self.native.linux_runtime(),'glibc')

    def test_realistic_musl_loader_string_can_live_beyond_the_first_64k(self):
        with tempfile.TemporaryDirectory() as tmp:
            python=Path(tmp)/'python';value=elf('/lib/ignored')
            location=70000;loader=b'/lib/ld-musl-x86_64.so.1\0';value.extend(b'\0'*(location+len(loader)-len(value)))
            struct.pack_into('<Q',value,72,location);struct.pack_into('<Q',value,96,len(loader));value[location:]=loader;python.write_bytes(value)
            with patch.object(self.native.platform,'libc_ver',return_value=('libc','')),patch.object(self.native.sys,'executable',str(python)):
                self.assertEqual(self.native.linux_runtime(),'musl')
            struct.pack_into('<Q',value,72,len(value)+1000);python.write_bytes(value)
            with patch.object(self.native.platform,'libc_ver',return_value=('libc','')),patch.object(self.native.sys,'executable',str(python)):
                self.assertEqual(self.native.linux_runtime(),'unknown')


if __name__=='__main__':unittest.main()
