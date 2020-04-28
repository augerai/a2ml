import boto3
import os
import sys
import threading

from boto3.s3.transfer import TransferConfig
from uuid import uuid4

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

    def multi_part_upload(self, file_path):
        config = TransferConfig(
            multipart_threshold=1024 * 25,
            max_concurrency=4,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )

        file_name = os.path.basename(file_path)
        base_name, extension = file_name.split('.', 1)
        key = 'uploads/' + base_name + '-' + str(uuid4()) + '.' + extension

        self.client.upload_file(
            file_path,
            self.bucket,
            key,
            Config=config,
            Callback=self.ProgressPercentage(file_path)
        )

        sys.stdout.write("\n")
        return f's3://{self.bucket}/{key}'

    class ProgressPercentage(object):
        def __init__(self, filename):
            self._filename = filename
            self._size = float(os.path.getsize(filename))
            self._seen_so_far = 0
            self._lock = threading.Lock()

        def __call__(self, bytes_amount):
            with self._lock:
                self._seen_so_far += bytes_amount
                percentage = (self._seen_so_far / self._size) * 100
                sys.stdout.write(
                    "\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far, self._size, percentage)
                )
                sys.stdout.flush()
