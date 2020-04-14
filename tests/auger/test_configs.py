from .utils import interceptor, EXPERIMENT, PROJECT_FILE
from a2ml.api.auger.impl.cloud.experiment import AugerExperimentApi


class TestConfigs(object):

    def test_experiment_settings(self, project, ctx_api, monkeypatch):
        config = ctx_api.config
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
            ctx_api, 'project-api', 'iris.csv-experiment', '1234').\
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

    def test_exclude_setting(self, project, ctx_api, monkeypatch):
        config = ctx_api.config
        config.set('config','target', 'species')
        config.set('config','exclude',['sepal_length'])

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type = AugerExperimentApi(
            ctx_api, 'project-api', 'iris.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['targetFeature'] == 'species'
        assert config['evaluation_options']['featureColumns'] == \
            ['sepal_width', 'petal_length', 'petal_width']
        assert config['evaluation_options']['categoricalFeatures'] == \
            ['species']

    def test_model_type_setting(self, project, ctx_api, monkeypatch):
        ctx_api.config.set('config','target', 'species')
        ctx_api.config.set('config','model_type','regression')
        ctx_api.config.set('auger','experiment/metric', None)

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type = AugerExperimentApi(
            ctx_api, 'project-api', 'iris.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['timeSeriesFeatures'] == []
        assert config['evaluation_options']['binaryClassification'] == False
        assert config['evaluation_options']['labelEncodingFeatures'] == []
        assert config['evaluation_options']['classification'] == False
        assert config['evaluation_options']['scoring'] == 'r2'
