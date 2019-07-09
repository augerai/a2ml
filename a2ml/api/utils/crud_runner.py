import importlib

class CRUDRunner(object):
    """Runner executes provider crud operations."""

    def __init__(self, ctx, provider, obj_name):
        super(CRUDRunner, self).__init__()
        self.ctx = ctx
        self.providers = self._load_providers(ctx, provider, obj_name)

    def execute(self, operation_name, *args, **kwargs):
        if len(self.providers) == 0:
            raise Exception(
                'Please specify provider(s) to run %s' % operation_name)

        for p in self.providers:
            try:
                if isinstance(p, str):
                    self.ctx.log(
                        'Can\'t load %s to run \'%s\'' % (p, operation_name))
                else:
                    return getattr(p, operation_name)(*args, **kwargs)
            except AttributeError:
                p.ctx.log('%s not found', operation_name)

    def _load_providers(self, ctx, provider, obj_name):
        def get_instance(p):
            try:
                module = importlib.import_module(
                    'a2ml.api.%s.%s' % (p, obj_name))
                provider_class = getattr(module, '%s%s' % \
                    (p.capitalize(),obj_name.capitalize()))
                return provider_class(ctx.copy(p))
            except:
                if self.ctx.debug:
                    import traceback
                    traceback.print_exc()
                return '%s%s' % (p.capitalize(),obj_name.capitalize())
        providers = [provider] if provider else ctx.get_providers()
        return [get_instance(p) for p in providers]
