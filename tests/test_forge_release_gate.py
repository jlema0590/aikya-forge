"""Public release cannot mistake local observations or stale code for accepted external trials."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
CHECKS=('positive_budget','exhaustion','unknown_usage','cancellation','compaction','resumption','independent_review','quota_provenance','comparative_trials')


class ForgeReleaseGateTests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'scripts/ci/forge_release_gate.py';self.assertTrue(path.is_file(),'Forge external release gate is absent')
        spec=importlib.util.spec_from_file_location('forge_release_gate',path);self.gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.gate)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        folder=self.root/'aikya/docs/validation';folder.mkdir(parents=True);self.paths=[]
        for number in (1,2,3):
            path=folder/('observation-'+str(number)+'.json')
            path.write_text(json.dumps(dict(schema=1,generated_by='aikya-provider-observation',runtime_version='0.2.0',
                runtime_fingerprint='f'*64,status='available',recorded_tokens=number*10,calls=number,uncertain_calls=0,
                groups_truncated=False,provider_verified=False)))
            self.paths.append(path.relative_to(self.root).as_posix())
        self.report=folder/'forge-provider-acceptance.json';self.value=dict(schema=1,version='0.2.0',runtime_fingerprint='f'*64,
            review_status='accepted',repetitions=3,cache_conditions='Fixed model/effort; three distinct controlled trials',
            checks={name:'passed' for name in CHECKS},observations=self.paths,review_note='Synthetic policy fixture; never a real-provider acceptance claim')
        self.write()

    def write(self):self.report.write_text(json.dumps(self.value))

    def validate(self):
        with patch.object(self.gate,'runtime_fingerprint',return_value='f'*64):return self.gate.validate(self.root,self.report,'0.2.0')

    def test_missing_or_pending_external_review_is_not_accepted(self):
        self.value['review_status']='pending';self.write()
        with self.assertRaises(ValueError):self.validate()
        self.report.unlink()
        with self.assertRaises(ValueError):self.validate()

    def test_distinct_current_observations_and_complete_review_are_required(self):
        result=self.validate();self.assertEqual(result['observation_count'],3);self.assertFalse(result['publishes'])
        self.value['runtime_fingerprint']='0'*64;self.write()
        with self.assertRaises(ValueError):self.validate()

    def test_unknown_usage_duplicates_and_omitted_scenarios_cannot_pass(self):
        path=self.root/self.paths[0];before=path.read_bytes();item=json.loads(before);item['status']='unknown_usage';item['recorded_tokens']=None;path.write_text(json.dumps(item))
        with self.assertRaises(ValueError):self.validate()
        path.write_bytes(before);second=self.root/self.paths[1];original_second=second.read_bytes();second.write_bytes(before)
        with self.assertRaises(ValueError):self.validate()
        second.write_bytes(original_second)
        self.value['checks']['compaction']='not_run';self.write()
        with self.assertRaises(ValueError):self.validate()

    def test_observation_paths_cannot_escape_the_validation_dossier(self):
        self.value['observations'][0]='../outside.json';self.write()
        with self.assertRaises(ValueError):self.validate()


if __name__=='__main__':unittest.main()
