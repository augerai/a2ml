from .base import AugerBaseApi
from .dataset import AugerDataSetApi
from a2ml.api.auger.dataset import AugerDataset
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
        experiment_session_properties = \
            experiment_session_api.create()
        experiment_session_api.run()
        return experiment_session_properties.get('id')

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

        test_data_path = None
        if config.get('experiment/validation_source'):
            data_set_api = None
            if self.ctx.config.get('experiment/validation_dataset'):
                data_set_api = AugerDataSetApi(self.ctx, self.parent_api, config.get('experiment/validation_dataset'))
                data_set_properties = data_set_api.properties()
                test_data_path = data_set_properties.get('url')

            if not test_data_path:
                data_set_api = AugerDataset(self.ctx)._create( self.parent_api,
                    source = self.ctx.config.get('experiment/validation_source'),
                    validation = True
                )
                data_set_properties = data_set_api.properties()
                test_data_path = data_set_properties.get('url')
        else:
            self.ctx.config.remove('experiment/validation_dataset')
            self.ctx.config.write()

        options = {
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
                    'accuracy' if model_type == 'classification' else 'r2'),
            'test_data_path': test_data_path
        }

        if config.get('experiment/trials_per_worker'):
            options['trials_per_worker'] = config.get('experiment/trials_per_worker')
        if config.get('experiment/class_weight'):
            options['algorithm_params_common'] = {'class_weight': config.get('experiment/class_weight')}
        if config.get('experiment/oversampling'):
            options['oversampling'] = config.get('experiment/oversampling')
        if config.get('experiment/estimate_trial_time'):
            options['apply_estimate_trial_time'] = config.get('experiment/estimate_trial_time')

        data_set_id = self.properties()['project_file_id']
        data_set_api = AugerDataSetApi(
            self.ctx, self.parent_api, None, data_set_id)
        data_set_properties = data_set_api.properties()
        stats = data_set_properties['statistics']

        self._fill_data_options(model_type, stats)

        return {'evaluation_options': options}, model_type, stats

    def _fill_data_options(self, model_type, stats):
        config = self.ctx.config
        target = config.get('target')
        if not target:
            raise AugerException('Please set target to build model.')

        exclude = config.get_list('exclude', [])
        label_encoded = config.get_list('experiment/label_encoded', [])
        categoricals = config.get_list('experiment/categoricals', [])
        date_time = config.get_list('experiment/date_time', [])
        time_series = None
        if model_type is 'timeseries':
            time_series = config.get('experiment/time_series', None)
            if not time_series:
                raise AugerException('Please select time series feature'
                    ' to build time series model'
                    ' (experiment/time_series option).')

        for item in stats.get('stat_data'):
            column_name = item['column_name']
            item['use'] = not column_name in exclude and column_name != target
            item['isTarget'] = target == column_name

            if column_name in label_encoded:
                item['datatype'] = 'hashing'
            elif column_name in categoricals:
                item['datatype'] = 'categorical'
            elif column_name in date_time:
                item['datatype'] = 'datetime'
            elif column_name == time_series:
                item['datatype'] = 'timeseries'
