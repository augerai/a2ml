
class BaseA2ML(object):
    def build_runner(self, ctx, provider, object_name=None, force_local=False):
        if ctx.config.get('use_server') == True and not force_local:
            from a2ml.api.utils.remote_runner import RemoteRunner

            return RemoteRunner(ctx, provider, object_name)
        elif object_name:
            from a2ml.api.utils.crud_runner import CRUDRunner

            return CRUDRunner(ctx, provider, object_name)
        else:
            from a2ml.api.utils.provider_runner import ProviderRunner

            return ProviderRunner(ctx, provider)

    def get_runner(self, locally, provider=None):
        if provider:
          return self.build_runner(self.ctx, provider, force_local=locally)
        else:
          if locally:
              return self.local_runner()
          else:
              return self.runner
