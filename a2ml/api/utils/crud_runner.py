import importlib

class CRUDRunner(object):
    """Runner executes provider crud operations."""

    def __init__(self, ctx, providers, obj_name):
        super(CRUDRunner, self).__init__()
        self.ctx = ctx
        self.providers = self._load_providers(providers, obj_name)

    def execute_one_provider(self, operation_name, *args, **kwargs):
        result = self.execute(operation_name, *args, **kwargs)        
        return list(result.values())[0]

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

    def _load_providers(self, provider, obj_name):
        def get_provider_class(p):
            module = importlib.import_module('a2ml.api.%s.%s' % (p, obj_name))
            return getattr(module, '%s%s' % (p.capitalize(),obj_name.capitalize()))

        def get_instance(p):
            new_ctx = self.ctx.copy(p)
            
            if self.ctx.use_auger_cloud() and p != 'auger':
                new_ctx.provider_info = {p: {"project": {
                    "cluster": self.ctx.config.get("cluster", config_name=p),
                    "deploy_cluster": self.ctx.config.get("deploy_cluster", config_name=p)
                }}}
                provider_class = get_provider_class("auger")
            else:
                provider_class = get_provider_class(p)

            return provider_class(new_ctx)

        return {p: get_instance(p) for p in self.ctx.get_providers(provider)}

