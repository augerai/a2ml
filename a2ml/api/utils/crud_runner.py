import importlib

class CRUDRunner(object):
    """Runner executes provider crud operations."""

    def __init__(self, ctx, providers, obj_name):
        super(CRUDRunner, self).__init__()
        self.ctx = ctx
        self.providers = self._load_providers(ctx, providers, obj_name)

    def execute(self, operation_name, *args, **kwargs):
        def send_error(p, msg):
            self.ctx.log('[%s]  %s' % (p, msg))
            raise Exception(msg)

        if len(self.providers) == 0:
            msg = 'Please specify provider(s) to run %s' % operation_name
            self.ctx.log(msg)
            return {'error': msg}

        results = {}
        for p in self.providers.keys():
            pi = self.providers[p]
            try:
                try:
                    if isinstance(pi, str):
                        send_error(p, 'Can\'t load %s to run \'%s\''\
                            % (pi, operation_name))
                    else:
                        result = getattr(pi, operation_name)(*args, **kwargs)
                        results[p] = {
                            'result': True,
                            'data': result }
                except AttributeError:
                    send_error(p, '%s not found' % operation_name)
            except Exception as e:
                if self.ctx.debug:
                    import traceback
                    traceback.print_exc()
                results[p] = {
                    'result': False,
                    'data': str(e) }

        return results

    def _load_providers(self, ctx, providers, obj_name):
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
        if providers:
            providers = [p.strip() for p in providers.split(',')]
        else:
            providers = ctx.get_providers()
        return {p: get_instance(p) for p in providers}
