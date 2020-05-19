import arff
import copy
import json
import logging
import os
import pandas as pd
import warnings

from functools import wraps

from a2ml.api.utils import fsclient
from a2ml.api.utils.local_fsclient import LocalFSClient
from a2ml.tasks_queue.utils import get_uid, get_uid4, remove_dups_from_list, process_arff_line

# To avoid warnings for inplace operation on datasets
pd.options.mode.chained_assignment = None

class DataSourceAPIPandas(object):
    BOOLEAN_WORDS_TRUE = ['yes', 'on']
    BOOLEAN_WORDS_FALSE = ['no', 'off']

    def __init__(self, options):
        self.options = options
        self.categoricals = {}
        self.transforms_log = [[],[],[],[]]
        self.df = None
        self.dataset_name = None

    def _get_compression(self, extension):
        compression = self.options.get('data_compression', 'infer')
        if extension.endswith('.gz') or extension.endswith('.gzip'):
            compression = 'gzip'
        elif extension.endswith('.bz2'):
            compression = 'bz2'
        elif extension.endswith('.zip'):
            compression = 'zip'
        elif extension.endswith('.xz'):
            compression = 'xz'

        return compression

    def load_from_file(self, path, features=None, nrows=None):
        from collections import OrderedDict

        extension = path
        if self.options.get('data_extension'):
            extension = self.options['data_extension']

        if self.options.get('content_type') == 'multipart':
            fsclient.merge_folder_files(path)

        if extension.endswith('.arff') or extension.endswith('.arff.gz'):
            arffFile = None
            class ArffFile:
                def __init__(self, file):
                    self.file = file
                    self.date_attrs = {}

                def __iter__(self):
                    return self

                def __next__(self):
                    line = process_arff_line(next(self.file), self.date_attrs)
                    return line

            try:

                with fsclient.open(path, 'r') as f:
                    arffFile = ArffFile(f)
                    arff_data = arff.load(arffFile, return_type=arff.COO)

                convert_arff = DataSourceAPIPandas._convert_arff_coo
            except arff.BadLayout:
                with fsclient.open(path, 'r') as f:
                    arffFile = ArffFile(f)
                    arff_data = arff.load(arffFile, return_type=arff.DENSE)

                convert_arff = DataSourceAPIPandas._convert_arff_dense

            columns = [a[0] for a in arff_data['attributes']]
            series = convert_arff(features, columns, arff_data['data'])

            res = pd.DataFrame.from_dict(OrderedDict(
                (c, s) for c, s in zip(columns, series) if s is not None
            ))
            for date_field, fmt in arffFile.date_attrs.items():
                res[date_field] = pd.to_datetime(res[date_field], infer_datetime_format=True, errors='ignore', utc=True)

            return res
        elif extension.endswith('.pkl') or extension.endswith('.pkl.gz'):
            return self.loadFromBinFile(path, features)
        elif extension.endswith('.json') or extension.endswith('.json.gz'):
            path = fsclient.s3fs_open(path)
            return pd.read_json(path, orient=self.options.get('json_orient',None))
        elif extension.endswith('.xlsx') or extension.endswith('.xls'):
            path = fsclient.s3fs_open(path)
            return pd.read_excel(path)
        elif extension.endswith('.feather') or extension.endswith('.feather.gz') or extension.endswith('.feather.zstd') or extension.endswith('.feather.lz4'):
            return self.loadFromFeatherFile(path)

        csv_with_header = self.options.get('csv_with_header', True)
        header = 0 if csv_with_header else None
        prefix = None if csv_with_header else 'c'

        compression = self._get_compression(extension)
        path = fsclient.s3fs_open(path)

        res_df = None
        try:
            res_df = pd.read_csv(
                path,
                encoding='utf-8',
                escapechar="\\",
                usecols=features,
                na_values=['?'],
                header=header,
                prefix=prefix,
                sep = ',',
                nrows=nrows,
                low_memory=False,
                compression=compression
            )
        except Exception as e:
            logging.error("read_csv failed: %s"%e)
            res_df = pd.read_csv(
                path,
                encoding='utf-8',
                escapechar="\\",
                usecols=features,
                na_values=['?'],
                header=header,
                prefix=prefix,
                sep = '|',
                nrows=nrows,
                low_memory=False,
                compression=compression
            )

        if res_df is not None:
            for name, value in res_df.dtypes.items():
                if value == 'object':
                    res_df[name] = pd.to_datetime(res_df[name], infer_datetime_format=True, errors='ignore', utc=True)

        return res_df

    def load(self, features=None, nrows=None):
        self.categoricals = {}
        self.transforms_log = [[],[],[],[]]

        import csv
        from io import StringIO

        path = self.options['data_path']
        if isinstance(path, StringIO):
            path.seek(0)
            self.df = pd.read_csv(path, encoding='utf-8', escapechar="\\", usecols=features, na_values=['?'], nrows=nrows)
            if self.options.get("targetFeature") in self.df.columns:
                self.dropna([self.options["targetFeature"]])
        else:
            if path.startswith("jdbc:"):
                import psycopg2
                from psycopg2.extensions import parse_dsn
                path = path.replace('sslfactory=org.postgresql.ssl.NonValidatingFactory&', '')
                ary = path.split('tablename')
                path = ary[0]
                tablename = ary[1]
                dataset_name = tablename

                self.dbconn_args = parse_dsn(path[5:])
                conn = psycopg2.connect(**self.dbconn_args)
                self.df = pd.read_sql("select * from %s"%tablename, con=conn)
            else:
                path, remote_path = self._check_remote_path()
                try:
                    self.df = self.load_from_file(path, features=features, nrows=nrows)
                except:
                    if remote_path:
                        logging.exception("Loading local file failed. Download it again...")
                        self.options['data_path'] = remote_path
                        path, remote_path = self._check_remote_path(force_download=True)
                        self.df = self.load_from_file(path, features=features, nrows=nrows)
                    else:
                        raise

                self.dataset_name = os.path.basename(path)

            if self.options.get("targetFeature") in self.df.columns:
                self.dropna([self.options["targetFeature"]])
        return self

    def _check_remote_path(self, force_download=False):
        remote_path = None
        if self.options['data_path'].startswith("http:") or self.options['data_path'].startswith("https:"):
            local_dir = Localfsclient.get_temp_folder()
            file_name = 'data-' + get_uid4

            local_file_path = download_file(self.options['data_path'],
                local_dir=local_dir, file_name=file_name, force_download=force_download)

            remote_path = self.options['data_path']
            self.options['data_path'] = local_file_path

        return self.options['data_path'], remote_path

    def saveToBinFile(self, path):
        fsclient.save_object_to_file(self.df, path)

    def loadFromBinFile(self, path, features=None):
        self.df = fsclient.load_object_from_file(path)

        if features:
            self.df =  self.df[features]

        return self.df

    def saveToFeatherFile(self, path):
        fsclient.save_object_to_file(self.df, path, fmt="feather")

    def loadFromFeatherFile(self, path, features=None):
        from pyarrow import feather

        with fsclient.open_file(path, 'rb', encoding=None) as local_file:
            self.df = feather.read_feather(local_file, columns=features, use_threads=bool(True))

        return self.df
            
    def count(self):
        if self.df is not None:
            return len(self.df)
        else:
            return 0

    @property
    def columns(self):
        return self.df.columns.get_values().tolist()

    def _map_dtypes(self, dtype):
        dtype_map = {'int64': 'integer', 'float64':'double', 'object': 'string',
            'categorical':'categorical', 'datetime64[ns]': 'datetime', 'bool': 'boolean'}
        if dtype_map.get(dtype, None):
            return dtype_map[dtype]

        if dtype and (dtype.startswith('int') or dtype.startswith('uint')):
            return 'integer'

        if dtype and dtype.startswith('float'):
            return 'float'

        if dtype and dtype.startswith('double'):
            return 'double'

        if dtype and dtype.startswith('datetime64'):
            return 'datetime'

        return dtype

    @property
    def dtypes(self):
        types_list = []
        columns_list = self.columns
        for idx, dtype in enumerate(self.df.dtypes):
            types_list.append((columns_list[idx], self._map_dtypes(dtype.name)))

        return types_list

    @property
    def dtypes_dict(self):
        types_dict = {}
        columns_list = self.columns
        for idx, dtype in enumerate(self.df.dtypes):
            types_dict[columns_list[idx]] = self._map_dtypes(dtype.name)

        return types_dict

    def drop(self, columns):
        self.df.drop(columns, inplace=True, axis=1)

    def drop_duplicates(self, columns=None):
        self.df.drop_duplicates(subset=columns, inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        return self

    def dropna(self, columns=None):
        self.df.dropna(subset=columns, inplace=True, axis=0)
        self.df.reset_index(drop=True, inplace=True)
        return self

    def fillna(self, value):
        if isinstance(value, dict):
            value = value.copy()
            for item in self.dtypes:
                if list(value.keys())[0] == item[0]:
                    if item[1] == 'string':
                        value[list(value.keys())[0]] = str(list(value.values())[0])
                    elif item[1] == 'integer':
                        value[list(value.keys())[0]] = int(list(value.values())[0])
                    else:
                        value[list(value.keys())[0]] = float(list(value.values())[0])

        self.df.fillna(value, inplace=True)
        return self

    @staticmethod
    def _convert_arff_coo(features, columns, arff_data_data):
        if features is None:
            data = [([], []) for _ in columns]
        else:
            fset = remove_dups_from_list(features)
            data = [([], []) if c in fset else None for c in columns]

        for v, i, j in zip(*arff_data_data):
            d = data[j]
            if d is not None:
                indices, values = d
                if indices:
                    assert indices[-1] < i
                indices.append(i)
                values.append(v)

        max_i = -1
        for d in data:
            if d is not None and len(d[0]) > 0:
                max_i = max(max_i, d[0][-1])
        height = max_i + 1

        series = []
        for d in data:
            if d is None:
                s = None
            else:
                keys, values = d
                sa = pd.SparseArray(
                    values,
                    sparse_index=pd._libs.sparse.IntIndex(height, keys),
                    fill_value=0
                )
                s = pd.Series(sa.values)
            series.append(s)

        return series

    @staticmethod
    def _convert_arff_dense(features, columns, arff_data_data):
        if features is None or set(features) == set(columns):
            return zip(*arff_data_data)

        fset = remove_dups_from_list(features)
        return [
            [row[i] for row in arff_data_data] if c in fset else None
            for i, c in enumerate(columns)
        ]

