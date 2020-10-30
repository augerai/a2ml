import numpy as np
import pandas as pd
import os

from sklearn.mixture import GaussianMixture

from a2ml.api.model_review.model_helper import ModelHelper
from a2ml.api.model_review.model_review import ModelReview
from a2ml.api.utils import fsclient
from a2ml.api.utils.dataframe import DataFrame


class FeatureDivergence:
    NUMERIC_TYPES = {
        'integer',
        'double',
    }

    CATEGORICAL_TYPES = {
        'categorical',
        'hashing',
        'boolean',
    }

    IGNORED_TYPES = {
        'datetime',
        'timeseries',
    }

    MODEL_NAME = 'density_model.pkl'

    class Histogram:
        def fit(self, X, y=None):
            X = X.replace([np.inf, -np.inf], np.nan).dropna()
            X = np.copy(X)
            self.hist_ = []

            for i in range(X.shape[1]):
                values, counts = np.unique(X[:, i], return_counts=True)
                self.hist_.append(
                    {v: p for v, p in zip(values, counts / X.shape[0])})

            return self

        def score_samples(self, X, y=None):
            X = X.replace([np.inf, -np.inf], np.nan).dropna()
            X = np.copy(X)
            res = np.zeros_like(X, dtype=float)

            for i in range(X.shape[1]):
                for v, p in self.hist_[i].items():
                    res[X[:, i] == v, i] = p

            return np.sum(np.log(res), axis=1)

    class DensityEstimator:
        def __init__(self, num_cols: list = None, cat_cols: list = None):
            self.num_cols = num_cols or []
            self.cat_cols = cat_cols or []

        def fit(self, X, y=None):
            X = X.replace([np.inf, -np.inf], np.nan).dropna()

            self.cont_ = None
            self.cat_ = None

            if self.num_cols:
                self.cont_ = GaussianMixture(
                    n_components=3, covariance_type="diag").fit(X[self.num_cols])

            if self.cat_cols:
                self.cat_ = FeatureDivergence.Histogram().fit(X[self.cat_cols])

            return self

        def score(self, X, y=None):
            X = X.replace([np.inf, -np.inf], np.nan).dropna()
            num_score = self.cont_.score_samples(
                X[self.num_cols]) if self.cont_ is not None else np.zeros(X.shape[0])
            cat_score = self.cat_.score_samples(
                X[self.cat_cols]) if self.cat_ is not None else np.zeros(X.shape[0])

            return np.mean(num_score + cat_score)

    class DensityEstimatorPerFeature:
        def __init__(self, features, numerical_features, categorical_features):
            self.features = features
            self.numerical_features = set(numerical_features)
            self.categorical_features = set(categorical_features)
            self.models = {}
            self.base_values = {}

        def fit(self, df):
            for feature in self.features:
                model = None

                if feature in self.numerical_features:
                    model = FeatureDivergence.DensityEstimator([feature], [])

                if feature in self.categorical_features:
                    model = FeatureDivergence.DensityEstimator([], [feature])

                if model:
                    model.fit(df)
                    self.models[feature] = model
                    self.base_values[feature] = model.score(df)

        def score(self, feature, df):
            if feature in self.models:
                return self.models[feature].score(df) / self.base_values[feature]
            else:
                raise KeyError("Feature: '" + feature +
                               "'' is not in the model")

    class ModelIsNotReadyError(Exception):
        pass

    def __init__(self, params):
        self.params = params
        self.experiment_session = params['hub_info']['experiment_session']
        self.stat_data = self.experiment_session.get(
            'dataset_statistics', {}).get('stat_data', [])

    def build_and_save_model(self, divergence_model_name=None):
        df = DataFrame.create_dataframe(
            data_path=self.params['data_path'], features=self._get_density_features())

        model = self.DensityEstimatorPerFeature(
            self._get_density_features(),
            self._get_numerical_features(),
            self._get_categorical_features()
        )
        model.fit(df.df)

        path = self._get_divergence_model_path(divergence_model_name)
        fsclient.save_object_to_file(model, path)
        return path

    def score_divergence_daily(self, date_from=None, date_to=None, divergence_model_name=None, top_n=None):
        model_path = ModelHelper.get_model_path(params=self.params)
        div_model_path = self._get_divergence_model_path(divergence_model_name)

        if not fsclient.is_file_exists(div_model_path):
            raise self.ModelIsNotReadyError(div_model_path)

        divergence_model = fsclient.load_object_from_file(div_model_path)
        features = self._get_density_features()

        features_source = features
        feature_importances = self._get_most_important_features(
            features, top_n)

        if top_n:
            features_source = feature_importances.keys()

        res = {}

        for (curr_date, files) in ModelReview._prediction_files_by_day(
            model_path,
            date_from,
            date_to,
            "_*_actuals.feather.zstd"
        ):
            daily_df = None
            for (file, df) in DataFrame.load_from_files(files, features):
                if daily_df != None:
                    daily_df.df = pd.concat(
                        [daily_df.df, df.df], ignore_index=True)
                else:
                    daily_df = df

            if daily_df != None:
                sub_res = {}

                for feature in features_source:
                    sub_res[feature] = divergence_model.score(
                        feature, daily_df.df)

                res[str(curr_date)] = sub_res

        return {
            'divergence': res,
            'importance': feature_importances,
        }

    def _get_most_important_features(self, features, top_n):
        features_set = set(features)
        res = ModelReview(self.params).get_feature_importances()
        # Get feature importance for our features
        res = {key: res.get(key) for key in features_set}
        res = [[res[k], k] for k in res if res.get(k) != None]
        # Sort by importance desc
        res.sort(reverse=True)
        # Return top features by importance dict(feature => importance)
        return dict(map(lambda x: [x[1], x[0]], res[0:top_n]))

    def _get_divergence_model_path(self, divergence_model_name=None):
        experiment_session_path = ModelHelper.get_experiment_session_path(
            self.params)
        return os.path.join(experiment_session_path, divergence_model_name or self.MODEL_NAME)

    def _get_density_features(self):
        def predicate(col): return self._is_column_used(
            col) and not self._is_column_ignored(col)
        return [col['column_name'] for col in self.stat_data if predicate(col)]

    def _get_numerical_features(self):
        def predicate(col): return self._is_column_used(
            col) and self._is_column_numerical(col)
        return [col['column_name'] for col in self.stat_data if predicate(col)]

    def _get_categorical_features(self):
        def predicate(col): return self._is_column_used(
            col) and self._is_column_categorical(col)
        return [col['column_name'] for col in self.stat_data if predicate(col)]

    def _is_column_used(self, column):
        return column['isTarget'] or column['use']

    def _is_column_numerical(self, column):
        return column['datatype'] in self.NUMERIC_TYPES

    def _is_column_categorical(self, column):
        return column['datatype'] in self.CATEGORICAL_TYPES

    def _is_column_ignored(self, column):
        return column['datatype'] in self.IGNORED_TYPES
