import pandas
from a2ml.api.utils import fsclient


class DataFrame(object):
    """Warpper around Pandas DataFrame."""

    def __init__(self):
        super(DataFrame, self).__init__()

    @staticmethod
    def load(filename, target, features=None, nrows=None):
        file = fsclient.s3fs_open(filename)
        df = None
        if filename.endswith('.json') or filename.endswith('.json.gz'):
            df = pandas.read_json(file)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pandas.read_excel(file)
        elif filename.endswith('.feather') or filename.endswith('.feather.gz'):
            import feather
            df = feather.read_dataframe(file, columns=features, use_threads=bool(True))

        if df is None:
            try:
                df = DataFrame._read_csv(file, ',', features, nrows)
            except Exception as e:
                df = DataFrame._read_csv(file, '|', features, nrows)

        features = df.columns.tolist()
        if target in features:
            df.drop(columns=[target], inplace=True)

        return df

    @staticmethod
    def load_records(filename, target, features=None, nrows=None):
        df = DataFrame.load(filename, target, features, nrows)

        features = df.columns.tolist()
        df.replace({pandas.np.nan: None}, inplace=True)
        records = df.values.tolist()

        return records, features

    @staticmethod
    def save(filename, data):
        df = pandas.DataFrame.from_records(data['data'], columns=data['columns'])
        str_data = df.to_csv(None, index=False, encoding='utf-8')
        fsclient.write_text_file(filename, str_data)

    @staticmethod
    def _read_csv(filename, sep, features=None, nrows=None):
        return pandas.read_csv(filename,
            encoding='utf-8', escapechar="\\", usecols=features,
            na_values=['?'], header=0, prefix=None, sep=sep,
            nrows=nrows, low_memory=False, compression='infer')
