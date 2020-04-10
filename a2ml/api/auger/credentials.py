import os
import json

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
        if hasattr(self.ctx, 'credentials'):
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
        self.api_url = content.get('api_url', 'https://app.auger.ai')
        self.token = content.get('token')

        return self

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
