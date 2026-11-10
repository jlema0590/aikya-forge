"""Forge release reset remains usable by the native release/build consumers."""
import json
import unittest
from unittest.mock import patch
from aikya.installation import managed_versions,managed_releases


class ForgeVersionTests(unittest.TestCase):
    def test_forge_version_normalizes_and_orders_for_native_packages(self):
        self.assertEqual(managed_versions.python_version('0.1.0'),'0.1.0')
        self.assertEqual(managed_versions.python_version('0.2.0-alpha.1'),'0.2.0a1')
        self.assertLess(managed_versions.order('0.2.0-alpha.1'),managed_versions.order('0.2.0'))
        for version in ('0.01.0','0.1.0-alpha.01','0.1.0+local','7.2.2'):
            with self.subTest(version=version),self.assertRaises(ValueError):managed_versions.parts(version)

    def test_forge_release_catalog_selects_stable_and_preview_from_zero(self):
        records=[dict(tag_name='v'+v,draft=False,prerelease=preview,published_at='2026-11-10T00:00:00Z')
                 for v,preview in [('0.1.0',False),('0.2.0-alpha.1',True),('7.2.2',False)]]
        def transport(url,limit):
            if url!='https://api.github.com/repos/jlema0590/aikya-forge/releases?per_page=100':
                raise AssertionError('Update lookup left the Forge repository')
            return json.dumps(records).encode()
        with patch.object(managed_releases.download,'https_bytes',side_effect=transport):
            self.assertEqual(managed_releases.resolve(channel='stable'),'0.1.0')
            self.assertEqual(managed_releases.resolve(channel='preview'),'0.2.0-alpha.1')


if __name__=='__main__':unittest.main()
