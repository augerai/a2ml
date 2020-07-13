import os
import pytest

from a2ml.cmdl.cmdl import cmdl
from a2ml.api.auger.impl.cloud.rest_api import RestApi


def interceptor(payload, monkeypatch):
    def payloader(x, method, *args, **kwargs):
        return payload[method]
    monkeypatch.setattr(
        RestApi, 'call_ex', payloader)

class TestAugerAuth():
    def test_login(self, log, runner, isolated, monkeypatch):
        PAYLOAD = {
            'create_token': {
                'data': {
                    'token': 'fake_token_for_testing_purpose',
                    },
            },
            'get_organizations': {
                'meta': {
                    'status': 200,
                    'pagination':
                        {'limit': 100, 'total': 1, 'count': 1, 'offset': 0}
                },
                'data': [{'name': 'auger'}]
            }
        }
        interceptor(PAYLOAD, monkeypatch)
        #monkeypatch.setenv("AUGER_CREDENTIALS_PATH", os.getcwd())
        result = runner.invoke(
            cmdl,
            ['auth', 'login'],
            input="test@example.com\nauger\npassword\n")
        assert result.exit_code == 0
        assert (log.records[-1].message ==
                "[auger]  You are now logged in on https://app.auger.ai"
                " as test@example.com.")

    def test_logout(self, log, runner, isolated, monkeypatch, auger_authenticated):
        result = runner.invoke(cmdl, ['auth', 'logout'])
        assert result.exit_code == 0
        assert log.records[-1].message == "[auger]  You are logged out of Auger."

    def test_whoami_anonymous(self, log, runner, monkeypatch):
        monkeypatch.setenv("AUGER_CREDENTIALS", '{}')
        result = runner.invoke(cmdl, ['auth', 'whoami'])
        #assert result.exit_code != 0
        assert (log.records[-1].message ==
                "[auger]  Please login to Auger...")

    def test_whoami_authenticated(self, log, runner, monkeypatch, auger_authenticated):
        result = runner.invoke(cmdl, ['auth', 'whoami'])
        assert result.exit_code == 0
        assert (log.records[-1].message ==
                "[auger]  test_user auger https://example.com")

    def test_logout_not_logged(self, log, runner, isolated, monkeypatch):
        monkeypatch.setenv("AUGER_CREDENTIALS", '{}')
        result = runner.invoke(cmdl, ['auth', 'logout'])
        assert (log.records[-1].message == '[auger]  You are not logged in Auger.')
        #assert result.exit_code != 0
