import json
from a2ml.api.auger.hub.base import AugerBaseApi
from a2ml.api.auger.hub.base import AugerException
from a2ml.api.auger.hub.data_source import AugerDataSourceApi
from a2ml.api.auger.hub.experiment_session import AugerExperimentSessionApi

MODEL_TYPES = ['classification', 'regression', 'timeseries']

class AugerExperimentApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Experiment Api."""

    def __init__(self,
        hub_client, project_api, experiment_name=None, experiment_id=None):
        super(AugerExperimentApi, self).__init__(
            hub_client, project_api, experiment_name, experiment_id)
        assert project_api is not None, 'Project must be set for Experiment'

    def run(self):
        experiment_session_api = \
            AugerExperimentSessionApi(self.hub_client, self)
        experiment_session_api.create()
        experiment_session_api.run()

    def create(self, data_source_name):
        assert data_source_name is not None, \
            'Data Source Name is required to create Experiment'

        data_source_api = AugerDataSourceApi(
            self.hub_client, self.parent_api, data_source_name)
        data_source_properties = data_source_api.properties()

        if not self.object_name:
            self.object_name = self._get_uniq_object_name(
                data_source_name, '-experiment')

        return self._call_create({
            'name': self.object_name,
            'project_id': self.parent_api.object_id,
            'data_path': data_source_properties.get('url')})

    def get_experiment_settings(self):
        config = self.hub_client.get_config('config')
        auger_config = self.hub_client.get_config('auger')

        model_type = config.get('model_type', '')
        if not model_type in MODEL_TYPES:
            raise AugerException('Model type should be %s' % \
                '|'.join(MODEL_TYPES))
        target = config.get('target', '')
        exclude = config.get('exclude', [])

        options = {
            'targetFeature': None,
            'featureColumns': [],
            'categoricalFeatures': [],
            'timeSeriesFeatures': [],
            'binaryClassification': False,
            'labelEncodingFeatures':
                auger_config.get('experiment/label_encoding', []),
            'crossValidationFolds':
                auger_config.get('experiment/cross_validation_folds', 5),
            'max_total_time_mins':
                auger_config.get('experiment/max_total_time', 60),
            'max_eval_time_mins':
                auger_config.get('experiment/max_eval_time', 1),
            'max_n_trials':
                auger_config.get('experiment/max_n_trials', 1000),
            'use_ensemble':
                auger_config.get('experiment/use_ensemble', True),
            'classification':
                True if model_type == 'classification' else False,
            'scoring':
                auger_config.get('experiment/metric',
                    'f1_macro' if model_type == 'classification' else 'r2')
        }

        data_source_id = self.properties()['project_file_id']
        data_source_api = AugerDataSourceApi(
            self.hub_client, self.parent_api, None, data_source_id)
        data_source_properties = data_source_api.properties()
        stats = data_source_properties['statistics']

        self._fill_data_options(options, stats, target, exclude)

        if options['targetFeature'] is None:
            raise AugerException('Please set target to build model.')

        if model_type is not 'timeseries':
            options['timeSeriesFeatures'] = []
        else:
            time_series = auger_config.get('experiment/time_series', None)
            if time_series:
                options['timeSeriesFeatures'] = [time_series]
            if len(options['timeSeriesFeatures']) != 1:
                raise AugerException('Please select time series feature'
                    ' to build time series model'
                    ' (experiment/time_series option).')

        print(json.dumps(options, indent = 2))
        return {'evaluation_options': options}, model_type

    def _fill_data_options(self, options, stats, target, exclude):
        for item in stats.get('stat_data'):
            column_name = item['column_name']
            if column_name in exclude:
                continue
            if column_name != target:
                options['featureColumns'].append(column_name)
            else:
                options['targetFeature'] = target
            if item['datatype'] == 'categorical':
                options['categoricalFeatures'].append(column_name)
                if column_name == target:
                    options['binaryClassification'] = \
                        True if item['unique_values'] == 2 else False
            if item['datatype'] == 'date':
                options['timeSeriesFeatures'].append(column_name)
                options['datetime_features'].append(column_name)
