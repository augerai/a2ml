import os
import pandas as pd
import datetime
import math
import copy
import logging

from a2ml.api.utils import get_uid, convert_to_date, merge_dicts, fsclient
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.a2ml import A2ML, Context
from a2ml.api.roi.calculator import Calculator as RoiCalculator
from a2ml.api.roi.validator import Validator as RoiValidator
from a2ml.api.roi.validator import ValidationResult as RoiValidationResult
from a2ml.api.roi.interpreter import Interpreter as RoiInterpreter

from .model_helper import ModelHelper
from .probabilistic_counter import ProbabilisticCounter


class ModelReview(object):
    def __init__(self, params):
        self.model_id = params.get('hub_info', {}).get('pipeline_id')
        self.model_path = params.get('model_path')
        self.params = params

        if not self.model_path:
            self.model_path = ModelHelper.get_model_path(self.model_id, params['hub_info'].get('project_path'))

        self._load_options()


    # def get_actuals_statistic(self, date_from=None, date_to=None):
    #     count_actuals = self.count_actuals_by_prediction_id()
    #     performance_daily = self.score_model_performance_daily(date_from, date_to)
    #     distribution_chart_stats = self.distribution_chart_stats(date_from, date_to)

    #     return {
    #         'count_actuals': count_actuals,
    #         'performance_daily': performance_daily,
    #         'distribution_chart_stats': distribution_chart_stats
    #     }

    def _load_options(self):
        self.options_path = os.path.join(self.model_path, "options.json")
        self.options_file_exists = fsclient.is_file_exists(self.options_path)

        self.options = fsclient.read_json_file(self.options_path)

        if self.params.get('hub_info'):
            self.options['hub_info'] = self.params['hub_info']

        self.target_feature = self.options.get('targetFeature')
        self.original_features = self.options.get("originalFeatureColumns", [])


    def _do_score_actual(self, df_data, predicted_feature=None):
        ds_true = DataFrame({})

        ds_predict = DataFrame({})
        if predicted_feature:
            df_predicted_actual = df_data[[predicted_feature, 'a2ml_actual']].dropna()

            ds_true.df = df_predicted_actual.rename(columns={'a2ml_actual': self.target_feature})
            ds_predict.df = df_predicted_actual.rename(columns={predicted_feature: self.target_feature})
        else:
            ds_true.df = df_data[['a2ml_actual']].rename(columns={'a2ml_actual': self.target_feature})
            ds_predict.df = df_data[[self.target_feature]] # copy to prevent source data modification

        y_pred, _ = ModelHelper.preprocess_target_ds(self.model_path, ds_predict)
        y_true, _ = ModelHelper.preprocess_target_ds(self.model_path, ds_true)

        res = ModelHelper.calculate_scores(self.options, y_test=y_true, y_pred=y_pred, raise_main_score=False)

        roi = self._calculate_roi(df_data, predicted_feature)
        if roi != None:
            res['roi'] = roi

        return res

    def validate_roi_syntax(self, expressions):
        res = []
        known_vars = ["A", "P", "$" + self.target_feature] + list(map(lambda name: "$" + name, self.original_features))

        for expression in expressions:
            if len(expression) > 0:
                validator = RoiValidator(expression, known_vars=known_vars)
                validation_result = validator.validate(force_raise=False)
            else:
                validation_result = RoiValidationResult()

            res.append(
                {
                    "expression": expression,
                    "is_valid": validation_result.is_valid,
                    "error": validation_result.error,
                }
            )

        return res

    def _calculate_roi(self, df_data, predicted_feature=None):
        if not self.params.get('roi'):
            return None

        predicted_feature = predicted_feature or self.target_feature
        known_vars = [predicted_feature] + self.original_features

        vars_mapping = {
            "A": "a2ml_actual",
            "actual": "a2ml_actual",
            "P": predicted_feature,
            "prediction": predicted_feature,
        }

        for known_var in known_vars:
            vars_mapping["$" + known_var] = known_var

        calc = RoiCalculator(
            filter=self.params['roi']['filter'],
            revenue=self.params['roi']['revenue'],
            investment=self.params['roi']['investment'],
            known_vars=known_vars,
            vars_mapping=vars_mapping,
        )

        res = calc.calculate(df_data)
        return res["roi"]

    def add_external_model(self, target_column, scoring, task_type, binary_classification):
        ModelHelper.create_model_options_file(
            options_path=self.options_path,
            scoring=scoring,
            target_column=target_column,
            task_type=task_type,
            binary_classification=binary_classification,
        )

        self._load_options()

        return True

    def add_actuals(
        self, ctx, actuals_path=None, data=None, columns=None, external_model=False,
        actual_date=None, actual_date_column=None, actuals_id = None, return_count=False, provider='auger'
    ):
        ds_actuals = DataFrame.create_dataframe(actuals_path, data, features=columns)

        if external_model or self.options.get('external_model'):
            options = self.options.copy()

            if 'hub_info' in options:
                del options['hub_info']

            ModelHelper.update_model_options_file(
                options_path=self.options_path,
                options=options,
                ds_actuals=ds_actuals,
            )

            self._load_options()

        if not 'actual' in ds_actuals.columns:
            raise Exception("There is no 'actual' column in data")

        actuals_count = ds_actuals.count()
        ds_actuals.df.rename(columns={"actual": 'a2ml_actual'}, inplace=True)

        if provider is not None and not self.target_feature in ds_actuals.columns:
            missing_features = set(self.original_features) - set(ds_actuals.columns)
            if len(missing_features) > 0:
                missing_features = ', '.join(sorted(list(missing_features)))
                raise Exception(f'Missing features to make prediction: {missing_features}. Please, provide target \'{self.target_feature}\' or all training features to run predict.')

            logging.info("Actual data missing predicted value column: %s. Call predict with features from actual data: %s"%(self.target_feature, ds_actuals.columns))
            res = A2ML(ctx).predict(self.model_id, data=ds_actuals.df, provider=provider)

            if res['result']:
                ds_actuals.df[self.target_feature] = res['data']['predicted'][self.target_feature]
            else:
                raise Exception(res['data'])

        result = self._do_score_actual(ds_actuals.df)
        baseline_score = {}
        if "baseline_target" in ds_actuals.columns:
            baseline_score = self._do_score_actual(ds_actuals.df, "baseline_target")

        #logging.info("Actual result: %s", result)
        ds_actuals.df = ds_actuals.df.rename(columns={self.target_feature: 'a2ml_predicted'})
        ds_actuals.df = ds_actuals.df.rename(columns={'a2ml_actual': self.target_feature})

        if not actuals_id:
            actuals_id = get_uid()

        suffix = "full_data"
        if len(ds_actuals.columns) == 2:
            suffix = "no_features_data"

        if actual_date_column:
            ds_actuals.df[actual_date_column] = ds_actuals.df[actual_date_column].fillna(datetime.date.today()).apply(pd.to_datetime).dt.date

            uniq_dates = ds_actuals.df[actual_date_column].unique()
            uniq_dates.sort()

            for actual_date in uniq_dates:
                file_name = str(actual_date) + '_' + actuals_id + "_" + suffix + ".feather.zstd"
                df = DataFrame.create_dataframe(records=ds_actuals.df[ds_actuals.df[actual_date_column] == actual_date])
                df.saveToFeatherFile(os.path.join(self.model_path, "predictions", file_name))
        else:
            file_name = str(actual_date or datetime.date.today()) + '_' + actuals_id + "_" + suffix + ".feather.zstd"
            ds_actuals.saveToFeatherFile(os.path.join(self.model_path, "predictions", file_name))

        if return_count:
            return {'score': result, 'count': actuals_count, 'baseline_score': baseline_score}
        else:
            return result

    def delete_actuals(self, with_predictions=False, begin_date=None, end_date=None):
        if with_predictions and not begin_date and not end_date:
            self.clear_model_results_and_actuals()
        else:
            path_suffixes = ["actuals.feather.zstd", "data.feather.zstd"]

            if with_predictions:
                path_suffixes = [".feather.zstd"]

            for path_suffix in path_suffixes:
                for (curr_date, files) in ModelReview._prediction_files_by_day(self.model_path, begin_date, end_date, path_suffix):
                    for file in files:
                        path = file if type(file) == str else file['path']
                        fsclient.remove_file(path)

    def build_review_data(self, data_path=None, output=None, date_col=None):
        if not data_path:
            data_path = self.options['data_path']

        train_features = ModelHelper.get_train_features(self.options)
        ds_train = DataFrame.create_dataframe(data_path, features=train_features)

        all_files = fsclient.list_folder(
            os.path.join(self.model_path, "predictions/*_full_data.feather.zstd"),
            wild=True, remove_folder_name=False, meta_info=True
        )

        all_files.sort(key=lambda f: f['path'][0:10], reverse=True)

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
                ds_train.df = pd.concat([ds_train.df, ds_actuals.df], ignore_index=True)
                #ds_train.drop_duplicates()

        #ds_train.dropna()

        if not output:
            directory = os.path.dirname(data_path)
            file_name = os.path.basename(data_path).split('_review_')[0]
            output = os.path.join(directory, file_name + "_review_%s.parquet"%(get_uid()))

        ds_train.saveToFile(output)
        return output

    # date_from..date_to inclusive
    def score_model_performance_daily(self, date_from, date_to):
        #To support baseline_target
        features = None #[self.target_feature, 'a2ml_predicted']
        res = {}

        for (curr_date, files) in ModelReview._prediction_files_by_day(
                self.model_path, date_from, date_to, "*_data.feather.zstd"):
            df_actuals = DataFrame({})
            for (file, df) in DataFrame.load_from_files(files, features):
                df_actuals.df = pd.concat([df_actuals.df, df.df])

            if df_actuals.count() > 0:
                df_actuals.df.rename(columns={self.target_feature: 'a2ml_actual'}, inplace=True)
                df_actuals.df.rename(columns={'a2ml_predicted': self.target_feature}, inplace=True)

                scores = self._do_score_actual(df_actuals.df)

                baseline_score = {}
                if "baseline_target" in df_actuals.columns:
                    baseline_score = self._do_score_actual(df_actuals.df, "baseline_target")

                res[str(curr_date)] = {
                    'scores': scores,
                    'score_name': self.options.get('score_name'),
                    'review_metric': self.options.get('review_metric'),
                    'baseline_scores': baseline_score
                }

        return res

    def distribution_chart_stats(self, date_from, date_to):
        features = [self.target_feature, 'a2ml_predicted']
        features += self.options.get('originalFeatureColumns', [])
        categoricalFeatures = self.options.get('categoricalFeatures', [])
        mapper = {}
        mapper[self.target_feature] = 'actual_%s' % self.target_feature
        mapper['a2ml_predicted'] = 'predicted_%s' % self.target_feature

        actuals_stats = self._distribution_stats(
            date_from, date_to, "_*_data.feather.zstd", features, categoricalFeatures, mapper
        )

        if not self.options.get('data_path'):
            all_files = []
            date_stat = convert_to_date(date_to) - datetime.timedelta(days=1)
            for (curr_date, files) in ModelReview._prediction_files_by_day(self.model_path, None,
                date_stat, "_*_data.feather.zstd"):
                all_files += files

            base_stat = ModelReview._get_distribution_stats_files(all_files, features, categoricalFeatures, mapper)
            if base_stat:
                actuals_stats['base_stat'] = base_stat

        return actuals_stats

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

    @staticmethod
    def _get_distribution_stats_files(files, features, categoricalFeatures=[], feature_mapper={},
        feature_importances={}):

        if not files:
            return None

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
        for (file, df) in DataFrame.load_from_files(files):
            df_list.append(df)

        # First pass: calc sum and count in each column for average
        for df in df_list:
            for feature in features:
                if feature in df.columns:
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
            for feature in features:
                if 'average' in stats[feature] and feature in df.columns:
                    avg = stats[feature]['average']
                    stats[feature]['sq_sum'] += ((df.df[feature] - avg)**2).sum()

        # Calc std dev
        return ModelReview._calc_stddev_for_features(stats, features, feature_mapper)

    def _distribution_stats(self, date_from, date_to, path_suffix, features,
        categoricalFeatures=[], feature_mapper={}):
        res = {}
        feature_importances = self.get_feature_importances()

        for (curr_date, files) in ModelReview._prediction_files_by_day(self.model_path, date_from, date_to, path_suffix):

            stats = ModelReview._get_distribution_stats_files(files, features, categoricalFeatures, feature_mapper, feature_importances)
            # Calc std dev
            if stats:
                res[str(curr_date)] = stats

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
    def _get_first_date_from_files(path):
        all_files = fsclient.list_folder(path,
            wild=True, remove_folder_name=True, meta_info=False
        )
        first_date = None
        if all_files:
            all_files.sort(key=lambda f: f[0:10], reverse=False)
            idxDate = all_files[0].find("_")
            if idxDate:
                first_date = all_files[0][0:idxDate]

        return first_date

    @staticmethod
    def _prediction_files_by_day(model_path, date_from, date_to, path_suffix):
        if (date_from and not date_to):# or (not date_from and date_to):
            # TODO: list all files by suffix, sort them by prefix date and return range of files
            raise Exception("Arguments error: please provide both start and end dates or date_to only or do not pass any.")

        if date_from or date_to:
            if date_from:
                date_from = convert_to_date(date_from)
            else:
                date_from = ModelReview._get_first_date_from_files(
                    os.path.join(model_path, "predictions/*" + path_suffix))
                if not date_from:
                    return
                date_from = convert_to_date(date_from)

            curr_date = date_from
            date_to = convert_to_date(date_to)

            while curr_date <= date_to:
                path = os.path.join(model_path, "predictions/" + str(curr_date) + "*" + path_suffix)
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
    def _get_prediction_files(model_path, prediction_group_id=None):
        predictions_path = os.path.join(model_path, "predictions/*_results.feather.zstd")

        if prediction_group_id:
            predictions_path = os.path.join(model_path, f"predictions/*_{prediction_group_id}_results.feather.zstd")

        files = fsclient.list_folder(predictions_path, wild=True, remove_folder_name=False, meta_info=True)
        files.sort(key=lambda f: f['last_modified'], reverse=True)

        if len(files) == 0:
            raise Exception('there is no prediction results for this model in ' + predictions_path)

        return files
