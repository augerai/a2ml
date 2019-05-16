import sys

from auger.hub_api_client import HubApiClient
from a2ml.api.auger.hub.auth import AugerAuthApi
from a2ml.api.auger.credentials import Credentials

class AugerAuth(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.credentials = Credentials(ctx.config).load()

    def login(self, username, password, url=None):
        self.credentials.token = None
        self.credentials.save()

        if url is None:
            url = self.credentials.api_url

        try:
            token = AugerAuthApi().login(username, password, url)

        except (HubApiClient.FatalApiError,
                HubApiClient.InvalidParamsError,
                HubApiClient.RetryableApiError,
                HubApiClient.MissingParamError) as exc:
            self.ctx.log(str(exc))
            return

        self.credentials.token = token
        self.credentials.username = username
        self.credentials.api_url = url
        self.credentials.save()

        self.ctx.log('You are sucessfully loged in Auger.')

    def logout(self):
        if self.credentials.token is None:
            self.ctx.log('You are not loged in Auger.')
        else:
            self.credentials.token = None
            self.credentials.save()
            self.ctx.log('You are loged out of Auger.')

    def whoami(self):
        if self.credentials.token is None:
            self.ctx.log('Please login to Auger...')
        else:
            self.ctx.log('%s %s' % self.credentials.username, self.credentials.api_url)
