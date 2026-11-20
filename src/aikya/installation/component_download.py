"""Bounded retries for immutable native-component reads, never model or mutation calls."""
import ssl
import time
from urllib.error import HTTPError,URLError
from .bootstrap import download


def fetch(url,limit,*,hosts):
    download.validate_url(url,hosts)
    for attempt in range(3):
        try:return download.https_bytes(url,limit,hosts=hosts)
        except HTTPError as error:
            if error.code not in (408,429,500,502,503,504) or attempt==2:raise
        except URLError as error:
            if isinstance(error.reason,ssl.SSLCertVerificationError) or attempt==2:raise
        except (TimeoutError,ConnectionError):
            if attempt==2:raise
        time.sleep(attempt+1)
