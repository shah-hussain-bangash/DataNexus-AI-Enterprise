"""NYC TLC downloader tests require no network and never create fake trip rows."""
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class TLCBronzeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.downloader=module("scripts/ingest_nyc_tlc.py","tlc_ingest")
    cls.manifests=module("apps/api/tlc_manifest.py","tlc_manifest")
 def test_only_fixed_nyc_tlc_urls(self):
    url,name=self.downloader.source_url(2024,1)
    self.assertEqual(url,"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet")
    with self.assertRaises(ValueError):self.downloader.source_url(2024,13)
    with self.assertRaises(ValueError):self.downloader.source_url(2050,1)
 def test_no_data_no_fabricated_rows(self):
    with tempfile.TemporaryDirectory() as root:
        self.assertEqual(self.manifests.available_downloads(root),[])
 def test_verified_raw_download_manifest_without_schema_claim(self):
    payload=b"PAR1"+b"test-minimal-placeholder"+b"PAR1"
    class Response:
        def __init__(self):self.buffer=io.BytesIO(payload)
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def geturl(self):return self.url
        def read(self,n):return self.buffer.read(n)
    def opener(req,timeout):
        o=Response();o.url=req.full_url;return o
    with tempfile.TemporaryDirectory() as root:
        info=self.downloader.download_month(2024,1,root,opener)
        self.assertEqual(info["bytes"],len(payload))
        self.assertFalse(info["schema_validated"])
        self.assertIsNone(info["row_count"])
        self.assertEqual(len(self.manifests.available_downloads(root)),1)
        with self.assertRaises(FileExistsError):self.downloader.download_month(2024,1,root,opener)
 def test_broken_file_rejected(self):
    class Response:
        def __init__(self):self.buf=io.BytesIO(b"wrong")
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def geturl(self):return self.url
        def read(self,n):return self.buf.read(n)
    def opener(req,timeout):
        o=Response();o.url=req.full_url;return o
    with tempfile.TemporaryDirectory() as root:
        with self.assertRaises(ValueError):self.downloader.download_month(2024,1,root,opener)
        self.assertEqual(self.manifests.available_downloads(root),[])
