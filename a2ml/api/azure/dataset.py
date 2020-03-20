from azureml.core import Workspace


class AzureDataset(object):

    def __init__(self, ctx):
        super(AzureDataset, self).__init__()
        self.ctx = ctx
        self.ws = self._get_ws()

    def list(self):
        ds = self.ws.get_default_datastore()
        self.ctx.log(ds.container_name)        
        rv = {'datasets': None}
        self.ctx.log(rv)
        return {'datasets': None}

    def _get_ws(self):
        # get the preloaded workspace definition
        return Workspace.from_config()
