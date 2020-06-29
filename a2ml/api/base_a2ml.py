
from a2ml.api.utils.provider_runner import ProviderRunner

class BaseA2ML(object):
    def build_runner(self, ctx, provider, object_name=None, force_local=False):
        if ctx.config.get('use_a2ml_hub'):
            providers = ctx.get_providers(provider)

            ctx.provider_info = {}
            auger_providers = []    
            for item in providers:    
                pr = list(ProviderRunner(ctx, item).providers.values())[0]
                ctx.provider_info[item] = pr.get_provider_info(ctx, item)
                auger_providers.append("auger")    

            provider = ",".join(auger_providers)

        if ctx.config.get('use_server') and not force_local:
            from a2ml.api.utils.remote_runner import RemoteRunner

            return RemoteRunner(ctx, provider, object_name)
        elif object_name:
            from a2ml.api.utils.crud_runner import CRUDRunner

            return CRUDRunner(ctx, provider, object_name)
        else:
            return ProviderRunner(ctx, provider)

    def get_runner(self, locally, provider=None):
        if provider:
          return self.build_runner(self.ctx, provider, force_local=locally)
        else:
          if locally:
              return self.local_runner()
          else:
              return self.runner
