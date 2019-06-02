import pandas


class DataFrame(object):
    """Warpper around Pandas DataFrame."""

    def __init__(self):
        super(DataFrame, self).__init__()

    @staticmethod
    def load(filename, target, features=None, nrows=None):
        try:
            df = DataFrame._read_csv(filename, ',', features, nrows)
        except Exception as e:
            df = DataFrame._read_csv(filename, '|', features, nrows)

        features = df.columns.get_values().tolist()
        if target in features:
            df.drop(columns=[target], inplace=True)

        return df

    @staticmethod
    def save(filename, data):
        df = pandas.DataFrame.from_dict(data)
        df.to_csv(filename, index=False, encoding='utf-8')

    @staticmethod
    def _read_csv(filename, sep, features=None, nrows=None):
        return pandas.read_csv(filename,
            encoding='utf-8', escapechar="\\", usecols=features,
            na_values=['?'], header=0, prefix=None, sep=sep,
            nrows=nrows, low_memory=False, compression='infer')
