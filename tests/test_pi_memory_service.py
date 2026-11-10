"""Pi reads only reviewed, current project notes using the existing store."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from aikya.memory.knowledge import remember, propose
try: service = importlib.import_module('aikya.services.memory')
except ModuleNotFoundError: service = None


class MemoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(service, 'Pi memory service is absent')
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve(); (self.root/'source.py').write_text('class Source: pass\n')

    def test_uninitialized_memory_status_and_search_are_read_only(self):
        self.assertEqual(service.status(self.root)['status'],'not_initialized')
        self.assertEqual(service.search(self.root,'decision',512)['notes'],[])
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['source.py'])

    def test_only_current_reviewed_notes_cross_the_bridge(self):
        raw=dict(kind='project',source='source.py',text='Decision: use a repository abstraction',ttl_days=30)
        remember(self.root,raw,approved=True)
        propose(self.root,{**raw,'text':'Decision: UNREVIEWED_SECRET'})
        result=service.search(self.root,'Decision',1000)
        self.assertEqual(len(result['notes']),1)
        self.assertIn('repository abstraction',result['notes'][0]['text'])
        self.assertNotIn('UNREVIEWED_SECRET',json.dumps(result))
        (self.root/'source.py').write_text('class Changed: pass\n')
        self.assertEqual(service.search(self.root,'Decision',1000)['notes'],[])
        self.assertGreater(service.status(self.root)['stale_notes'],0)

    def test_packet_is_bounded_and_does_not_search_another_project(self):
        remember(self.root,dict(kind='project',source='source.py',text='Decision '+('source ' * 1000),ttl_days=30),approved=True)
        result=service.search(self.root,'Decision',512)
        self.assertLessEqual(len(json.dumps(result,ensure_ascii=True)),512)
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(service.search(Path(other).resolve(),'Decision',1000)['notes'],[])
        for query,budget in [('x',100000),('x'*1001,1000)]:
            with self.assertRaises(ValueError): service.search(self.root,query,budget)


if __name__=='__main__': unittest.main()
