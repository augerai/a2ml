import os

from a2ml.api.utils import fsclient


class BaseCredentials(object):
    """Manage credentials on user computer."""
    def __init__(self, ctx, provider):
        super(BaseCredentials, self).__init__()
        self.ctx = ctx
        self.provider = provider
        self.creds_path = self._path_to_credentials()
        self.creds_file = os.environ.get(
            '%s_CREDENTIALS_PATH' % self.provider.upper(),
            os.path.join(self.creds_path, '%s.json'%self.provider)
        )
        self.creds_path = os.path.dirname(self.creds_file)

    def _path_to_credentials(self):
        if self.ctx.config.get('path_to_credentials'):
            creds_path = os.path.abspath(self.ctx.config.get('path_to_credentials'))
        else:
            cur_path = os.getcwd()
            if self.ctx.config.path:
                cur_path = self.ctx.config.path

            if fsclient.is_file_exists(os.path.join(cur_path, "%s.json"%self.provider)):
                creds_path = cur_path
            else:
                creds_path = os.path.abspath('%s/.a2ml' % os.environ.get('HOME', os.getcwd()))

        return creds_path

    def _credentials_file_exist(self):
        return os.path.exists(self.creds_file)

    def _ensure_credentials_file(self):
        if not os.path.exists(self.creds_path):
            os.makedirs(self.creds_path)

        if not os.path.exists(self.creds_file):
            with open(self.creds_file, 'w') as f:
                f.write('{}')
