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

    @staticmethod    
    def get_experiment_options(config, ):
        model_type = config.get('model_type', '')

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
                    'accuracy' if model_type == 'classification' else 'r2')
        }

        if config.get('experiment/trials_per_worker'):
            options['trials_per_worker'] = config.get('experiment/trials_per_worker')
        if config.get('experiment/class_weight'):
            options['algorithm_params_common'] = {'class_weight': config.get('experiment/class_weight')}
        if config.get('experiment/oversampling'):
            options['oversampling'] = config.get('experiment/oversampling')
        if config.get('experiment/estimate_trial_time'):
            options['apply_estimate_trial_time'] = config.get('experiment/estimate_trial_time')
        if config.get('experiment/max_cores_per_trial'):
            options['cpu_per_mt_algorithm'] = config.get('experiment/max_cores_per_trial')
        if config.get('experiment/max_concurrent_trials'):
            options['trials_per_worker'] = config.get('experiment/max_concurrent_trials')
        if config.get('experiment/blocked_models'):
            options["algorithms_to_exlude"] = config.get_list('experiment/blocked_models')
        if config.get('experiment/allowed_models'):
            options["allowed_algorithms"] = config.get_list('experiment/allowed_models')

        if config.get('experiment/blocked_preprocessors'):
            options["blocked_preprocessors"] = config.get_list('experiment/blocked_preprocessors')
        if config.get('experiment/allowed_preprocessors'):
            options["allowed_preprocessors"] = config.get_list('experiment/allowed_preprocessors')
        if config.get('experiment/preprocessors'):
            options["preprocessors"] = config.get_list('experiment/preprocessors')

        if config.get('experiment/exit_score'):
            options['exit_score'] = config.get('experiment/exit_score')
        if config.get('experiment/score_top_count'):
            options['score_top_count'] = config.get('experiment/score_top_count')
        if config.get('experiment/build_metrics_in_trial', None) is not None:
            options['build_metrics_in_trial'] = config.get('experiment/build_metrics_in_trial')
        if config.get('experiment/optimizer_batch_size', None) is not None:
            options['optimizer_batch_size'] = config.get('experiment/optimizer_batch_size')
        if config.get('experiment/cpu_per_mt_algorithm', None) is not None:
            options['cpu_per_mt_algorithm'] = config.get('experiment/cpu_per_mt_algorithm')
        if config.get('experiment/optimizers_names', None) is not None:
            options['optimizers_names'] = config.get('experiment/optimizers_names')
        if config.get('experiment/optimizers', None) is not None:
            options['optimizers'] = config.get('experiment/optimizers')
        if config.get('experiment/search_space', None) is not None:
            options['search_space'] = config.get('experiment/search_space')

        if config.get('review/alert/retrain_policy/type'):
            options['retrain_policy_type'] = config.get('review/alert/retrain_policy/type')
        if config.get('review/alert/retrain_policy/value'):
            options['retrain_policy_value'] = config.get('review/alert/retrain_policy/value')

        split_options = {}
        if config.get('experiment/validation_size'):
            split_options['trainRatio'] = 1.0-float(config.get('experiment/validation_size'))
        if config.get('experiment/shuffle') is not None:
            split_options['shuffleData'] = config.get('experiment/shuffle')
        if config.get('experiment/timeseries_fold_split') is not None:
            split_options['timeseriesSplit'] = config.get('experiment/timeseries_fold_split')
        if config.get('experiment/test_size_limit') is not None:
            split_options['test_size_limit'] = config.get('experiment/test_size_limit')
        if config.get('experiment/groups_col') is not None:
            split_options['groups_col'] = config.get('experiment/groups_col')

        if split_options:
            options['splitOptions'] = split_options

        if  config.get('review/roi/filter'):
            options['roi_metric'] = {
                'filter': str(config.get('review/roi/filter')), 
                'revenue': str(config.get('review/roi/revenue')), 
                'investment': str(config.get('review/roi/investment'))
            }

        return options
            
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

        options = self.get_experiment_options(config)
        options['test_data_path'] = test_data_path
            
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
        if model_type == 'timeseries':
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
