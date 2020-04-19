from .base import AugerBaseApi
from .dataset import AugerDataSetApi
from .experiment_session import AugerExperimentSessionApi
from ..exceptions import AugerException

MODEL_TYPES = ['classification', 'regression', 'timeseries']

class AugerExperimentApi(AugerBaseApi):
    """Auger Experiment Api."""

    def __init__(self, ctx, project_api,
        experiment_name=None, experiment_id=None):
        super(AugerExperimentApi, self).__init__(
            ctx, project_api, experiment_name, experiment_id)
        assert project_api is not None, 'Project must be set for Experiment'
        self._set_api_request_path('AugerExperimentApi')

    def run(self):
        experiment_session_api = \
            AugerExperimentSessionApi(self.ctx, self)
        experimeny_session_properties = \
            experiment_session_api.create()
        experiment_session_api.run()
        return experimeny_session_properties.get('id')

    def create(self, data_set_name):
        assert data_set_name is not None, \
            'DataSet Name is required to create Experiment'

        data_set_api = AugerDataSetApi(
            self.ctx, self.parent_api, data_set_name)
        data_set_properties = data_set_api.properties()

        if not self.object_name:
            self.object_name = self._get_uniq_object_name(
                data_set_name, '-experiment')

        return self._call_create({
            'name': self.object_name,
            'project_id': self.parent_api.object_id,
            'data_path': data_set_properties.get('url')})

    def get_experiment_settings(self):
        config = self.ctx.config

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
                config.get('experiment/label_encoded', []),
            'crossValidationFolds':
                config.get('experiment/cross_validation_folds', 5),
            'max_total_time_mins':
                config.get('experiment/max_total_time', 60),
            'max_eval_time_mins':
                config.get('experiment/max_eval_time', 6),
            'max_n_trials':
                config.get('experiment/max_n_trials', 1000),
            'use_ensemble':
                config.get('experiment/use_ensemble', True),
            'classification':
                True if model_type == 'classification' else False,
            'scoring':
                config.get('experiment/metric',
                    'f1_macro' if model_type == 'classification' else 'r2')
        }

        data_set_id = self.properties()['project_file_id']
        data_set_api = AugerDataSetApi(
            self.ctx, self.parent_api, None, data_set_id)
        data_set_properties = data_set_api.properties()
        stats = data_set_properties['statistics']

        self._fill_data_options(options, stats, target, exclude)

        if options['targetFeature'] is None:
            raise AugerException('Please set target to build model.')

        if model_type is not 'timeseries':
            options['timeSeriesFeatures'] = []
        else:
            time_series = config.get('experiment/time_series', None)
            if time_series:
                options['timeSeriesFeatures'] = [time_series]
            if len(options['timeSeriesFeatures']) != 1:
                raise AugerException('Please select time series feature'
                    ' to build time series model'
                    ' (experiment/time_series option).')

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
