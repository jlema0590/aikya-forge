"""Native preflight consumes inspection metadata without inventing top-level fields."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation import managed_probe


class NativeToolProbe(unittest.TestCase):
    def test_inspection_result_probes_both_tools_before_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();runtime=root/'runtime';runtime.mkdir()
            for name in ('fd','rg'):
                p=root/'tools'/name/(name+('.exe' if os.name=='nt' else ''));p.parent.mkdir(parents=True);p.write_bytes(b'Inert probe fixture')
            inspected=dict(version='0.2.0',runtime=str(runtime),python=str(root/'python'),node=str(root/'node'),
                manifest={'platform':'win32-x64' if os.name=='nt' else 'darwin-arm64'})
            outputs=['0.2.0\n','Aikya Forge read-only help\n','fd 10.5.2\n','ripgrep 15.2.0 (rev e89fff89ac)\n']
            observed=[]
            def execute(command,**kwargs):
                observed.append(command[0]);return subprocess.CompletedProcess(command,0,stdout=outputs.pop(0),stderr='')
            with patch.object(managed_probe.subprocess,'run',side_effect=execute):
                self.assertEqual(managed_probe.check(inspected,root/'home'),{'status':'passed'})
            self.assertEqual(len(observed),4);self.assertEqual(outputs,[])


if __name__=='__main__':unittest.main()
