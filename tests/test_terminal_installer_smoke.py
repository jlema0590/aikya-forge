"""The native smoke observes process results and never adopts existing user data."""
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from aikya.installation.managed_runtime import host_platform


@unittest.skipIf(os.name=='nt','Controlled shell process fixtures require POSIX')
class TerminalInstallerSmokeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.ci.terminal_installer_smoke'),'Native installer smoke is absent')
        self.smoke=importlib.import_module('scripts.ci.terminal_installer_smoke')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.assets=self.root/'assets';self.assets.mkdir()

    def assets_for(self,*,exit_code=0,doctor=True):
        script='''#!/bin/sh
set -eu
case " $* " in *' --dry-run '*) echo '{"writes":false,"network":false}'; exit 0;; esac
'''
        if exit_code:script+=f'exit {exit_code}\n'
        else:
            script+='''
app="$AIKYA_INSTALL_ROOT"
if [ -f "$app/terminal/current.json" ]; then echo '{"status":"up-to-date"}'; exit 0; fi
mkdir -p "$app/bin" "$app/terminal"
printf '{}' > "$app/terminal/current.json"
cat > "$app/bin/aikya" <<'COMMAND'
#!/bin/sh
echo 'Aikya Forge help'
COMMAND
cat > "$app/bin/aikya-manage" <<'COMMAND'
#!/bin/sh
case "$1" in
doctor) echo '{"installed":DOCTOR,"pending":false,"errors":[]}';;
uninstall) rm "$AIKYA_INSTALL_ROOT/terminal/current.json" "$AIKYA_INSTALL_ROOT/bin/aikya" "$AIKYA_INSTALL_ROOT/bin/aikya-manage"; echo '{"status":"uninstalled"}';;
esac
COMMAND
chmod +x "$app/bin/aikya" "$app/bin/aikya-manage"
echo '{"status":"installed"}'
'''.replace('DOCTOR','true' if doctor else 'false')
        name='aikya-terminal-0.1.0-'+host_platform()+'.tar.gz'
        files={'install.sh':script.encode(),name:b'Controlled transport; the fixture entry does not execute it.'}
        record=dict(version='0.1.0',platforms={host_platform():dict(asset=name,sha256=hashlib.sha256(files[name]).hexdigest())},entries={'install.sh':hashlib.sha256(files['install.sh']).hexdigest()})
        files['terminal-bootstrap.json']=json.dumps(record).encode()
        for name,raw in files.items():(self.assets/name).write_bytes(raw)
        (self.assets/'SHA256SUMS').write_text(''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,raw in files.items()))

    def test_install_reinstall_doctor_and_uninstall_are_observed_without_erasing_owner_data(self):
        self.assets_for();target=self.root/'smoke Forge á with spaces'
        result=self.smoke.run(self.assets,target)
        self.assertEqual(result['status'],'passed')
        self.assertEqual(result['steps'],['preview','install','help','doctor','reinstall','uninstall'])
        self.assertFalse((target/'application/terminal/current.json').exists())
        self.assertEqual((target/'application/owner-data.txt').read_text(),'Preserve owner data.\n')
        self.assertEqual(list((target/'project').iterdir()),[])

    def test_failed_install_and_false_doctor_status_never_report_success(self):
        for status in ('install','doctor'):
            self.assets_for(exit_code=17 if status=='install' else 0,doctor=status!='doctor')
            target=self.root/status
            with self.subTest(status=status),self.assertRaisesRegex(ValueError,status):self.smoke.run(self.assets,target)
            self.assertTrue((target/'logs').is_dir())

    def test_existing_output_and_corrupt_assets_are_preserved_before_execution(self):
        self.assets_for();target=self.root/'existing';target.mkdir();custom=target/'custom';custom.write_text('Keep me')
        with self.assertRaises(ValueError):self.smoke.run(self.assets,target)
        self.assertEqual(custom.read_text(),'Keep me')
        (self.assets/'install.sh').write_text('exit 0\n')
        fresh=self.root/'fresh'
        with self.assertRaisesRegex(ValueError,'checksum|integrity'):self.smoke.run(self.assets,fresh)
        self.assertFalse(fresh.exists())


if __name__=='__main__':unittest.main()
