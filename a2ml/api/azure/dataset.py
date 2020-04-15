import os
from azureml.core import Dataset
from .project import AzureProject
from .exceptions import AzureException
from .decorators import error_handler

class AzureDataset(object):

    def __init__(self, ctx):
        super(AzureDataset, self).__init__()
        self.ctx = ctx
        self.ws = None

    @error_handler
    def list(self):
        selected = self.ctx.config.get('dataset', None)
        datasets = Dataset.get_all(self._get_ws())
        ndatasts = len(datasets)
        for name in datasets.keys():
            self.ctx.log(
                ('[%s] ' % ('x' if selected == name else ' ')) + name)
        self.ctx.log('%s DataSet(s) listed' % ndatasts)
        return {'datasets': [name for name in datasets.keys()]}

    @error_handler
    def create(self, source = None, validation=False):
        ws = self._get_ws(True)
        if source is None:
            source = self.ctx.config.get('source', None)
        if source is None:
            raise AzureException('Please specify data source file...')

        if source.startswith("http:") or source.startswith("https:"):
            dataset = Dataset.Tabular.from_delimited_files(path=source)
            dataset_name = os.path.basename(source)
        else:    
            ds = self.ws.get_default_datastore()

            if self.ctx.config.path and not source.startswith("/"):
                source = os.path.join(self.ctx.config.path, source)

            ds.upload_files(files=[source], relative_root=None,
                target_path=None, overwrite=True, show_progress=True)
            dataset_name = os.path.basename(source)
            dataset = Dataset.Tabular.from_delimited_files(
                path=ds.path(dataset_name))

        dataset.register(workspace = ws, name = dataset_name,
            create_new_version = True)
        self._select(dataset_name, validation)
        self.ctx.log('Created DataSet %s' % dataset_name)
        return {'dataset': dataset_name}

    @error_handler
    def delete(self, name = None):
        ws = self._get_ws()
        if name is None:
            name = self.ctx.config.get('dataset', None)
        if name is None:
            raise AzureException('Please specify dataset name...')
        ds = Dataset.get_by_name(ws, name)
        ds.unregister_all_versions()
        self._select(None, False)
        self.ctx.log('Deleted dataset %s' % name)
        return {'deleted': name}

    @error_handler        
    def select(self, name = None):
        self._select(name)
        self.ctx.log('Selected dataset %s' % name)
        return {'selected': name}

    def _select(self, name, validation):
        if validation:
            self.ctx.config.set('azure', 'validation_dataset', name)
        else:
            self.ctx.config.set('azure', 'dataset', name)

        self.ctx.config.write('azure')

    def _get_ws(self, create_if_not_exist = False):
        if self.ws is None:
            self.ws = AzureProject(self.ctx)._get_ws(
                create_if_not_exist=create_if_not_exist)
        return self.ws
