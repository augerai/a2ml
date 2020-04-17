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
from a2ml.tasks_queue.utils import get_uid, remove_dups_from_list, convertStringsToUTF8, process_arff_line

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

    @staticmethod
    def create_dataframe(data_path=None, records=None, features=None):
        if data_path:
            ds = DataSourceAPIPandas({'data_path': data_path})
            ds.load(features = features, use_cache=False)
        else:
            ds = DataSourceAPIPandas({})
            ds.load_records(records, features=features, use_cache=False)

        return ds

    def load_from_file(self, path, features=None, nrows=None):
        from collections import OrderedDict

        if not fsclient.is_abs_path(path) and 'augerInfo' in self.options:
            path = os.path.join(self.options['augerInfo']['projectPath'], path)

        extension = path
        if self.options.get('data_extension'):
            extension = self.options['data_extension']

        if self.options.get('content_type') == 'multipart':
            fsclient.merge_folder_files(path)

        #logging.info("load_from_file path: %s, extension: %s"%(path, extension))
        if extension.endswith('.arff') or extension.endswith('.arff.gz'):
            #TODO: support nrows  in arff
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
                #print(date_field, fmt)
                res[date_field] = pd.to_datetime(res[date_field], infer_datetime_format=True, errors='ignore', utc=True)

            return res
        elif extension.endswith('.pkl') or extension.endswith('.pkl.gz'):
            #TODO: support nrows  in pkl file
            return self.loadFromBinFile(path, features)
        elif extension.endswith('.json') or extension.endswith('.json.gz'):
            path = fsclient.s3fs_open(path)
            return pd.read_json(path, orient=self.options.get('json_orient',None))
        elif extension.endswith('.xlsx') or extension.endswith('.xls'):
            path = fsclient.s3fs_open(path)
            return pd.read_excel(path)
        elif extension.endswith('.feather') or extension.endswith('.feather.gz'):
            import feather
            # path = fsclient.s3fs_open(path)

            # if fsclient.isS3Path(path):
            #     with fsclient.save_atomic(path, move_file=False) as local_tmp_path:
            #         fsclient.downloadFile(path, local_tmp_path)
            #         return feather.read_dataframe(local_tmp_path, columns=features, use_threads=bool(True))

            with fsclient.open(path, 'rb', encoding=None) as local_file:
                return feather.read_dataframe(local_file, columns=features, use_threads=bool(True))

            # from pyarrow import feather
            # return feather.read_feather(path, columns=features, use_threads=bool(True))
            #return pd.read_feather(path) #, columns = features)

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

    def load(self, features=None, use_cache=True, nrows=None):
        self.categoricals = {}
        self.transforms_log = [[],[],[],[]]

        if use_cache and self.loadFromCacheFile("data_transformed",
            features, self.options.get("datetimeFeatures", None)):
            transformations_path = self._get_datacache_path("transformations.json")
            if fsclient.isFileExists(transformations_path):
                self.transforms_log = fsclient.readJSONFile(transformations_path)
        else:
            import csv
            from io import StringIO

            path = self.options['data_path']
            if isinstance(path, StringIO):
                path.seek(0)
                self.df = pd.read_csv(path, #parse_dates=self.options.get("datetimeFeatures", None),
                    encoding='utf-8', escapechar="\\", usecols=features, na_values=['?'], nrows=nrows)
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

                #self._update_dataset_manifest({'name': self.dataset_name, 'statistics': {'stat_data':[]}}, skip_if_exists=True)
        return self

    def _check_remote_path(self, force_download=False):
        remote_path = None
        if self.options['data_path'].startswith("http:") or self.options['data_path'].startswith("https:"):
            local_dir = self.options.get('augerInfo', {}).get('dataTmpPath', Localfsclient.get_temp_folder())
            file_name = self.options.get('augerInfo', {}).get('project_file_id')
            if not file_name:
                file_name = self.options.get('data_id')

            local_file_path = download_file(self.options['data_path'],
                local_dir=local_dir, file_name=str(file_name), force_download=force_download)

            remote_path = self.options['data_path']
            self.options['data_path'] = local_file_path

        return self.options['data_path'], remote_path

    def load_records(self, records, features=None, use_cache=False ):
        self.categoricals = {}
        self.transforms_log = [[],[],[],[]]

        self.df = pd.DataFrame.from_records(records, columns=features)

        return self

    def saveToCsvFile(self, path, compression="gzip"):
        fsclient.removeFile(path)
        fsclient.createParentFolder(path)

        with fsclient.save_local(path) as local_path:
            self.df.to_csv(local_path, index=False, compression=compression, encoding='utf-8')

    def saveToBinFile(self, path):
        fsclient.save_object_to_file(self.df, path)

    def loadFromBinFile(self, path, features=None):
        self.df = fsclient.load_object_from_file(path)

        if features:
            self.df =  self.df[features]

        return self.df

    def saveToCacheFile(self, name):
        path = self._get_datacache_path(name + ".pkl.gz")
        uid_path = self._get_datacache_path(name + ".uid.json")
        fsclient.removeFile(uid_path)

        self.saveToBinFile(path)
        fsclient.writeJSONFile(uid_path, {'uid': get_uid()})

        return path

    def loadFromCacheFile(self, name, features=None, parse_dates=None):
        if self.options.get('augerInfo', {}).get('datacachePath') is not None:
            path = self._get_datacache_path(name + ".pkl.gz")
            try:
                if fsclient.isFileExists(path):
                    self.df = self.loadFromBinFile(path, features)
                    return True
            except:
                logging.exception("Failed to load cache file: %s"%path)

        return False

    def count(self):
        if self.df is not None:
            return len(self.df)
        else:
            return 0

    def getCategoricalsInfo(self):
        return self.categoricals

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

    def getOptions(self):
        return self.options

    def setOptions(self, value):
        self.options = value

    def select(self, features):
        self.df = self.df[features]
        return self

    def select_and_limit(self, features, limit):
        res = []
        if features:
            if limit > 0:
                res = self.df[features].head(limit)
            else:
                res = self.df[features]
        else:
            if limit > 0:
                res = self.df.head(limit)
            else:
                res = self.df

        return res.values.tolist()

    def sort(self, columns, ascending=True):
        self.df.sort_values(columns, ascending = ascending, inplace=True)

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

        #print(value)
        self.df.fillna(value, inplace=True)
        return self

    @staticmethod
    def encode_feature_list(list_features_arg):
        from urllib.parse import quote

        list_features = list_features_arg.copy()
        for idx, name in enumerate(list_features):
            encoded_name = quote(name)
            if encoded_name != name:
                list_features[idx] = encoded_name

        return list_features

    def encode_features(self):
        from urllib.parse import quote

        rename_cols = {}
        feature_names = self.columns

        for name in feature_names:
            encoded_name = quote(name)
            if encoded_name != name:
                rename_cols[name] = encoded_name

        self.df.rename(columns=rename_cols, inplace=True)

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

    def expandCategoricalFeatures(self, features):
        res = []
        for feature in features:
            if self.categoricals.get(feature):
                if self.categoricals[feature].get('columns'):
                    res.extend(self.categoricals[feature].get('columns'))
                else:
                    res.append(feature)
            else:
                res.append(feature)

        return res

    def getSummary(self):
        types_list = []
        columns_list = self.df.columns.get_values().tolist()
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
                stat_data.append({'column_name': cname, 'orig_datatype': ctype, 'datatype': ctype})

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

    def error_decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                logging.exception("DataSourceAPIPandas method: %s failed."%str(method))
                return {}

        return wrapper

    def getMetaFeatures(self, create_new_manifest=False):
        statistics = self.getStatistics(update_manifest=False)
        manifest = {'statistics': statistics}
        manifest['metafeatures'] = self._doMetaFeatures(statistics)
        #logging.info(manifest['metafeatures'])
        self._update_dataset_manifest(manifest, create_new_manifest)

        return manifest

    def filter_ex(self, params, conditions):
        cond_map = {'OR': '|', 'AND': "&"}

        query_text = ""
        for index, item in enumerate(params):
            cond_str = item.split(",")

            if conditions and index > 0:
                query_text += " " + cond_map[conditions[index-1]] + " " + " ".join(cond_str)
            else:
                query_text = " ".join(cond_str)

        # print(query_text)
        self.df.query(query_text, inplace=True)

        return self

    def search(self, params, features, limit):
        for key in params:
            tpl = params[key]
            val = tpl[0]
            op = tpl[1]

            if val == 'null':
                if op == '==':
                    query_text = key + "!=" + key
                else:
                    query_text = key + "==" + key
            else:
                query_text = key + " " + op + " " + str(val)

            self.df.query(query_text, inplace=True)

        return self.select_and_limit(features, limit)

    def calculateFeaturesCorrelation(self, model_features, target_feature):
        fields = self.dtypes_dict
        result = []
        cols_to_process = []

        if target_feature in fields and fields[target_feature] == 'string':
            self.convertToCategorical(target_feature, is_target=True)

        fields = self.dtypes_dict
        for col in model_features:
            if col in fields and fields[col] != 'string' and fields[col] != 'datetime':
                cols_to_process.append(col)

        if cols_to_process:
            res_corr = self.df[cols_to_process].corrwith(self.df[target_feature]).values
            for idx, col in enumerate(cols_to_process):
                if col != target_feature:
                    result.append( (col, format(res_corr[idx], '.2f') ) )

        manifest = {
            'correlation_to_target': result,
            'featureColumns': cols_to_process,
            'targetFeature': target_feature
        }

        self._update_dataset_manifest(manifest)
        return manifest

    def calculateAllFeaturesCorrelation(self, names):
        cols = self.columns
        cols_to_process = []
        result = []
        for col in names:
            if col in cols:
                cols_to_process.append(col)

        if cols_to_process:
            df_corr = self.df[cols_to_process].corr()
            result = self._convert_floats_to_str(df_corr)
            cols_to_process = df_corr.columns.get_values().tolist()

        manifest = {
            'correlation_matrix': result,
            'featureColumns': cols_to_process
        }

        self._update_dataset_manifest(manifest)
        return manifest

    def _isNumericType(self, col_type):
        if col_type.lower() == 'double' or col_type.lower() == 'float' or \
            col_type.lower() == 'integer' or col_type.lower() == 'boolean' or col_type.lower() == 'short' or col_type.lower() == 'byte' \
            or col_type.lower() == 'long' or col_type.lower() == 'decimal':
            return True

        return False

    def withJsonColumn(self, col_name, json_col_name, child_name, col_type):
        def get_json_value(json_value, child_name, col_type):
            result = []
            for item in json_value:
                try:
                    #print(item)
                    res = json.loads(item, object_hook=convertStringsToUTF8)
                    if col_type.lower() == 'double' or col_type.lower() == 'float':
                        result.append(float(res[child_name]))
                    elif col_type.lower() == 'integer' or col_type.lower() == 'boolean' or col_type.lower() == 'short' or col_type.lower() == 'byte' \
                        or col_type.lower() == 'long' or col_type.lower() == 'decimal':
                        result.append(int(res[child_name]))
                    else:
                        result.append(res[child_name])
                except Exception as e:
                    #logging.exception("withJsonColumn failed for child name: %s."%(child_name))

                    if self._isNumericType(col_type):
                        result.append(0)
                    else:
                        result.append("")

            return result

        try:
            self.df[col_name] = get_json_value(self.df[json_col_name], child_name, col_type)
        except Exception as e:
            raise Exception("Extract from json field '%s'.'%s' to '%s' of type '%s' failed: %s"%(col_name, json_col_name, child_name, col_type, str(e)))
        return self

    def withNumericColumn(self, col_name):
        import re

        if not col_name in self.columns:
            return

        non_decimal = re.compile(r'[^\d.]+')
        field_type = self._map_dtypes(self.df[col_name].dtype.name)

        try:
            if field_type == 'string':
                self.df[col_name] = self.df[col_name].str.replace(non_decimal, '').astype(float)
            else:
                self.df[col_name] = self.df[col_name].astype(float)
        except Exception as e:
            logging.exception("withNumericColumn failed.")

            raise Exception("Cannot convert field '%s' from type '%s' to '%s': %s"%(col_name,
                field_type, 'double', str(e)))
        return self

    def withBooleanColumn(self, col_name):
        import re

        if not col_name in self.columns:
            return

        field_type = self._map_dtypes(self.df[col_name].dtype.name)

        try:
            def convert_to_boolean(col_name, x):
                x_lower = x.lower()
                if x_lower in DataSourceAPIPandas.BOOLEAN_WORDS_TRUE:
                    return 1

                if x_lower in DataSourceAPIPandas.BOOLEAN_WORDS_FALSE:
                    return 0

                raise Exception("Cannot convert field '%s' with value '%s' to Boolean"%(col_name, x))

            if field_type == 'string':
                self.df[col_name] = self.df[col_name].apply(lambda x: convert_to_boolean(col_name, x))
            else:
                self.df[col_name] = self.df[col_name].astype(bool)

        except Exception as e:
            logging.exception("withNumericColumn failed.")

            raise Exception("Cannot convert field '%s' from type '%s' to '%s': %s"%(col_name,
                field_type, 'double', str(e)))
        return self

    def withColumn(self, col_name, expra):
        #self.df = self.df.withColumn(col_name, expr(expra))
        return self

    def withCustomColumn(self, col_name, eval_text):
        #self.df = self.df.withColumn(col_name, eval(eval_text))
        return self

    def _convert_floats_to_str(self, data, precision='.2f'):
        str_res = []
        if len(data.shape) > 1:
            for res_row in data.values:
                result = [format(res, precision) for res in res_row]
                str_res.append(result)
        else:
            str_res = [format(res, precision) for res in data.values]

        return str_res

    def _check_for_json(self, cname):
        rows = self.df[cname][(self.df[cname] != '[]') & (self.df[cname] != '{}')].values
        if rows is None or len(rows) == 0:
            return []
        else:
            row = rows[0]

        try:
            data = json.loads(row, object_hook=convertStringsToUTF8)
            children = []
            for key in data:
                name = str(key) + '_' + cname
                dtype = type(data[key]).__name__
                if dtype == 'unicode':
                    dtype = 'string'
                #cast_type = self.sparkTypes[dtype] + "Type()"

                # self.df = self.df.withColumn(name, get_json_object(
                #     self.df[cname], '$.%s' % str(key)).cast(eval(cast_type)))
                children.append({'column_name': name, 'orig_column_name': str(key), 'child': cname, 'orig_datatype': dtype, 'datatype': dtype})

            return children
        except Exception as e:
            return []

    @staticmethod
    def saveToFileFoldFunc(options, fold_idx, X_train, y_train, test_index, X_test, y_test):
        path = options['data_folds_path_prefix'] + "%d" % fold_idx + ".pkl.gz"
        # np.savez_compressed(
        # path, X_train=X_train, y_train=y_train, test_index=test_index, X_test=X_test, y_test=y_test)
        fsclient.save_object_to_file(
            {'X_train': X_train, 'y_train': y_train, 'test_index': test_index, 'X_test': X_test, 'y_test': y_test},
            path
        )
        return path

    @staticmethod
    def loadFoldFile_s(options, nFold=0, fold_path=None):
        if not fold_path:
            fold_path = str(options['data_folds_path'][nFold])
        # if 'data_folds_path' in options:
        #     fold_path = str(options['data_folds_path'][nFold])
        # else:
        #     fold_path = DataSourceAPIPandas.get_datacache_path_s(options, "traindata_fold")+ "%d.npz" % nFold

        # data_fold = np.load(fold_path)
        data_fold = fsclient.load_object_from_file(fold_path)

        return (data_fold['X_train'], data_fold['y_train'], data_fold['X_test'], data_fold['y_test'])

    def loadFoldFile(self, nFold=0, fold_path=None):
        return self.loadFoldFile_s(self.options, nFold, fold_path)

    def splitToFoldFiles(self, fold_name=None, test_data_index=None):
        if fold_name is None:
            fold_name="traindata_fold"

        #print(self.df)
        path = self._get_datacache_path(os.path.join(self.options.get('fold_group', ''), fold_name))
        fsclient.removeFile(path+"*", wild=True)
        self.options['data_folds_path_prefix'] = path

        return self.splitToFolds(DataSourceAPIPandas.saveToFileFoldFunc, test_data_index)

    @staticmethod
    def getFoldPath_s(options, nFold=0):
        return DataSourceAPIPandas.get_datacache_path_s(options, options.get('fold_group', '') + "/traindata_fold")+ "%d" % nFold + ".pkl.gz"

    def getFoldPath(self, nFold=0):
        return self.getFoldPath_s(self.options, nFold)

    def getFoldPaths(self):
        return [self.getFoldPath(nFold) for nFold in range(0, self.options.get('crossValidationFolds', 2))]

    def call_fold_func(self, fold_func, fold_idx, **kfold_func_args):
        fold_file = self.options['data_folds_path'][fold_idx]
        data_fold = fsclient.load_object_from_file(str(fold_file), self.options.get('use_local_cache', False))
        return fold_func(self.options, fold_idx, data_fold['X_train'], data_fold['y_train'],
                        data_fold['test_index'], data_fold['X_test'], data_fold['y_test'], **kfold_func_args)

    @staticmethod
    def get_datacache_path_s(options, suffix):
        if 'augerInfo' in options:
            path = options['augerInfo']["datacachePath"]
            fsclient.createFolder(path)

            return os.path.join(path, suffix)

        return ""

    def _get_datacache_path(self, suffix):
        return self.get_datacache_path_s(self.options, suffix)

    @staticmethod
    def oversampling_shuffling_augment_data(x, y, augmentations=2):
        xs, xn = [], []
        for i in range(augmentations):
            mask = y > 0
            x1 = x[mask].copy()
            ids = np.arange(x1.shape[0])
            for c in range(x1.shape[1]):
                np.random.shuffle(ids)
                x1[:, c] = x1[ids][:, c]
            xs.append(x1)

        for i in range(augmentations//2):
            mask = y == 0
            x1 = x[mask].copy()
            ids = np.arange(x1.shape[0])
            for c in range(x1.shape[1]):
                np.random.shuffle(ids)
                x1[:, c] = x1[ids][:, c]
            xn.append(x1)

        xs = np.vstack(xs)
        xn = np.vstack(xn)
        ys = np.ones(xs.shape[0])
        yn = np.zeros(xn.shape[0])
        x = np.vstack([x, xs, xn])
        y = np.concatenate([y, ys, yn])

        return x, y

    def update_options_by_dataset_statistics(self):
        transforms = []
        categoricals = []
        hashings = []
        timeseries = []
        selected_features = []
        target_feature = None
        binaryClassification = None
        minority_target_class = None
        datetimeFeatures = []

        #logging.info(self.options.get('dataset_statistics'))
        for item in self.options.get('dataset_statistics', {}).get('stat_data', []):
            if item.get('isTarget'):
                print(item)
                target_feature = item['column_name']
                if (self.options.get('model_type', '') == 'classification' or self.options.get('classification')):
                    binaryClassification = item.get('unique_values', 0) == 2

                    #Find minority target class
                    if item.get('value_counts'):
                        minority_target_class = list(item['value_counts'].keys())[0]
                        for name, counts in item['value_counts'].items():
                            if counts < item['value_counts'][minority_target_class]:
                                minority_target_class = name

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
        if minority_target_class is not None:
            self.options['minority_target_class'] = minority_target_class
            # if isinstance(self.options['minority_target_class'], bool):
            #     self.options['minority_target_class_pos'] = 1 if self.options['minority_target_class'] else 0

        if not 'datasource_transforms' in self.options:
            self.options['datasource_transforms'] = []

        self.options['datasource_transforms'] = [transforms]

        # if  'dataset_statistics' in self.options:
        #     del self.options['dataset_statistics']

        #logging.info(self.options)

    def getBooleanCategoricals(self, feature):
        res = {}
        values = []

        for item in self.options.get('dataset_statistics', {}).get('stat_data', []):
            if item['column_name'] == feature:
                if item['datatype'] == 'boolean':
                    for key in list(item.get('value_counts', {}).keys()):
                        if isinstance(key, str):
                            if key.lower() in self.BOOLEAN_WORDS_TRUE:
                                values.append(key)
                            else:
                                values.insert(0, key)
                        else:
                            values.append(key)
                break

        if values:
            res[feature] = {'categories': values}

        return res

    def transform(self, transforms, cache_to_file=True):
        ordered_trans = [[], [], [], []]
        for group in transforms:
            for item in group:
                if list(item.keys())[0] == 'withJsonColumn':
                    ordered_trans[0].append(item)
                elif list(item.keys())[0] == 'fillna':
                    ordered_trans[1].append(item)
                elif list(item.keys())[0] == 'filter_ex':
                    ordered_trans[2].append(item)
                else:
                    ordered_trans[3].append(item)

        #TODO: implement comparing lists
        # if len(self.transforms_log) == len(ordered_trans):
        #     return
        # if  cmp(self.transforms_log, ordered_trans) == 0:
        #     #logging.info("Same transformations.Skip transform")
        #     return

        if self.transforms_log != [[], [], [], []]:
            logging.info("New transformations.Re-load data")
            self.load(use_cache=False)

        for group in ordered_trans:
            for item in group:
                name = list(item.keys())[0]
                args = list(item.values())[0]
                getattr(self, name)(**args)
                if name == "convertToCategorical" and args.get('is_target', False) and self.categoricals.get(args.get('col_names')):
                    args['categories'] = self.categoricals[args.get('col_names')]['categories']

        self.transforms_log = ordered_trans

        if cache_to_file:
            path = self._get_datacache_path("transformations.json")
            fsclient.removeFile(path)
            fsclient.writeJSONFile(path, self.transforms_log, atomic=True)

            self.saveToCacheFile("data_transformed")

    @staticmethod
    def revertTargetCategories(results, transforms):
        target_categories = []
        for group in transforms:
            for item in group:
                name = list(item.keys())[0]
                args = list(item.values())[0]
                if name == "convertToCategorical" and args.get('is_target', False):
                    target_categories = args['categories']
                    break

        if len(target_categories) == 0:
            return results

        return map(lambda x: target_categories[int(x)], results)

    @staticmethod
    def revertCategories(results, categories):
        return map(lambda x: categories[int(x)], results)

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
        # for idx, item in enumerate(arff_data_data):
        #     arff_data_data[idx] = [pd.np.nan if x is None else x for x in item]

        if features is None or set(features) == set(columns):
            return zip(*arff_data_data)

        fset = remove_dups_from_list(features)
        return [
            [row[i] for row in arff_data_data] if c in fset else None
            for i, c in enumerate(columns)
        ]

def load_each_df_from_bin_file(model_path, files, features=None):
    for file in files:
        df = DataSourceAPIPandas.create_dataframe(
            os.path.join(model_path, "predictions", file['path']),
            None,
            features
        )

        yield (file, df)
