import os

from vcr import VCR

vcr = VCR(
    cassette_library_dir=os.path.join(os.getcwd(), 'tests/cassettes'),
    decode_compressed_response=True,
    match_on=['uri', 'method'],
    record_mode='once',
    ignore_hosts=('minio', 'localhost', '127.0.0.1'),
)
