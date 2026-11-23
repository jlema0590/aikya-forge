"""Approved Pi writes update the existing local index and HTML without inference."""
from pathlib import Path
import os
import tempfile
import unittest
from aikya.services.authorization import issue,apply_write
from aikya.code_index.policy import configure
from aikya.code_index.store import IndexStore


class PiMemoryEventTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();(self.root/'source.py').write_text('class Before: pass\n')
        self.key=os.urandom(32);self.intent=dict(path='source.py',content='class After: pass\n')

    def test_approved_write_updates_index_and_owned_html_when_project_policy_enables_it(self):
        configure(self.root,approved=True,manage_ignore=False)
        result=apply_write(self.root,'author',self.intent,issue(self.root,'author',self.intent,self.key),self.key)
        self.assertEqual(result['memory']['status'],'updated')
        names={s['name'] for s in IndexStore(self.root).read_snapshot().symbols}
        self.assertIn('After',names);self.assertNotIn('Before',names)
        html=self.root/'aikya/docs/memory/view/index.html'
        self.assertIn('After',html.read_text())

    def test_custom_html_is_preserved_and_memory_failure_does_not_hide_successful_source_write(self):
        configure(self.root,approved=True,manage_ignore=False)
        html=self.root/'aikya/docs/memory/view/index.html';html.parent.mkdir(parents=True);html.write_text('USER HTML')
        result=apply_write(self.root,'author',self.intent,issue(self.root,'author',self.intent,self.key),self.key)
        self.assertEqual(result['status'],'written');self.assertEqual(result['memory']['status'],'degraded')
        self.assertEqual(html.read_text(),'USER HTML')
        self.assertEqual((self.root/'source.py').read_text(),'class After: pass\n')

    def test_disabled_memory_does_not_initialize_an_index_or_html(self):
        result=apply_write(self.root,'author',self.intent,issue(self.root,'author',self.intent,self.key),self.key)
        self.assertEqual(result['memory']['status'],'disabled')
        self.assertFalse((self.root/'.harness/state/code-index/index.sqlite').exists())
        self.assertFalse((self.root/'aikya/docs/memory').exists())


if __name__=='__main__':unittest.main()
