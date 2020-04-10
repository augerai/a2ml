from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.provider_runner import ProviderRunner
from a2ml.api.utils.remote_runner import RemoteRunner


class BaseA2ML(object):
    def build_runner(self, ctx, provider, object_name=None, force_local=False):
        if ctx.config.get('use_server') == True and not force_local:
            return RemoteRunner(ctx, provider, object_name)
        elif object_name:
            return CRUDRunner(ctx, provider, object_name)
        else:
            return ProviderRunner(ctx, provider)
