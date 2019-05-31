import os
import json
import pandas
from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.utils.exception import AugerException
from a2ml.api.auger.hub.pipeline import AugerPipelineApi


class AugerPredict(AugerBase):
    """Predict using deployed Auger Pipeline."""

    def __init__(self, ctx):
        super(AugerPredict, self).__init__(ctx)

    @AugerBase._error_handler
    def predict(self, filename, deployed_model_id, threshold=None):
        # verify avalability of auger credentials
        self.credentials.verify()

        self.ctx.log('Predicting on data in %s' % filename)

        df = self._load_dataframe(filename)

        pipeline_api = AugerPipelineApi(None, deployed_model_id)
        predictions = pipeline_api.predict(
            df.values.tolist(), df.columns.get_values().tolist(), threshold)
        # print(pandas.DataFrame.from_dict(predictions))

        predictions_filename = \
            os.path.splitext(filename)[0] + "-predicted.csv"
        self._save_to_csv(predictions_filename, predictions)
        self.ctx.log('Predictions stored in %s' % predictions_filename)

    def _load_dataframe(self, filename, features=None, nrows=None):
        try:
            df = self._read_csv(filename, ',', features, nrows)
        except Exception as e:
            df = self._read_csv(filename, '|', features, nrows)

        target = self.ctx.config['config'].get('target', None)
        features = df.columns.get_values().tolist()
        if target in features:
            df.drop(columns=[target], inplace=True)

        return df

    def _save_to_csv(self, filename, data):
        df = pandas.DataFrame.from_dict(data)
        df.to_csv(filename, index=False, encoding='utf-8')

    def _read_csv(self, filename, sep, features=None, nrows=None):
        return pandas.read_csv(filename,
            encoding='utf-8', escapechar="\\", usecols=features,
            na_values=['?'], header=0, prefix=None, sep=sep,
            nrows=nrows, low_memory=False, compression='infer')
