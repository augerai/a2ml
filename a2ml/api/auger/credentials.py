import os
import json
import sys

from .impl.cloud.auth import AugerAuthApi
from a2ml.api.utils.base_credentials import BaseCredentials

class Credentials(BaseCredentials):
    """Manage credentials on user computer."""
    def __init__(self, ctx):
        super(Credentials, self).__init__(ctx, "auger")
        self.organization = None
        self.username = None
        self.api_url = None
        self.token = None

    def load(self):
        if hasattr(self.ctx, 'credentials') and self.ctx.credentials:
            content = self.ctx.credentials
        elif 'AUGER_CREDENTIALS' in os.environ:
            content = os.environ.get('AUGER_CREDENTIALS', None)
            content = json.loads(content) if content else {}
        else:
            self._ensure_credentials_file()
            with open(self.creds_file, 'r') as file:
                content = json.loads(file.read())

        self.username = content.get('username')
        self.organization = content.get('organization')
        if content.get('api_url'): 
            self.api_url = content['api_url']
        else:
            self.api_url = content.get('url', 'https://app.auger.ai')

        self.token = content.get('token')
            
        return self

    def login(self, username, password, organization, url=None):
        self.load()
        try:
            self.token = None
            self.save()

            if url is None:
                url = self.api_url

            token = AugerAuthApi(self.ctx).login(
                username, password, organization, url)

            self.token = token
            self.username = username
            self.api_url = url
            self.organization = organization
            self.save()

            self.ctx.log(
                'You are now logged in on %s as %s.' % (url, username))

        except Exception as exc:
            exc_text = str(exc)
            if 'Email or password incorrect' in exc_text:
                exc_text = 'Email or password incorrect...'
            self.ctx.log(exc_text)

    def logout(self):
        self.load()

        if self.token is None:
            self.ctx.log('You are not logged in Auger.')
        else:
            self.token = None
            self.api_url = None
            self.organization = None
            self.save()
            self.ctx.log('You are logged out of Auger.')

    def whoami(self):
        self.load()

        if self.token is None:
            self.ctx.log('Please login to Auger...')
        else:
            self.ctx.log(
                '%s %s %s' % (
                    self.username,
                    self.organization,
                    self.api_url))

    def serialize(self):
        return {
            'organization' : self.organization,
            'api_url': self.api_url,
            'token': self.token,
            'username': self.username
        }

    def save(self):
        self._ensure_credentials_file()

        content = self.serialize()
        with open(self.creds_file, 'w') as file:
            file.write(json.dumps(content))

    def verify(self):
        if self.token is None:
            raise Exception(
                'Please provide your credentials to Auger...')
        return True
