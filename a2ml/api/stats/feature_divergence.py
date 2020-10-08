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
            X = np.copy(X)
            self.hist_ = []

            for i in range(X.shape[1]):
                values, counts = np.unique(X[:, i], return_counts=True)
                self.hist_.append({v: p for v, p in zip(values, counts / X.shape[0])})

            return self

        def score_samples(self, X, y=None):
            X = np.copy(X)
            res = np.zeros_like(X, dtype=float)

            for i in range(X.shape[1]):
                for v, p in self.hist_[i].items():
                    res[X[:, i] == v, i] = p

            return np.sum(np.log(res), axis=1)

    class DensityEstimation:
        def __init__(self, num_cols: list = None, cat_cols: list = None):
            self.num_cols = [] if num_cols is None else num_cols
            self.cat_cols = [] if cat_cols is None else cat_cols

        def fit(self, X, y=None):
            if self.num_cols:
                self.cont_ = GaussianMixture(n_components=3, covariance_type="diag").fit(X[self.num_cols])

            if self.cat_cols:
                self.cat_ = FeatureDivergence.Histogram().fit(X[self.cat_cols])

            return self

        def score(self, X, y=None):
            num_score = self.cont_.score_samples(X[self.num_cols]) if self.cont_ is not None else np.zeros(X.shape[0])
            cat_score = self.cat_.score_samples(X[self.cat_cols]) if self.cat_ is not None else np.zeros(X.shape[0])

            return np.mean(num_score + cat_score)

    def __init__(self, params):
        self.params = params
        self.experiment_session = params['hub_info']['experiment_session']
        self.stat_data = self.experiment_session.get('dataset_statistics', {}).get('stat_data', [])

    def build_and_save_model(self):
        evaluation_options = self.experiment_session.get('model_settings', {}).get('evaluation_options')
        data_path = evaluation_options['data_path']

        df = DataFrame.create_dataframe(data_path=data_path, features=self._get_density_features())
        model = self.DensityEstimation(self._get_numerical_features(), self._get_categorical_features())
        model.fit(df.df)

        path = self._get_divergence_model_path()
        fsclient.save_object_to_file(model, path)
        return path

    def score_divergence_daily(self, model_path, date_from=None, date_to=None, divergence_model_name=None):
        model = fsclient.load_object_from_file(self._get_divergence_model_path(divergence_model_name))
        features = self._get_density_features()
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
                    daily_df.df = pd.concat([daily_df.df, df.df], ignore_index=True)
                else:
                    daily_df = df

            if daily_df != None:
                res[str(curr_date)] = model.score(daily_df.df)

        return res

    def _get_divergence_model_path(self, divergence_model_name=None):
        experiment_session_path = ModelHelper.get_experiment_session_path(self.params)
        return os.path.join(experiment_session_path, divergence_model_name or self.MODEL_NAME)


    def _get_density_features(self):
        predicate = lambda col: self._is_column_used(col) and not self._is_column_ignored(col)
        return [col['column_name'] for col in self.stat_data if predicate(col)]

    def _get_numerical_features(self):
        predicate = lambda col: self._is_column_used(col) and self._is_column_numerical(col)
        return [col['column_name'] for col in self.stat_data if predicate(col)]

    def _get_categorical_features(self):
        predicate = lambda col: self._is_column_used(col) and self._is_column_categorical(col)
        return [col['column_name'] for col in self.stat_data if predicate(col)]

    def _is_column_used(self, column):
        return column['isTarget'] or column['use']

    def _is_column_numerical(self, column):
        return column['datatype'] in self.NUMERIC_TYPES

    def _is_column_categorical(self, column):
        return column['datatype'] in self.CATEGORICAL_TYPES

    def _is_column_ignored(self, column):
        return column['datatype'] in self.IGNORED_TYPES
