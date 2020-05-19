import pandas
from a2ml.api.utils import fsclient


class DataFrame(object):
    """Warpper around Pandas DataFrame."""

    def __init__(self):
        super(DataFrame, self).__init__()

    @staticmethod
    def load(filename, target, features=None, nrows=None, data=None):
        df = None

        if filename:
            if filename.endswith('.json') or filename.endswith('.json.gz'):
                file = fsclient.s3fs_open(filename)
                df = pandas.read_json(file)
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                file = fsclient.s3fs_open(filename)
                df = pandas.read_excel(file)
            elif filename.endswith('.feather') or filename.endswith('.feather.gz'):
                from pyarrow import feather

                with fsclient.open_file(filename, 'rb', encoding=None) as local_file:
                    df = feather.read_feather(local_file, columns=features, use_threads=bool(True))

            if df is None:
                file = fsclient.s3fs_open(filename)
                try:
                    df = DataFrame._read_csv(file, ',', features, nrows)
                except Exception as e:
                    df = DataFrame._read_csv(file, '|', features, nrows)
        else:
            df = DataFrame.load_data(data, features)

        features = df.columns.tolist()
        if target in features:
            df.drop(columns=[target], inplace=True)

        return df

    @staticmethod
    def load_records(filename, target, features=None, nrows=None, data=None):
        df = DataFrame.load(filename, target, features, nrows, data)

        features = df.columns.tolist()
        df.replace({pandas.np.nan: None}, inplace=True)
        records = df.values.tolist()

        return records, features

    @staticmethod
    def load_data(data, columns):
        df = None
        if columns:
            df = pandas.DataFrame.from_records(data, columns=columns)
        else:
            df = pandas.DataFrame(data)

        return df
            
    @staticmethod
    def save(filename, data):
        df = pandas.DataFrame.from_records(data['data'], columns=data['columns'])
        str_data = df.to_csv(None, index=False, encoding='utf-8')
        fsclient.write_text_file(filename, str_data)

    @staticmethod
    def convert_records_to_dict(data):
        df = pandas.DataFrame.from_records(data['data'], columns=data['columns'])
        return df.to_dict('records')

    @staticmethod
    def save_df(filename, df):
        fsclient.create_parent_folder(filename)
        
        df.to_csv(filename, index=False, encoding='utf-8')

    @staticmethod
    def columns(df):
        return df.columns.tolist()

    @staticmethod    
    def select_columns(df, columns):
        return df[columns]

    @staticmethod
    def _read_csv(filename, sep, features=None, nrows=None):
        return pandas.read_csv(filename,
            encoding='utf-8', escapechar="\\", usecols=features,
            na_values=['?'], header=0, prefix=None, sep=sep,
            nrows=nrows, low_memory=False, compression='infer')
