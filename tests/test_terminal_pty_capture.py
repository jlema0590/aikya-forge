"""Real PTY I/O is bounded and only its owned child is terminated on failure."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class TerminalPtyCapture(unittest.TestCase):
    def setUp(self):
        path=ROOT/'scripts/ci/terminal_pty_acceptance.py';self.assertTrue(path.is_file(),'Native PTY acceptance is absent')
        spec=importlib.util.spec_from_file_location('pty_acceptance',path);self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def child(self,code,**kwargs):
        return self.module.ConsoleCapture([sys.executable,'-I','-u','-c',code],self.root,dict(os.environ),**kwargs)

    def test_real_terminal_input_and_resize_are_observed(self):
        code='import os,sys;assert sys.stdin.isatty() and sys.stdout.isatty();print("READY",flush=True);input();print("SIZE",os.get_terminal_size(0).columns,flush=True)'
        with self.child(code) as terminal:
            terminal.expect('READY',timeout=3)
            terminal.resize(100,32);terminal.send('size\r');terminal.expect('SIZE 100',timeout=3)
            self.assertEqual(terminal.finish(timeout=3),0)
        self.assertIsNone(terminal.pid)

    def test_excess_output_and_timeout_do_not_leave_the_child_running(self):
        for code,limit,exception in [('import os,time;os.write(1,b"x"*4096);time.sleep(10)',512,ValueError),('import time;time.sleep(10)',65536,TimeoutError)]:
            with self.subTest(limit=limit):
                with self.assertRaises(exception):
                    with self.child(code,max_bytes=limit) as terminal:terminal.expect('NEVER',timeout=.2)
                self.assertIsNone(terminal.pid)

    def test_ansi_normalization_preserves_text_without_turning_titles_into_content(self):
        raw=b'\x1b]0;private title\x07\x1b[31mREADY\x1b[0m\r\n'
        self.assertEqual(self.module.plain(raw),'READY\r\n')


if __name__=='__main__':unittest.main()
