import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from aikya.services import acceptance
from aikya.review.contracts import digest
class InstalledObservationIdentity(unittest.TestCase):
 def test_verified_resolver_public_contract_supplies_runtime_identity(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();provenance=dict(core={'source':{'files':{'src/core.py':'a'*64}}},runtime={'files':{'src/runtime.ts':'b'*64}})
   raw=json.dumps(provenance).encode();manifest=json.dumps({'files':{'provenance.json':{'sha256':hashlib.sha256(raw).hexdigest()}}}).encode();identity=hashlib.sha256(manifest).hexdigest()
   payload=root/'terminal/versions'/identity;(payload/'runtime').mkdir(parents=True);(payload/'manifest.json').write_bytes(manifest);(payload/'provenance.json').write_bytes(raw)
   current=dict(root=str(root),python=sys.executable,runtime=str(payload/'runtime'),version='0.2.0',manifest_hash=identity)
   with patch.object(acceptance.managed_runtime,'resolve',return_value=current):
    self.assertEqual(acceptance._runtime(),('0.2.0',digest(dict(core=provenance['core']['source']['files'],runtime=provenance['runtime']['files']))))
    (payload/'provenance.json').write_bytes(b'Changed provenance')
    self.assertEqual(acceptance._runtime(),(None,None))
if __name__=='__main__':unittest.main()
