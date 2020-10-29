from a2ml.api.utils.dataframe import DataFrame

def test_feather_segfault():
    # without explicit list of features this file cause a segfault
    # Looks like a bug in feather
    # https://issues.apache.org/jira/browse/ARROW-9662
    ds = DataFrame({'data_path': 'tests/fixtures/feather/2020-07-30_BF43CA09E5404F9_actuals.feather.zstd'})
    ds.load(features = ['class'])
