import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed, thread

class ProviderRunner(object):
    """Runner executes provider jobs on threads."""

    def __init__(self, ctx):
        super(ProviderRunner, self).__init__()
        self.ctx = ctx
        try:
            self.providers = self._load_providers()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def execute(self, operation_name, *args, **kwargs):
        if len(self.providers) == 0:
            raise Exception('Please specify list of providers '
                'at config.yaml/providers')
        # if there is single operation requested
        # no need to run it on the thread
        if len(self.providers) == 1:
            getattr(self.providers[0], operation_name)(*args, **kwargs)
            return

        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            futures = [
                executor.submit(getattr(p, operation_name), *args, **kwargs)
                for p in self.providers]

            try:
                for future in as_completed(futures):
                    future.result()
            except KeyboardInterrupt:
                # not a graceful termination
                executor._threads.clear()
                thread._threads_queues.clear()
                raise

    def _load_providers(self):
        def get_instance(p):
            module = importlib.import_module('a2ml.api.%s.a2ml' % p)
            provider_class = getattr(module, '%sA2ML' % p.capitalize())
            return provider_class(self.ctx.copy(p))
        return [get_instance(p) for p in self.ctx.get_providers()]
