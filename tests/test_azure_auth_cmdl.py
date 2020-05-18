import os
import pytest
import json
from a2ml.cmdl.cmdl import cmdl

class TestAzureAuth():
    def test_login(self, log, runner, isolated, monkeypatch):
        azure_dict = {
          "subscription_id": "test_subscription_id",
          "directory_tenant_id": "test_directory_tenant_id",
          "application_client_id": "test_application_client_id",
          "client_secret": "test_client_secret"
        }
        AZURE_JSON = json.dumps(azure_dict)
        monkeypatch.setenv("AZURE_CREDENTIALS", AZURE_JSON)
        result = runner.invoke(
            cmdl,
            ['auth', 'login', '-p', 'azure'])
        assert result.exit_code == 0
        assert (log.records[-1].message ==
                "[azure]  You are now logged in to Azure")

    def test_logout(self, log, runner, isolated, monkeypatch, auger_authenticated):
        result = runner.invoke(cmdl, ['auth', 'logout', '-p', 'azure'])
        assert result.exit_code == 0
        assert log.records[-1].message == "[azure]  You are logged out of Azure."

    def test_whoami_anonymous(self, log, runner, monkeypatch):
        result = runner.invoke(cmdl, ['auth', 'whoami', '-p', 'azure'])
        #assert result.exit_code != 0
        assert (log.records[-1].message ==
                "[azure]  Please login to Azure...")

    def test_whoami_authenticated(self, log, runner, monkeypatch, auger_authenticated):
        azure_dict = {
          "subscription_id": "test_subscription_id",
          "directory_tenant_id": "test_directory_tenant_id",
          "application_client_id": "test_application_client_id",
          "client_secret": "test_client_secret"
        }
        AZURE_JSON = json.dumps(azure_dict)
        monkeypatch.setenv("AZURE_CREDENTIALS", AZURE_JSON)
        result = runner.invoke(cmdl, ['auth', 'whoami', '-p', 'azure'])
        assert result.exit_code == 0
        assert (log.records[-1].message ==
                "[azure]  subscription_id: test_subscription_id directory_tenant_id:test_directory_tenant_id application_client_id:test_application_client_id client_secret:test_client_secret")

    def test_logout_not_logged(self, log, runner, isolated, monkeypatch):
        monkeypatch.setenv("AZURE_CREDENTIALS", '{}')
        result = runner.invoke(cmdl, ['auth', 'logout', '-p', 'azure'])
        assert (log.records[-1].message == '[azure]  You are logged out of Azure.')
        #assert result.exit_code != 0
