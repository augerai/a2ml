from .mock_rest_api import interceptor
from auger.api.cloud.experiment import AugerExperimentApi


EXPERIMENT = {
    'data': {
        'name': 'iris-1.csv-experiment',
        'project_file_id': 1256,
    }
}

PROJECT_FILE = {
    'data': {
        'name': 'iris-1.csv',
        'id': 1256,
        'statistics': {
            'columns_count': 2, 'count': 150,
            'stat_data': [{
                'datatype': 'categorical',
                'column_name': 'species',
                'unique_values': 3
            },{
                'datatype': 'integer',
                'column_name': 'sepal_length'
            },{
                'datatype': 'integer',
                'column_name': 'sepal_width'
            },{
                'datatype': 'integer',
                'column_name': 'petal_length'
            },{
                'datatype': 'integer',
                'column_name': 'petal_width'
            }]
         },
    }
}

class TestConfigs(object):

    def test_experiment_settings(self, project, ctx, monkeypatch):
        config = ctx.config
        config.set('config','target', 'species')
        config.set('config','experiment/cross_validation_folds', 55)
        config.set('config','experiment/max_total_time', 606)
        config.set('config','experiment/max_eval_time', 55)
        config.set('config','experiment/max_n_trials', 101)
        config.set('config','experiment/use_ensemble', False)

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type = AugerExperimentApi(
            ctx, 'project-api', 'iris-1.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['crossValidationFolds'] == 55
        assert config['evaluation_options']['max_total_time_mins'] == 606
        assert config['evaluation_options']['max_eval_time_mins'] == 55
        assert config['evaluation_options']['max_n_trials'] == 101
        assert config['evaluation_options']['use_ensemble'] == False
        # dataset
        assert config['evaluation_options']['targetFeature'] == 'species'
        assert config['evaluation_options']['featureColumns'] == \
            ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
        assert config['evaluation_options']['categoricalFeatures'] == \
            ['species']
        assert config['evaluation_options']['timeSeriesFeatures'] == []
        assert config['evaluation_options']['binaryClassification'] == False
        assert config['evaluation_options']['labelEncodingFeatures'] == []
        assert config['evaluation_options']['classification'] == True
        assert config['evaluation_options']['scoring'] == 'f1_macro'

    def test_exclude_setting(self, project, ctx, monkeypatch):
        config = ctx.config
        config.set('config','target', 'species')
        config.set('config','exclude',['sepal_length'])

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type = AugerExperimentApi(
            ctx, 'project-api', 'iris-1.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['targetFeature'] == 'species'
        assert config['evaluation_options']['featureColumns'] == \
            ['sepal_width', 'petal_length', 'petal_width']
        assert config['evaluation_options']['categoricalFeatures'] == \
            ['species']

    def test_model_type_setting(self, project, ctx, monkeypatch):
        ctx.config.set('config','target', 'species')
        ctx.config.set('config','model_type','regression')
        ctx.config.set('auger','experiment/metric', None)

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type = AugerExperimentApi(
            ctx, 'project-api', 'iris-1.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['timeSeriesFeatures'] == []
        assert config['evaluation_options']['binaryClassification'] == False
        assert config['evaluation_options']['labelEncodingFeatures'] == []
        assert config['evaluation_options']['classification'] == False
        assert config['evaluation_options']['scoring'] == 'r2'
