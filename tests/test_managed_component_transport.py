"""Extending component downloads must keep the stable release-origin boundary intact."""
import io
import unittest
from unittest.mock import patch
from aikya.installation.bootstrap import download


class Reply(io.BytesIO):
    def __init__(self,url,raw):super().__init__(raw);self.url=url


class Opener:
    def __init__(self,url,raw):self.url=url;self.raw=raw
    def open(self,*args,**kwargs):return Reply(self.url,self.raw)


class ComponentTransportTests(unittest.TestCase):
    def test_official_node_needs_explicit_scoped_hosts_and_is_still_bounded(self):
        url='https://nodejs.org/dist/v26.13.0/node-v26.13.0-darwin-arm64.tar.gz'
        with self.assertRaises(ValueError):download.validate_url(url)
        with patch.object(download,'build_opener',return_value=Opener(url,b'node')):
            self.assertEqual(download.https_bytes(url,4,hosts=frozenset({'nodejs.org'})),b'node')
        with patch.object(download,'build_opener',return_value=Opener(url,b'oversized')):
            with self.assertRaises(ValueError):download.https_bytes(url,4,hosts=frozenset({'nodejs.org'}))
        with self.assertRaises(ValueError):download.validate_url(url)

    def test_component_redirect_cannot_adopt_an_unlisted_server(self):
        url='https://nodejs.org/dist/v26.13.0/asset'
        with patch.object(download,'build_opener',return_value=Opener('https://evil.example/asset',b'foreign')):
            with self.assertRaises(ValueError):download.https_bytes(url,100,hosts=frozenset({'nodejs.org'}))


if __name__=='__main__':unittest.main()
