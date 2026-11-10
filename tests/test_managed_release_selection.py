"""Stable and preview resolution must never silently share a prerelease channel."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class NativeReleaseTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.managed_releases'),'Native release channel selection is absent')
        self.releases=importlib.import_module('aikya.installation.managed_releases');self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()

    def test_stable_excludes_preview_drafts_and_invalid_release_identities(self):
        records=[dict(tag_name='v'+version,draft=draft,prerelease=preview,published_at='2026-11-09T00:00:00Z') for version,draft,preview in [('8.0.0',False,False),('8.1.0-alpha.1',False,True),('8.1.0',True,False),('8.00.1',False,False),('7.2.2',False,False)]]
        with patch.object(self.releases.download,'https_bytes',return_value=json.dumps(records).encode()):
            self.assertEqual(self.releases.resolve(channel='stable'),'8.0.0');self.assertEqual(self.releases.resolve(channel='preview'),'8.1.0-alpha.1')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_offline_explicit_versions_never_resolve_latest_or_relax_channel(self):
        with patch.object(self.releases.download,'https_bytes',side_effect=AssertionError('Network forbidden')):
            self.assertEqual(self.releases.resolve('8.0.0-alpha.1',channel='preview',offline=True),'8.0.0-alpha.1')
            for version,channel in [(None,'stable'),('latest','preview'),('8.0.0-alpha.0','stable'),('8.0.0+custom','preview')]:
                with self.subTest(version=version,channel=channel):
                    with self.assertRaises(ValueError):self.releases.resolve(version,channel=channel,offline=True)

    def test_offline_bundle_integrity_is_checked_before_any_staging_writes(self):
        name='aikya-terminal-8.0.0-alpha.0-darwin-arm64.zip';raw=b'Exact pinned artifact fixture';(self.root/name).write_bytes(raw)
        (self.root/'SHA256SUMS').write_text(hashlib.sha256(raw).hexdigest()+'  '+name+'\n')
        self.assertEqual(self.releases.artifact('8.0.0-alpha.0','darwin-arm64',offline_dir=self.root),raw)
        (self.root/name).write_bytes(b'Corruption')
        with self.assertRaises(ValueError):self.releases.artifact('8.0.0-alpha.0','darwin-arm64',offline_dir=self.root)
        self.assertEqual((self.root/name).read_bytes(),b'Corruption');self.assertEqual(len(list(self.root.iterdir())),2)


if __name__=='__main__':unittest.main()
