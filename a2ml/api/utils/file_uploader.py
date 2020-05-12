import boto3
import math
import os
import sys
import threading

from boto3.s3.transfer import TransferConfig
from urllib.parse import urlparse
from uuid import uuid4

from  a2ml.api.utils import fsclient

class FileUploader(object):
    def __init__(self, bucket, endpoint_url, access_key, secret_key, session_token):
        self.bucket = bucket

        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

    def transfer_config(self):
        return TransferConfig(
            multipart_threshold=1024 * 25,
            max_concurrency=4,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )

    def multi_part_upload(self, file_path, key=None, callback=None):
        if not key:
            file_name = os.path.basename(file_path)
            base_name, extension = file_name.split('.', 1)
            key = 'uploads/' + base_name + '-' + str(uuid4())[0:8] + '.' + extension

        self.client.upload_file(
            file_path,
            self.bucket,
            key,
            Config=self.transfer_config(),
            Callback=callback
        )

        return f's3://{self.bucket}/{key}'

    def multipart_upload_obj(self, file_obj, key, callback=None):
        self.client.upload_fileobj(
            file_obj,
            self.bucket,
            key,
            Config=self.transfer_config(),
            Callback=callback
        )

        return 's3://%s/%s' % (self.bucket, key)

    def download(self, s3_path, local_path):
        url = urlparse(s3_path)
        self.client.download_file(self.bucket, url.path, local_path)

class OnelineProgressPercentage(object):
    def __init__(self, filename):
        self._filename = os.path.basename(filename)
        self._size = float(fsclient.get_file_size(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._done = False

    def __call__(self, bytes_amount):
        with self._lock:
            if not self._done:
                self._seen_so_far += bytes_amount
                percentage = (self._seen_so_far / self._size) * 100
                sys.stdout.write(
                    "\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far, int(self._size), percentage)
                )
                sys.stdout.flush()

                if percentage >= 100:
                    self._done = True
                    sys.stdout.write("\n")

class NewlineProgressPercentage(object):
    def __init__(self, filename, report_step = 25):
        self._filename = os.path.basename(filename)
        self._size = float(fsclient.get_file_size(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._reported_steps = 0
        self._report_step = report_step

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            if (math.floor(percentage / self._report_step) > self._reported_steps):
                self._reported_steps = math.floor(percentage / self._report_step)

                sys.stdout.write(
                    "%s  %s / %s  (%.2f%%)\n" % (self._filename, self._seen_so_far, int(self._size), percentage)
                )
                sys.stdout.flush()
