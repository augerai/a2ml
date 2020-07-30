from .utils import interceptor, EXPERIMENT, PROJECT_FILE
from a2ml.api.auger.impl.cloud.experiment import AugerExperimentApi


class TestConfigs(object):

    def find_stat_item(self, data, name):
        for item in data:
            if item['column_name'] == name:
                return item

        return None
                
    def test_experiment_settings(self, project, ctx_api, monkeypatch):
        config = ctx_api.config
        config.set('target', 'species')
        config.set('experiment/cross_validation_folds', 55)
        config.set('experiment/max_total_time', 606)
        config.set('experiment/max_eval_time', 55)
        config.set('experiment/max_n_trials', 101)
        config.set('experiment/use_ensemble', False)

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type, dataset_statistics = AugerExperimentApi(
            ctx_api, 'project-api', 'iris.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['crossValidationFolds'] == 55
        assert config['evaluation_options']['max_total_time_mins'] == 606
        assert config['evaluation_options']['max_eval_time_mins'] == 55
        assert config['evaluation_options']['max_n_trials'] == 101
        assert config['evaluation_options']['use_ensemble'] == False
        assert config['evaluation_options']['classification'] == True
        assert config['evaluation_options']['scoring'] == 'accuracy'

        stats = dataset_statistics['stat_data']
        assert stats == [
            {'datatype': 'categorical', 'column_name': 'species', 'unique_values': 3, 'use': False, 'isTarget': True}, 
            {'datatype': 'integer', 'column_name': 'sepal_length', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'sepal_width', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'petal_length', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'petal_width', 'use': True, 'isTarget': False}]

    def test_exclude_setting(self, project, ctx_api, monkeypatch):
        config = ctx_api.config
        config.set('target', 'species')
        config.set('exclude',['sepal_length'])

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type, dataset_statistics = AugerExperimentApi(
            ctx_api, 'project-api', 'iris.csv-experiment', '1234').\
            get_experiment_settings()

        stats = dataset_statistics['stat_data']    
        assert stats == [
            {'datatype': 'categorical', 'column_name': 'species', 'unique_values': 3, 'use': False, 'isTarget': True}, 
            {'datatype': 'integer', 'column_name': 'sepal_length', 'use': False, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'sepal_width', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'petal_length', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'petal_width', 'use': True, 'isTarget': False}]

    def test_model_type_setting(self, project, ctx_api, monkeypatch):
        ctx_api.config.set('target', 'species')
        ctx_api.config.set('model_type','regression')
        ctx_api.config.set('experiment/metric', None)

        PAYLOAD = {
            'get_experiment': EXPERIMENT,
            'get_project_file': PROJECT_FILE
        }
        interceptor(PAYLOAD, monkeypatch)
        config, model_type, dataset_statistics = AugerExperimentApi(
            ctx_api, 'project-api', 'iris.csv-experiment', '1234').\
            get_experiment_settings()

        assert config['evaluation_options']['classification'] == False
        assert config['evaluation_options']['scoring'] == 'r2'

        stats = dataset_statistics['stat_data']
        assert stats == [
            {'datatype': 'categorical', 'column_name': 'species', 'unique_values': 3, 'use': False, 'isTarget': True}, 
            {'datatype': 'integer', 'column_name': 'sepal_length', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'sepal_width', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'petal_length', 'use': True, 'isTarget': False}, 
            {'datatype': 'integer', 'column_name': 'petal_width', 'use': True, 'isTarget': False}]
