from a2ml.api.utils.s3_fsclient import S3FSClient

def test_split_path_to_bucket_and_key_plain_key():
    path = "s3://auger-options-1sunr2/temp/options-a2ml/data_temp/parquet_review_B26364B24FF94E7.parquet"
    bucket, key = S3FSClient.split_path_to_bucket_and_key(path)

    assert "auger-options-1sunr2" == bucket
    assert "temp/options-a2ml/data_temp/parquet_review_B26364B24FF94E7.parquet" == key

def test_split_path_to_bucket_and_key_rel_path():
    path = "s3://auger-options-1sunr2/temp/options-a2ml/data_temp/"
    bucket, key = S3FSClient.split_path_to_bucket_and_key(path)

    assert "auger-options-1sunr2" == bucket
    assert "temp/options-a2ml/data_temp" == key

def test_split_path_to_bucket_and_key_with_double_leading_slash():
    path = "s3://auger-options-1sunr2//temp/options-a2ml/data_temp/key"
    bucket, key = S3FSClient.split_path_to_bucket_and_key(path)

    assert "auger-options-1sunr2" == bucket
    assert "/temp/options-a2ml/data_temp/key" == key # Hm, looks like source code whanted something else
