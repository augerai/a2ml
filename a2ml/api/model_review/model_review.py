import os
import pandas as pd
import datetime
import math
import copy
import logging

from a2ml.api.utils import get_uid, convert_to_date, merge_dicts, fsclient
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.a2ml import A2ML, Context

from .model_helper import ModelHelper
from .probabilistic_counter import ProbabilisticCounter


class ModelReview(object):
    def __init__(self, params):
        self.model_id = params.get('hub_info', {}).get('pipeline_id')
        self.model_path = params.get('model_path')

        if not self.model_path:
            self.model_path = ModelHelper.get_model_path(self.model_id, params['hub_info'].get('project_path'))

        self.options = fsclient.read_json_file(os.path.join(self.model_path, "options.json"))
        if params.get('hub_info'):
            self.options['hub_info'] = params['hub_info']

        self.target_feature = self.options.get('targetFeature')
        self.original_features = self.options.get("originalFeatureColumns")

    # def get_actuals_statistic(self, date_from=None, date_to=None):
    #     count_actuals = self.count_actuals_by_prediction_id()
    #     performance_daily = self.score_model_performance_daily(date_from, date_to)
    #     distribution_chart_stats = self.distribution_chart_stats(date_from, date_to)

    #     return {
    #         'count_actuals': count_actuals,
    #         'performance_daily': performance_daily,
    #         'distribution_chart_stats': distribution_chart_stats
    #     }

    def _do_score_actual(self, df_data):
        ds_true = DataFrame({})
        ds_true.df = df_data[['a2ml_actual']].rename(columns={'a2ml_actual':self.target_feature})

        ds_predict = DataFrame({})
        ds_predict.df = df_data[[self.target_feature]] # copy to prevent source data modification

        y_pred, _ = ModelHelper.preprocess_target_ds(self.model_path, ds_predict)
        y_true, _ = ModelHelper.preprocess_target_ds(self.model_path, ds_true)

        return ModelHelper.calculate_scores(self.options, y_test=y_true, y_pred=y_pred, raise_main_score=False)

    # prediction_group_id - prediction group for these actuals
    # primary_prediction_group_id - means that prediction_group_id is produced by a candidate model
    # and prediction rows id should be matched with actuals using primary_prediction_group
    def add_actuals(self, ctx, actuals_path=None, actual_records=None,
            prediction_group_id=None, primary_prediction_group_id=None, primary_model_path=None,
            actual_date=None, actuals_id = None, return_count=False):

        features = None
        list_records = actual_records and type(actual_records[0]) == list

        if actuals_path or list_records:
            features = ['actual'] + self.original_features + [self.target_feature]

        try:
            ds_actuals = DataFrame.create_dataframe(actuals_path, actual_records, features=features)
        except ValueError:
            # Predicted value of target is optional last item in features
            # data withouttarget column, remote it and reload data
            features.pop()
            ds_actuals = DataFrame.create_dataframe(actuals_path, actual_records, features=features)

        missed_features = set(self.original_features) - set(ds_actuals.columns)

        if missed_features:
            missed_features = list(missed_features)
            missed_features.sort()
            raise Exception("There is a missed features in data: " + ", ".join(list(missed_features)))

        if not 'actual' in ds_actuals.columns:
            raise Exception("There is no 'actual' column in data")

        actuals_count = ds_actuals.count()
        ds_actuals.df.rename(columns={"actual": 'a2ml_actual'}, inplace=True)

        if not self.target_feature in ds_actuals.columns:
            res = A2ML(ctx).predict(None, self.model_id, data=ds_actuals.df, provider='auger')

            if res['result']:
                ds_actuals.df[self.target_feature] = res['data']['predicted'][self.target_feature]
            else:
                raise Exception(res['data'])

        result = self._do_score_actual(ds_actuals.df)

        ds_actuals.df = ds_actuals.df.rename(columns={self.target_feature: 'a2ml_predicted'})
        ds_actuals.df = ds_actuals.df.rename(columns={'a2ml_actual':self.target_feature})

        if not actuals_id:
            actuals_id = get_uid()

        file_name = str(actual_date or datetime.date.today()) + '_' + actuals_id + "_actuals.feather.zstd"
        ds_actuals.saveToFeatherFile(os.path.join(self.model_path, "predictions", file_name))

        if return_count:
            return {'score': result, 'count': actuals_count}
        else:
            return result

    def delete_actuals(self, with_predictions=False, begin_date=None, end_date=None):
        if with_predictions and not begin_date and not end_date:
            self.clear_model_results_and_actuals()
        else:
            path_suffix = "_*_actuals.feather.zstd"
            if with_predictions:
                path_suffix = "_*_*.feather.zstd"

            for (curr_date, files) in ModelReview._prediction_files_by_day(self.model_path, begin_date, end_date, path_suffix):
                for file in files:
                    path = file if type(file) == str else file['path']
                    fsclient.remove_file(path)

    def build_review_data(self, data_path=None, output=None, date_col=None):
        if not data_path:
            data_path = self.options['data_path']

        train_features = ModelHelper.get_train_features(self.options)
        ds_train = DataFrame.create_dataframe(data_path, features=train_features)

        all_files = fsclient.list_folder(os.path.join(self.model_path, "predictions/*_actuals.feather.zstd"),
            wild=True, remove_folder_name=False, meta_info=True)
        all_files.sort(
            key=lambda f: f['last_modified'],
            reverse=True
        )
        if date_col and date_col in train_features:
            new_files = []
            try:
                start_date = convert_to_date(ds_train.df[date_col].max())
                logging.info("build_review_data with date_col: %s = %s"%(date_col,start_date))

                for idx, file in enumerate(all_files):
                    file_date = os.path.basename(file['path']).split("_")[0]
                    if convert_to_date(file_date) <= start_date:
                        continue

                    new_files.append(file)

                all_files = new_files
            except Exception as e:
                logging.error("Getting latest date from data path %s failed: %s"%(data_path,e))

        logging.info("build_review_data adding files: %s"%all_files)
        for (file, ds_actuals) in DataFrame.load_from_files(all_files):
            if not ds_actuals.df.empty:
                ds_actuals.drop(['a2ml_predicted'])
                ds_train.df = pd.concat([ds_train.df, ds_actuals.df[ds_train.columns]], ignore_index=True)
                ds_train.drop_duplicates()

        if not output:
            file_name = os.path.splitext(data_path)[0]
            if '_review_' in file_name:
                idx = file_name.find('_review_')
                if idx > 0:
                    file_name = file_name[:idx]

            output =  file_name + "_review_%s.parquet"%(get_uid())

        ds_train.saveToFile(output)
        return output

    # def count_actuals_by_prediction_id(self, date_from=None, date_to=None):
    #     res = {}
    #     features = ['prediction_group_id', 'prediction_id', self.target_feature]
    #     counter = ProbabilisticCounter()

    #     all_files = fsclient.list_folder(
    #         os.path.join(self.model_path, "predictions/*_actuals.feather.zstd"),
    #         wild=True,
    #         remove_folder_name=False,
    #         meta_info=False
    #     )

    #     #print(all_files)

    #     for (curr_date, files) in ModelReview._prediction_files_by_day(
    #         self.model_path, date_from, date_to, "_*_actuals.feather.zstd"):

    #         for (file, df) in DataFrame.load_from_files(files, features):
    #             ModelReview._remove_duplicates_by(df, 'prediction_id', counter)

    #             agg = df.df.groupby(['prediction_group_id', 'prediction_id']).count()
    #             agg[self.target_feature] = 1 # exclude duplication prediction_id's inside groups
    #             agg = agg.groupby('prediction_group_id').count()

    #             for prediction_group_id, row, in agg.iterrows():
    #                 count = row[0]

    #                 if prediction_group_id not in res:
    #                     res[prediction_group_id] = count
    #                 else:
    #                     res[prediction_group_id] = res[prediction_group_id] + count

    #     return res

    def statistic_daily(self, date_from, date_to):
        features = ['prediction_id', self.target_feature]
        res = {}

        for (curr_date, files) in ModelReview._prediction_files_by_day(
                self.model_path, date_from, date_to, "_*_actuals.feather.zstd"):
            df_actuals = DataFrame({})
            for (file, df) in DataFrame.load_from_files(files, features):
                df_actuals.df = pd.concat([df_actuals.df, df.df])

            res[str(curr_date)] = {}
            res[str(curr_date)]['actuals_count'] = df_actuals.count()

            if df_actuals.count()>0:
                df_actuals.drop_duplicates(['prediction_id'])
            res[str(curr_date)]['actuals_count_unique'] = df_actuals.count()

        for (curr_date, files) in ModelReview._prediction_files_by_day(
                self.model_path, date_from, date_to, "_*_results.feather.zstd"):
            df_results = DataFrame({})
            for (file, df) in DataFrame.load_from_files(files, features):
                df_results.df = pd.concat([df_results.df, df.df])

            if not str(curr_date) in res:
                res[str(curr_date)] = {}

            res[str(curr_date)]['predictions_count'] = df_results.count()
            if df_results.count()>0:
                df_results.drop_duplicates(['prediction_id'])
            res[str(curr_date)]['predictions_count_unique'] = df_results.count()

        return res

    # date_from..date_to inclusive
    def score_model_performance_daily(self, date_from, date_to):
        features = ['prediction_id', self.target_feature, 'a2ml_predicted']
        res = {}

        for (curr_date, files) in ModelReview._prediction_files_by_day(
                self.model_path, date_from, date_to, "_*_actuals.feather.zstd"):
            df_actuals = DataFrame({})
            for (file, df) in DataFrame.load_from_files(files, features):
                df_actuals.df = pd.concat([df_actuals.df, df.df])

            if df_actuals.count() > 0:
                df_actuals.drop_duplicates(['prediction_id'])

                df_actuals.df.rename(columns={self.target_feature: 'a2ml_actual'}, inplace=True)
                df_actuals.df.rename(columns={'a2ml_predicted': self.target_feature}, inplace=True)

                scores = self._do_score_actual(df_actuals.df)
                res[str(curr_date)] = scores[self.options.get('score_name')]

        return res

    def distribution_chart_stats(self, date_from, date_to):
        features = [self.target_feature]
        categoricalFeatures = self.options.get('categoricalFeatures', [])
        mapper = {}
        mapper[self.target_feature] = 'actual_%s'%self.target_feature

        actuals_stats = self._distribution_stats(
            date_from, date_to, "_*_actuals.feather.zstd", features, categoricalFeatures, mapper
        )

        features += self.options.get('originalFeatureColumns', [])
        mapper[self.target_feature] = 'predicted_%s'%self.target_feature
        features_stats = self._distribution_stats(
            date_from, date_to, "_*_results.feather.zstd", features, categoricalFeatures, mapper
        )

        return merge_dicts(features_stats, actuals_stats)

    def set_support_review_model_flag(self, flag_value):
        path = os.path.join(self.model_path, "options.json")

        self.options['support_review_model'] = bool(flag_value)

        fsclient.remove_file(path)
        fsclient.write_json_file(path, self.options, atomic=True)

    def remove_model(self):
        fsclient.remove_folder(self.model_path)
        return True

    def clear_model_results_and_actuals(self):
        fsclient.remove_folder(os.path.join(self.model_path, "predictions"))
        return True

    def _distribution_stats(self, date_from, date_to, path_suffix, features,
        categoricalFeatures=[], feature_mapper={}):
        res = {}
        feature_importances = self.get_feature_importances()
        counter = ProbabilisticCounter()
        second_pass_counter = ProbabilisticCounter()

        for (curr_date, files) in ModelReview._prediction_files_by_day(self.model_path, date_from, date_to, path_suffix):
            stats = {}

            for feature in features:
                stats[feature] = {
                    'count': 0,
                    'sum': 0,
                    'sq_sum': 0,
                    'dist': None,
                    'imp': feature_importances.get(feature, 0)
                }

            df_list = []
            for (file, df) in DataFrame.load_from_files(files, features + ['prediction_id']):
                ModelReview._remove_duplicates_by(df, 'prediction_id', counter)

                df_list.append(df)

            # First pass: calc sum and count in each column for average
            for df in df_list:
                for feature in features:
                    stats[feature]['count'] += df.df[feature].count()

                    if df.df[feature].dtype.name in ['category', 'string', 'object'] or \
                        feature in categoricalFeatures:
                        stats[feature]['dist'] = merge_dicts(
                            stats[feature]['dist'] or {},
                            dict(df.df[feature].value_counts()),
                            lambda v, ov: v + ov
                        )
                    else:
                        stats[feature]['sum'] += df.df[feature].sum()

            # Calc average
            for feature in features:
                if stats[feature]['count'] > 0 and stats[feature]['dist'] == None:
                    stats[feature]['average'] = stats[feature]['sum'] / stats[feature]['count']

            # Second pass: sum of squares of value and average for std dev
            for df in df_list:
                ModelReview._remove_duplicates_by(df, 'prediction_id', second_pass_counter)

                for feature in features:
                    if 'average' in stats[feature]:
                        avg = stats[feature]['average']
                        stats[feature]['sq_sum'] += ((df.df[feature] - avg)**2).sum()

            # Calc std dev
            if len(files) > 0:
                res[str(curr_date)] = ModelReview._calc_stddev_for_features(stats, features, feature_mapper)

        return res

    def get_feature_importances(self):
        cache_path = ModelHelper.get_metric_path(self.options)

        importance_data = None
        if cache_path:
            importance_data = fsclient.read_json_file(os.path.join(cache_path, "metrics.json")).get('feature_importance_data')
            if not importance_data:
                importance_data = fsclient.read_json_file(os.path.join(cache_path, "metric_names_feature_importance.json")).get('feature_importance_data')

        if importance_data:
            if importance_data.get('features_orig') and importance_data.get('scores_orig'):
                return dict(zip(importance_data['features_orig'], importance_data['scores_orig']))
            else:
                return dict(zip(importance_data['features'], importance_data['scores']))
        else:
            logging.warn("No feature importance in cache: for model %s" % (cache_path))
            return {}

    @staticmethod
    def _calc_stddev_for_features(stats, features, feature_mapper):
        res = {}

        for feature in features:
            count = stats[feature]['count']

            if count > 0:
                feature_key = feature_mapper.get(feature, feature)
                if 'average' in stats[feature]:
                    res[feature_key] = {
                        "avg": stats[feature]['average'],
                        "std_dev": math.sqrt(stats[feature]['sq_sum'] / (count - 1)) if count > 1 else 0
                    }
                else:
                    res[feature_key] = { 'dist': stats[feature]['dist'] }

                res[feature_key]['imp'] = round(stats[feature]['imp'], 6)

        return res

    @staticmethod
    def _prediction_files_by_day(model_path, date_from, date_to, path_suffix):
        if (date_from and not date_to) or (not date_from and date_to):
            # TODO: list all files by suffix, sort them by prefix date and return range of files
            raise Exception("Arguments error: please provide both start and end dates or do not pass any.")

        if date_from:
            date_from = convert_to_date(date_from)
            date_to = convert_to_date(date_to)

            curr_date = date_from

            while curr_date <= date_to:
                path = os.path.join(model_path, "predictions/" + str(curr_date) + path_suffix)
                files = fsclient.list_folder(path, wild=True, remove_folder_name=False, meta_info=False)
                yield (curr_date, files)
                curr_date += datetime.timedelta(days=1)
        else:
            path = os.path.join(model_path, "predictions/" + "*" + path_suffix)
            files = fsclient.list_folder(path, wild=True, remove_folder_name=False, meta_info=False)
            yield ("today", files)

    @staticmethod
    def _remove_duplicates_by(df, column_name, counter):
        dup_flag_column_name = '__duplicate'
        df.df[dup_flag_column_name] = df.df[column_name]
        df.df[dup_flag_column_name] = df.df[dup_flag_column_name].apply(lambda uid: not counter.add(uid))

        df.df = df.df[df.df[dup_flag_column_name] == False]
        df.drop([dup_flag_column_name])

        return df

    @staticmethod
    def _map_primary_prediction_id_to_candidate(prediction_id, primary_prediction_id, candidate_prediction_id):
        primary_prediction_id = primary_prediction_id.rename('primary_prediction_id')

        if len(primary_prediction_id) != len(candidate_prediction_id):
            raise Exception("Primary prediction's rows count doesn't match candidate's one")

        mapper = {}
        for (i, row) in pd.concat([primary_prediction_id, candidate_prediction_id], axis=1).iterrows():
            mapper[row['primary_prediction_id']] = row['prediction_id']


        return prediction_id.map(mapper)

    @staticmethod
    def _get_prediction_files(model_path, prediction_group_id=None):
        predictions_path = os.path.join(model_path, "predictions/*_results.feather.zstd")

        if prediction_group_id:
            predictions_path = os.path.join(model_path, f"predictions/*_{prediction_group_id}_results.feather.zstd")

        files = fsclient.list_folder(predictions_path, wild=True, remove_folder_name=False, meta_info=True)
        files.sort(key=lambda f: f['last_modified'], reverse=True)

        if len(files) == 0:
            raise Exception('there is no prediction results for this model in ' + predictions_path)

        return files
