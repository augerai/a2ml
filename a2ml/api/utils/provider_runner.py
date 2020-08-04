import contextlib
import importlib
import os
import psutil
import sys
import threading
import time


from concurrent.futures import ThreadPoolExecutor, as_completed, thread

class ProviderRunner(object):
    """Runner executes provider jobs on threads."""
    class SpinningCursorThread(threading.Thread):
        def __init__(self,  *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)
            self._stop_event = threading.Event()

        def stop(self):
            self._stop_event.set()

        def stopped(self):
            return self._stop_event.is_set()

        def run(self):
            while not self.stopped():
                for cursor in '|/-\\':
                    sys.stdout.write(cursor)
                    sys.stdout.flush()
                    time.sleep(0.2)
                    sys.stdout.write('\b')

    def __init__(self, ctx, provider = None):
        super(ProviderRunner, self).__init__()
        self.ctx = ctx
        try:
            self.providers = self._load_providers(provider)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def execute_one_provider(self, operation_name, *args, **kwargs):
        result = self.execute(operation_name, *args, **kwargs)

        if list(self.providers.keys())[0] in result:
            return list(result.values())[0]

        return result
            
    def execute(self, operation_name, *args, **kwargs):
        if len(self.providers) == 0:
            raise Exception('Please specify list of providers '
                'at config.yaml/providers')
        # if there is single operation requested
        # no need to run it on the thread
        if len(self.providers) == 1:
            provider_name = list(self.providers.keys())[0]
            return self.execute_provider(provider_name, operation_name, *args, **kwargs)

        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            futures = {
                executor.submit(
                    self.execute_provider, provider_name, operation_name, *args, **kwargs): provider_name
                for provider_name in self.providers.keys()
            }

            try:
                results = {}
                for future in as_completed(futures):
                    results.update(future.result())
                return results
            except KeyboardInterrupt:
                # not a graceful termination
                executor._threads.clear()
                thread._threads_queues.clear()
                raise

    def execute_provider(self, provider_name, operation_name, *args, **kwargs):
        try:
            provider = self.providers[provider_name]
            result = getattr(provider, operation_name)(*args, **kwargs)
            return {
                provider_name: {
                    'result': True,
                    'data': result
                }
            }
        except Exception as e:
            if self.ctx.debug:
                import traceback
                traceback.print_exc()

            return {
                provider_name: {
                    'result': False,
                    'data': str(e)
                }
            }

    def _load_providers(self, provider = None):
        def get_provider_class(p):
            module = importlib.import_module('a2ml.api.%s.a2ml' % p)
            return getattr(module, '%sA2ML' % p.capitalize())

        def get_instance(p):
            new_ctx = self.ctx.copy(p)
            
            if self.ctx.config.get('use_a2ml_hub', False) and p != 'auger':
                new_ctx.provider_info = {p: {"project": {"cluster": self.ctx.config.get("cluster", config_name=p)}}}
                provider_class = get_provider_class("auger")
            else:
                provider_class = get_provider_class(p)

            return provider_class(new_ctx)

        return {p: get_instance(p) for p in self.ctx.get_providers(provider)}
