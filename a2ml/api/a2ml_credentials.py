import importlib


class A2MLCredentials(object):
    """Contains the dataset CRUD operations that interact with provider."""
    def __init__(self, ctx, provider):
        super(A2MLCredentials, self).__init__()

        self.ctx = ctx
        self.provider = self._load_provider(provider)

    def load(self):
        return self.provider.load()

    def verify(self):
        return self.provider.verify()

    def serialize(self):
        return self.provider.serialize()

    def login(self,username=None, password=None, organization=None, url=None):
        return self.provider.login(username, password, organization, url)

    def logout(self):
        return self.provider.logout()

    def whoami(self):
        return self.provider.whoami()
    
    def _load_provider(self, provider):
        module = importlib.import_module('a2ml.api.%s.credentials' % provider)
        provider_class = getattr(module, 'Credentials')
        return provider_class(self.ctx.copy(provider))
