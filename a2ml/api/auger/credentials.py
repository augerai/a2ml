import os
import json


class Credentials(object):
    """Manage credentials on user computer."""
    def __init__(self, config):
        super(Credentials, self).__init__()
        self.config = config
        self.credentials_path = self._path_to_credentials()
        self.organisation = None
        self.username = None
        self.api_url = None
        self.token = None

    def load(self):
        self._ensure_credentials_file()

        with open(self.credentials_path, 'r') as file:
            content = json.loads(file.read())

        self.username = content.get('username')
        self.organisation = content.get('organisation')
        self.api_url = content.get('url')
        if self.api_url is None:
            self.api_url = 'https://app.auger.ai'
        self.token = content.get('token')

        return self

    def save(self):
        self._ensure_credentials_file()

        content = {}
        content['username'] = self.username
        content['url'] = self.api_url
        content['token'] = self.token
        content['organisation'] = self.organisation

        with open(self.credentials_path, 'w') as file:
            file.write(json.dumps(content))

    def verify(self):
        if self.token is None:
            raise Exception(
                'Please provide your credentials to Auger...')
        return True

    def _path_to_credentials(self):
        default_path = '{home}/.a2ml'.format(home=os.getenv("HOME"))
        credentials_path = os.path.abspath(self.config.get('credentials_path', default_path))
        return os.path.join(credentials_path, 'auger')

    def _ensure_credentials_file(self):
        creds_file = self.credentials_path
        creds_path = os.path.dirname(creds_file)

        if not os.path.exists(creds_path):
            os.makedirs(creds_path)

        if not os.path.exists(creds_file):
            with open(creds_file, 'w') as f:
                f.write('{}')
