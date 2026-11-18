"""Only bounded read-only component fetches retry transient transport failures."""
import importlib
import importlib.util
import ssl
import unittest
from unittest.mock import patch,call
from urllib.error import HTTPError,URLError


class NativeComponentDownloadTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.installation.component_download'),'Scoped component retry is absent')
        self.module=importlib.import_module('aikya.installation.component_download')
        self.url='https://nodejs.org/dist/pinned.tar.gz';self.hosts=frozenset({'nodejs.org'})

    def fetch(self):return self.module.fetch(self.url,100,hosts=self.hosts)

    def test_transient_dns_is_retried_without_changing_origin_or_bounds(self):
        with patch.object(self.module.download,'https_bytes',side_effect=[URLError('temporary DNS'),b'verified downstream']) as transport,patch.object(self.module.time,'sleep') as delay:
            self.assertEqual(self.fetch(),b'verified downstream')
            self.assertEqual(transport.call_args_list,[call(self.url,100,hosts=self.hosts)]*2);delay.assert_called_once_with(1)

    def test_permanent_status_certificate_and_validation_errors_are_not_retried(self):
        for error in (HTTPError(self.url,404,'missing',{},None),URLError(ssl.SSLCertVerificationError(1,'invalid certificate')),ValueError('Untrusted redirect')):
            with self.subTest(error=type(error).__name__),patch.object(self.module.download,'https_bytes',side_effect=error) as transport,patch.object(self.module.time,'sleep') as delay:
                with self.assertRaises(type(error)):self.fetch()
                self.assertEqual(transport.call_count,1);delay.assert_not_called()

    def test_transient_server_failure_recovers_and_exhaustion_still_raises(self):
        with patch.object(self.module.download,'https_bytes',side_effect=[HTTPError(self.url,503,'busy',{},None),b'ok']),patch.object(self.module.time,'sleep'):
            self.assertEqual(self.fetch(),b'ok')
        with patch.object(self.module.download,'https_bytes',side_effect=URLError('unavailable')) as transport,patch.object(self.module.time,'sleep') as delay:
            with self.assertRaises(URLError):self.fetch()
            self.assertEqual(transport.call_count,3);self.assertEqual(delay.call_args_list,[call(1),call(2)])


if __name__=='__main__':unittest.main()
