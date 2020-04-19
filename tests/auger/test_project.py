import os
import pytest

from .utils import interceptor, object_status_chain, ORGANIZATIONS, PROJECTS
from a2ml.api.auger.project import AugerProject

class TestProject():
    def test_list(self, log, ctx, monkeypatch, authenticated):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerProject(ctx).list()

        assert result.get('projects')
        assert len(result['projects']) == 2
        assert result['projects'][0]['name'] == 'project_1'

    def test_create(self, log, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'create_project': {
                'data': {
                    'id': 1,
                    'name': 'igor-test',
                },
            },
            'get_project': {
                'data': {
                    'id': 1,
                    'name': 'igor-test',
                },
            }
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerProject(ctx).create('igor-test')
        assert result.get('created') == 'igor-test'

    def test_delete(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'delete_project': {
                'data': {}
            }
        }
        interceptor(PAYLOAD, monkeypatch)

        result = AugerProject(ctx).delete('project_1')
        assert result.get('deleted') == 'project_1'

    def test_select(self, log, project, ctx, authenticated):
        assert ctx.config.get('name', '') == 'cli-integration-test'

        result = AugerProject(ctx).select('another_project')

        assert ctx.config.get('name', '') == 'another_project'
        assert result.get('selected') == 'another_project'

    def test_start(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_organization': {'data': {} },
            'get_projects': PROJECTS,
            'get_project': {'data': {'status': 'running'}},
            # 'update_project': {'data': {}},
            # 'deploy_project': {'data': {}}
        }
        interceptor(PAYLOAD, monkeypatch)
        object_status_chain(['deploying', 'deployed', 'running'], monkeypatch)

        result = AugerProject(ctx).start("cli-integration-test")
        assert result.get('running') == 'cli-integration-test'

    def test_stop(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
            'get_project': {
                'data': {
                    'id': 1,
                    'name': 'project_1',
                    'status': 'running',
                },
                'meta': {'status': 404},
            },
            'undeploy_project': {'meta': {'status': 200}, 'data': {}},
        }
        interceptor(PAYLOAD, monkeypatch)
        object_status_chain(['running', 'undeploying', 'undeployed'], monkeypatch)
        monkeypatch.setattr('a2ml.api.auger.impl.cloud.project.AugerProjectApi.status', lambda x: 'undeployed')

        result = AugerProject(ctx).stop("project_1")
        print(result)
        assert result.get('stopped') == 'project_1'
