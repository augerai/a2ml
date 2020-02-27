import os
import json


class Credentials(object):
    """Manage credentials on user computer."""
    def __init__(self, ctx):
        super(Credentials, self).__init__()
        self.ctx = ctx
        self.creds_path = self._path_to_credentials()
        self.creds_file = os.path.join(self.creds_path, 'auger.json')
        self.organization = None
        self.username = None
        self.api_url = None
        self.token = None

    def load(self):
        if 'AUGER_CREDENTIALS' in os.environ:
            content = os.environ.get('AUGER_CREDENTIALS', None)
            content = json.loads(content) if content else {}
        else:
            self._ensure_credentials_file()
            with open(self.creds_file, 'r') as file:
                content = json.loads(file.read())

        self.username = content.get('username')
        self.organization = content.get('organization')
        self.api_url = content.get('url', 'https://app.auger.ai')
        self.token = content.get('token')

        return self

    def save(self):
        self._ensure_credentials_file()

        content = {}
        content['username'] = self.username
        content['url'] = self.api_url
        content['token'] = self.token
        content['organization'] = self.organization

        with open(self.creds_file, 'w') as file:
            file.write(json.dumps(content))

    def verify(self):
        if self.token is None:
            raise Exception(
                'Please provide your credentials to Auger...')
        return True

    def _path_to_credentials(self):
        default_path = '%s/.augerai' % os.environ.get('HOME', os.getcwd())
        creds_path = os.path.abspath(self.ctx.config.get(
            'path_to_credentials', default_path))
        return os.environ.get('AUGER_CREDENTIALS_PATH', creds_path)

    def _ensure_credentials_file(self):
        if not os.path.exists(self.creds_path):
            os.makedirs(self.creds_path)

        if not os.path.exists(self.creds_file):
            with open(self.creds_file, 'w') as f:
                f.write('{}')
