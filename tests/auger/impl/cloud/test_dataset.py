import os

from a2ml.api.auger.impl.cloud.dataset import AugerDataSetApi
from a2ml.api.utils.s3_fsclient import S3FSClient

class TestAugerDataSetApi():
    def test_verify_local(self):
        path, local = AugerDataSetApi.verify('tests/fixtures/iris.csv')

        assert local == True
        assert path == os.path.join(os.getcwd(), 'tests/fixtures/iris.csv')

    def test_verify_http(self):
        path, local = AugerDataSetApi.verify('http://some-host.com/iris.csv')

        assert local == False
        assert path == 'http://some-host.com/iris.csv'

    def test_verify_s3(self, monkeypatch):
        monkeypatch.setattr(S3FSClient, 'is_file_exists', lambda self, path: True)

        path, local = AugerDataSetApi.verify('s3://some-bucket/iris.csv')

        assert local == True
        assert path == 's3://some-bucket/iris.csv'
