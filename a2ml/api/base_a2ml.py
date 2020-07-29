
from a2ml.api.utils.provider_runner import ProviderRunner

class BaseA2ML(object):
    def __init__(self, ctx, object_name):
        self.ctx = ctx
        self.object_name = object_name

    def build_runner(self, ctx, provider, force_local=False):
        if not ctx.config.get('use_a2ml_hub', False) and ctx.config.get('use_server', False) and not force_local:
            from a2ml.api.utils.remote_runner import RemoteRunner

            return RemoteRunner(ctx, provider, self.object_name)
        elif self.object_name:
            from a2ml.api.utils.crud_runner import CRUDRunner

            return CRUDRunner(ctx, provider, self.object_name)
        else:
            return ProviderRunner(ctx, provider)

    def get_runner(self, locally, model_id=None, provider=None):
        if provider is None and model_id:
            provider = self.ctx.get_model_provider(model_id)

        if provider:
            return self.build_runner(self.ctx, provider, force_local=locally)
        else:
          if locally:
              return self.local_runner()
          else:
              return self.runner
