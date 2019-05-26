import concurrent.futures.thread
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProviderOperations(object):
    """Runner executes provider jobs on threads."""
    def __init__(self, ctx):
        super(ProviderOperations, self).__init__()
        self.ctx = ctx

    def execute(self, providers, operations):
        # if there is single operation requested
        # no need to run it on the thread
        if len(providers) == 1:
            operations[providers[0]]()
            return

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            futures = [executor.submit(operations[p])
                for p in providers if p in operations]

            try:
                for future in as_completed(futures):
                    future.result()
            except KeyboardInterrupt:
                # not a graceful termination
                executor._threads.clear()
                concurrent.futures.thread._threads_queues.clear()
                raise
