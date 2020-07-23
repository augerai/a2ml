import os

import pytest

from .utils import interceptor, ORGANIZATIONS, PROJECTS, PROJECT_FILES, PROJECT_FILE, EXPERIMENTS
from a2ml.api.auger.experiment import AugerExperiment


EXPERIMENT_SESSION = {
    'data': {
        'id': 'test_id_2',
        'model_settings': {'start_time': '2019-06-28 20:30:00.992405'},
        'status': 'completed',
        'project_file_id': 1256,
    }
}

EXPERIMENT_SESSIONS = {
    'meta': {
        'pagination': {'offset': 0, 'count': 2, 'total': 2, 'limit': 100},
        'status': 200},
    'data': [{
        'id': 'test_id_1',
        'model_settings': {'start_time': '2019-06-26 22:00:00.405'},
        'status': 'completed',
    },
    EXPERIMENT_SESSION['data']
    ]
}

TRIALS = {
    'meta': {'pagination': {'offset': 0, 'limit': 100, 'count': 20, 'total': 20}, 'status': 200},
    'data': [{
        'id': 'A79FBADD8CCD417',
        'score_name': 'f1_macro',
        'score_value': 0.123,
        'hyperparameter': {'algorithm_name': 'auger_ml.algorithms.baseline.BaselineClassifier'},
    }]*20
}

PROJECT = {
    'data': {
        'status': 'running',
    }
}


class TestExperiment():
    def test_list(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project': PROJECT,
            'get_project_files': PROJECT_FILES,
            'get_experiments': EXPERIMENTS,
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerExperiment(ctx).list()

        assert result.get('experiments')
        assert len(result['experiments']) == 1
        assert result['experiments'][0]['name'] == 'iris-1.csv-experiment'
        assert result['experiments'][0]['project_file_id'] == 1256

    def test_start(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project': PROJECT,
            'get_project_files': PROJECT_FILES,
            'get_project_file': PROJECT_FILE,
            'get_experiments': EXPERIMENTS,
            'get_experiment_sessions': EXPERIMENT_SESSIONS,
            'create_experiment_session': EXPERIMENT_SESSION,
            'get_experiment_session': EXPERIMENT_SESSION,
            'update_experiment_session': EXPERIMENT_SESSION,
            'get_trials': TRIALS,
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerExperiment(ctx).start()

        assert result.get('experiment_name') == 'iris-1.csv-experiment'
        assert result.get('session_id') == 'test_id_2'

    @pytest.mark.skip(reason="Make it work first, edge cases next")
    def test_start_without_target(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project': PROJECT,
            'get_project_files': PROJECT_FILES,
            'get_experiments': EXPERIMENTS,
            'get_experiment_sessions': EXPERIMENT_SESSIONS,
            'get_trials': TRIALS,
        }
        interceptor(PAYLOAD, monkeypatch)
        # TODO: ensure cli throws error on trying to start exp w/o target
        result = AugerExperiment(ctx).start()
        # assert result.exit_code != 0
        # assert log.messages[-1] == 'Please set target to build model.'

    def test_stop(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project_files': PROJECT_FILES,
            'get_experiments': EXPERIMENTS,
            'get_experiment_sessions': EXPERIMENT_SESSIONS,
            'update_experiment_session': EXPERIMENT_SESSION,
        }
        interceptor(PAYLOAD, monkeypatch)
        monkeypatch.setattr('a2ml.api.auger.impl.cloud.experiment_session.AugerExperimentSessionApi.status', lambda *a, **kw: 'started')

        result = AugerExperiment(ctx).stop()
        assert result.get('stopped') == 'iris-1.csv-experiment'
        # assert result.exit_code == 0
        # assert log.messages[0] == 'Search is stopped...'

    def test_leaderboard(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project_files': PROJECT_FILES,
            'get_experiments': EXPERIMENTS,
            'get_experiment_session': EXPERIMENT_SESSION,
            'get_experiment_sessions': EXPERIMENT_SESSIONS,
            'get_trials': TRIALS,
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerExperiment(ctx).leaderboard()

        assert result.get('leaderboard')
        assert len(result.get('leaderboard')) == 10
        assert result.get('status') == 'completed'

    def test_history(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project_files': PROJECT_FILES,
            'get_experiments': EXPERIMENTS,
            'get_experiment_sessions': EXPERIMENT_SESSIONS,
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerExperiment(ctx).history()
        assert result.get('history')
        assert len(result.get('history')) == 2
        assert result['history'][0].get('status') == 'completed'

