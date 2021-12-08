import arff
import copy
import json
import logging
import math
import os
import pandas as pd
import warnings

from functools import wraps

from a2ml.api.utils import fsclient, get_uid, get_uid4, remove_dups_from_list, process_arff_line, download_file, retry_helper, parse_url
from a2ml.api.utils.local_fsclient import LocalFSClient


# To avoid warnings for inplace operation on datasets
pd.options.mode.chained_assignment = None

class DataFrame(object):
    BOOLEAN_WORDS_TRUE = ['yes', 'on']
    BOOLEAN_WORDS_FALSE = ['no', 'off']

    def __init__(self, options):
        self.options = options
        self.categoricals = {}
        self.transforms_log = [[],[],[],[]]
        self.df = None
        self.dataset_name = None
        self.loaded_columns = None
        self.from_pandas = False

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

    @staticmethod
    def create_dataframe(data_path=None, records=None, features=None, reset_index=False, dtype=None):
        if data_path is not None:
            if isinstance(data_path, pd.DataFrame):
                ds = DataFrame({})
                ds.df = data_path
            elif isinstance(data_path, DataFrame):
                ds = data_path
            elif isinstance(data_path, list):
                ds = DataFrame({})
                ds.load_records(data_path)                
            elif isinstance(data_path, dict):
                ds = DataFrame({})

                if 'data' in data_path and 'columns' in data_path:
                    ds.load_records(data_path['data'], features=data_path['columns'])
                else:    
                    ds.load_records(data_path)
            else:    
                ds = DataFrame({'data_path': data_path})
                ds.load(features = features, dtype=dtype)
        else:
            ds = DataFrame({})
            ds.load_records(records, features=features)

        if reset_index and ds.df is not None:
            ds.df.reset_index(drop=True, inplace=True)


        # if data_path:
        #     ds = DataFrame({'data_path': data_path})
        #     ds.load(features = features)
        # elif records is not None and isinstance(records, pd.DataFrame):
        #     ds = DataFrame({})
        #     ds.df = records
        #     if features:
        #         ds.df = ds.df[features]
                    
        #     ds.from_pandas = True
        # else:
        #     ds = DataFrame({})
        #     ds.load_records(records, features=features)

        return ds

    @staticmethod
    def load_from_files(files, features=None):
        for file in files:
            path = file if type(file) == str else file['path']

            fsclient.wait_for_file(path, True)
            try:
                df = retry_helper(lambda: DataFrame.create_dataframe(path, None, features))
                yield (file, df)
            except Exception as exc:
                logging.exception("load_from_files failed for: %s. Error: %s"%(path, exc))

    @staticmethod
    def is_dataframe(data):
        return isinstance(data, pd.DataFrame) or isinstance(data, DataFrame)

    def load_from_file(self, path, features=None, nrows=None, dtype=None):
        from collections import OrderedDict

        extension = path
        if self.options.get('data_extension', 'infer') != 'infer':
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

                convert_arff = DataFrame._convert_arff_coo
            except arff.BadLayout:
                with fsclient.open(path, 'r') as f:
                    arffFile = ArffFile(f)
                    arff_data = arff.load(arffFile, return_type=arff.DENSE)

                convert_arff = DataFrame._convert_arff_dense

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
            res = pd.read_json(path, orient=self.options.get('json_orient',None))
            if features:
                res = res[features]
            return res
        elif extension.endswith('.xlsx') or extension.endswith('.xls'):
            path = fsclient.s3fs_open(path)
            return pd.read_excel(path, usecols=features)
        elif extension.endswith('.feather') or extension.endswith('.feather.gz') or extension.endswith('.feather.zstd') or extension.endswith('.feather.lz4'):
            # Features list is optional for feather file, but it can segfault without it on some files
            return self.loadFromFeatherFile(path, features)
        elif extension.endswith('.parquet'):
            return self.loadFromParquetFile(path, features)

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
                compression=compression,
                dtype=dtype
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
                compression=compression,
                dtype=dtype
            )

        # if res_df is not None:
        #     for name, value in res_df.dtypes.items():
        #         if value == 'object':
        #             res_df[name] = pd.to_datetime(res_df[name], infer_datetime_format=True, errors='ignore', utc=True)

        return res_df

    def load(self, features=None, nrows=None, dtype=None):
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
                path, params = parse_url(path)

                self.dbconn_args = parse_dsn(path)
                conn = psycopg2.connect(**self.dbconn_args)

                sql_cmd = "select " + (",".join(features) if features else "*") +" from %s"%params['tablename'][0]
                if 'limit' in params:
                    sql_cmd += " LIMIT %s"%params['limit'][0]

                if 'offset' in params:
                    sql_cmd += " OFFSET %s"%params['offset'][0]

                logging.info("Read data from remote DB: %s"%sql_cmd)
                self.df = pd.read_sql(sql_cmd, con=conn)
            else:
                path, remote_path = self._check_remote_path()
                try:
                    self.df = self.load_from_file(path, features=features, nrows=nrows, dtype=dtype)
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
            local_dir = LocalFSClient().get_temp_folder()
            file_name = 'data-' + get_uid4()

            local_file_path = download_file(self.options['data_path'],
                local_dir=local_dir, file_name=file_name, force_download=force_download)

            remote_path = self.options['data_path']
            self.options['data_path'] = local_file_path

        return self.options['data_path'], remote_path

    def load_records(self, records, features=None):
        self.categoricals = {}
        self.transforms_log = [[],[],[],[]]

        if features:
            self.df = pd.DataFrame.from_records(records, columns=features)
            self.loaded_columns = features
        else:
            self.df = pd.DataFrame(records) #dict

        return self

    def get_records(self):
        return self.df.values.tolist()

    def saveToCsvFile(self, path, compression="gzip"):
        fsclient.remove_file(path)
        fsclient.create_parent_folder(path)

        with fsclient.save_local(path) as local_path:
            self.df.to_csv(local_path, index=False, compression=compression, encoding='utf-8')

    def saveToBinFile(self, path):
        fsclient.save_object_to_file(self.df, path)

    def loadFromBinFile(self, path, features=None):
        self.df = fsclient.load_object_from_file(path)

        if features:
            self.df =  self.df[features]

        return self.df

    def saveToFeatherFile(self, path):
        fsclient.save_object_to_file(self.df, path, fmt="feather")

    def saveToParquetFile(self, path, compression="gzip"):
        fsclient.remove_file(path)
        fsclient.create_parent_folder(path)

        with fsclient.save_local(path) as local_path:
            self.df.to_parquet(local_path, index=False, compression=compression)

    def loadFromFeatherFile(self, path, features=None):
        self.df = fsclient.load_db_from_feather_file(path, features)
        return self.df

    def loadFromParquetFile(self, path, features=None):
        self.df = fsclient.load_db_from_parquet_file(path, features)
        return self.df

    def saveToFile(self, path):
        if path.endswith('.feather') or path.endswith('.feather.gz') or path.endswith('.feather.zstd') or path.endswith('.feather.lz4'):
            self.saveToFeatherFile(path)
        elif path.endswith('.parquet'):
            self.saveToParquetFile(path)
        else:
            compression = None
            if path.endswith('.gz'):
                compression = 'gzip'

            self.saveToCsvFile(path, compression)

    def count(self):
        if self.df is not None:
            return len(self.df)
        else:
            return 0

    def __len__(self):
        return self.count()

    @property
    def columns(self):
        return self.df.columns.tolist()

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

    def select(self, features):
        self.df = self.df[features]
        return self

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

    def convertToCategorical(self, col_names, is_target = False, categories = None):
        #print("convertToCategorical:%s"%col_names)
        if not isinstance(col_names, list):
            col_names = [col_names]

        if is_target:
            for col in col_names:
                if col in self.columns and self.categoricals.get(col, None) is None:
                    self.df[col] = pd.Categorical(self.df[col], categories=categories)
                    self.categoricals[col] = {'categories': list(self.df[col].cat.categories)}
                    self.df[col] = self.df[col].cat.codes
        else:
            cols_to_process = []
            cols = self.columns
            for col in col_names:
                if col in cols:
                    cols_to_process.append(col)

            #print(cols_to_process)
            if cols_to_process:
                self.df = pd.get_dummies(self.df, columns=cols_to_process)
                new_cols = self.columns

                for col in cols_to_process:
                    generated_cols = []
                    for new_col in new_cols:
                        if new_col.startswith(col+'_'):
                            generated_cols.append(new_col)

                    self.categoricals[col] = {'columns': generated_cols}

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

    def _check_for_json(self, cname):
        rows = self.df[cname][(self.df[cname] != '[]') & (self.df[cname] != '{}')].values

        if rows is None or len(rows) == 0:
            return []
        else:
            row = rows[0]

        try:
            data = json.loads(row)
            children = []
            for key in data:
                name = str(key) + '_' + cname
                dtype = type(data[key]).__name__
                if dtype == 'unicode':
                    dtype = 'string'

                children.append(
                    {
                        'column_name': name,
                        'orig_column_name': str(key),
                        'child': cname,
                        'parent': None,
                        'orig_datatype': dtype,
                        'datatype': dtype,
                        'range': ('', ''),
                        'use': False,
                        'isTarget': False,
                        'missing_values': 0,
                        'unique_values': 0
                    }
                )
            return children
        except Exception as e:
            return []

    def __format_number_for_serialization(self, v):
        if v != v or math.isinf(v):
            return None
        else:
            return round(v, 6)

    def getSummary(self):
        types_list = []
        columns_list = self.df.columns.values.tolist()
        for idx, dtype in enumerate(self.df.dtypes):
            types_list.append((columns_list[idx], self._map_dtypes(dtype.name)))

        info = {"dtypes": self.dtypes, "count": self.count(), 'columns_count': len(self.columns)}
        stat_data = []
        for x in info['dtypes']:
            cname = str(x[0])
            ctype = x[1]
            children = []

            if ctype == 'string':
                children = self._check_for_json(cname)

            # add children or just add row
            if children:
                stat_data = stat_data + children
            else:
                item = {
                    'column_name': cname,
                    'orig_datatype': ctype,
                    'datatype': ctype,
                }

                if ctype == 'integer' or ctype == 'float' or ctype == 'double':
                    mean = self.__format_number_for_serialization(self.df[cname].mean())
                    if mean:
                        item['avg'] = mean

                    std = self.__format_number_for_serialization(self.df[cname].std())
                    if std:
                        item['std_dev'] = std

                stat_data.append(item)

        #TODO : remove from UI isTarget and use
        lef = set(self.options.get('labelEncodingFeatures', []))
        tf = self.options.get('targetFeature', "")
        fc = set(self.options.get('featureColumns', []))
        tsf = set(self.options.get('timeSeriesFeatures', []))
        dtf = self.options.get('datetimeFeatures', [])
        if dtf is None:
            dtf = []

        for row in stat_data:
            row['isTarget'] = False
            row['use'] = False

            cname = row['column_name']
            if row['datatype'] == 'string':
                row['datatype'] = 'hashing' if cname in lef else 'categorical'

            if cname == tf:
                row['isTarget'] = True
            if cname in fc:
                row['use'] = True
            if cname in tsf:
                row['datatype'] = 'timeseries'
            if cname in dtf:
                row['datatype'] = 'datetime'

        info['stat_data'] = stat_data
        del info['dtypes']

        return info

    def update_options_by_dataset_statistics(self, stat_data=None):
        transforms = []
        categoricals = []
        hashings = []
        timeseries = []
        selected_features = []
        target_feature = None
        binaryClassification = None
        minority_target_class = None
        datetimeFeatures = []
        stat_data = stat_data or self.options.get('dataset_statistics', {}).get('stat_data', [])

        for item in stat_data:
            if item.get('isTarget'):
                target_feature = item['column_name']
                if (self.options.get('model_type', '') == 'classification' or self.options.get('classification')):
                    binaryClassification = item.get('unique_values', 0) == 2

                    #Find minority target class
                    if item.get('value_counts_ex'):
                        minority_target_class = item['value_counts_ex'][0]['value']
                        minority_target_count = item['value_counts_ex'][0]['count']
                        for vc in item['value_counts_ex']:
                            if vc['count'] < minority_target_count:
                                minority_target_class = vc['value']
                                minority_target_count = vc['count']

            if item.get('use') and not item.get('isTarget'):
                selected_features.append(item['column_name'])

            if item.get('use') or item.get('isTarget'):
                if item['orig_datatype'] == 'string':
                    if item['datatype'] == 'integer' or item['datatype'] == 'double':
                        transforms.append({"withNumericColumn":{"col_name":item['column_name']}})
                    if item['datatype'] == 'boolean':
                        transforms.append({"withBooleanColumn":{"col_name":item['column_name']}})

                if item['datatype'] == 'categorical':
                    categoricals.append(item['column_name'])
                if item['datatype'] == 'hashing':
                    categoricals.append(item['column_name'])
                    hashings.append(item['column_name'])
                if item['datatype'] == 'timeseries':
                    timeseries.append(item['column_name'])
                if item['datatype'] == 'datetime':
                    datetimeFeatures.append(item['column_name'])

        if categoricals:
            self.options['categoricalFeatures'] = categoricals
        if hashings:
            self.options['labelEncodingFeatures'] = hashings
        if timeseries:
            self.options['timeSeriesFeatures'] = timeseries
        if selected_features:
            self.options['featureColumns'] = selected_features
        if target_feature:
            self.options['targetFeature'] = target_feature
        if datetimeFeatures:
            self.options['datetimeFeatures'] = datetimeFeatures
        if binaryClassification is not None:
            self.options['binaryClassification'] = binaryClassification
        if minority_target_class is not None and self.options.get('minority_target_class') is None and \
            self.options.get('use_minority_target_class'):
            self.options['minority_target_class'] = minority_target_class

        if not 'datasource_transforms' in self.options:
            self.options['datasource_transforms'] = []

        self.options['datasource_transforms'] = [transforms]

        return self.options
