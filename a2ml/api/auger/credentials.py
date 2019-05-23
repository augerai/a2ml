import os
import json


class Credentials(object):
    """Manage credentials on user computer."""
    def __init__(self, config):
        super(Credentials, self).__init__()
        self.config = config
        self.credentials_path = self._path_to_credentials()
        self.username = None
        self.api_url = None
        self.token = None

    def load(self):
        self._ensure_credentials_file()

        with open(self.credentials_path, 'r') as file:
            content = json.loads(file.read())

        self.username = content.get('username')
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

        with open(self.credentials_path, 'w') as file:
            file.write(json.dumps(content))

    def verify(self):
        if self.token is None:
            raise Exception(
                'Please provide your credentials to import data to Auger...')
        return True

    def _path_to_credentials(self):
        default_path = '{home}/.a2ml'.format(home=os.getenv("HOME"))
        credentials_path = os.path.abspath(self.config.get('credentials_path', default_path))
        return os.path.join(credentials_path, 'auger')

    def _ensure_credentials_file(self):
        file = self.credentials_path
        dir = os.path.dirname(file)

        if not os.path.exists(dir):
            os.makedirs(dir)

        if not os.path.exists(file):
            with open(file, 'w') as file:
                file.write('{}')
