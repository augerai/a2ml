import sys

from .impl.cloud.auth import AugerAuthApi
from .credentials import Credentials
from .impl.exceptions import AugerException


class AugerAuth(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def login(self, username, password, organization, url=None):
        self.credentials = Credentials(self.ctx).load(verify=False)

        try:
            self.credentials.token = None
            self.credentials.save()

            if url is None:
                url = self.credentials.api_url

            token = AugerAuthApi(self.ctx).login(
                username, password, organization, url)

            self.credentials.token = token
            self.credentials.username = username
            self.credentials.api_url = url
            self.credentials.organization = organization
            self.credentials.save()

            self.ctx.log(
                'You are now logged in on %s as %s.' % (url, username))

        except Exception as exc:
            exc_text = str(exc)
            if 'Email or password incorrect' in exc_text:
                exc_text = 'Email or password incorrect...'
            self.ctx.log(exc_text)

    def logout(self):
        self.credentials = Credentials(self.ctx).load(verify=False)

        if self.credentials.token is None:
            self.ctx.log('You are not logged in Auger.')
        else:
            self.credentials.token = None
            self.credentials.api_url = None
            self.credentials.organization = None
            self.credentials.save()
            self.ctx.log('You are logged out of Auger.')

    def whoami(self):
        self.credentials = Credentials(self.ctx).load(verify=False)

        if self.credentials.token is None:
            self.ctx.log('Please login to Auger...')
        else:
            self.ctx.log(
                '%s %s %s' % (
                    self.credentials.username,
                    self.credentials.organization,
                    self.credentials.api_url))
