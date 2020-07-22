import os

from azureml.core import Dataset
from a2ml.api.utils import fsclient, get_remote_file_info
from .project import AzureProject
from .exceptions import AzureException
from a2ml.api.utils.decorators import error_handler, authenticated
from .credentials import Credentials


class AzureDataset(object):

    def __init__(self, ctx, ws = None):
        super(AzureDataset, self).__init__()
        self.ctx = ctx
        self.ws = ws
        self.credentials = Credentials(self.ctx).load()

    @error_handler
    @authenticated
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
    @authenticated
    def create(self, source = None, validation=False):
        ws = self._get_ws(True)
        if source is None:
            source = self.ctx.config.get('source', None)
        if source is None:
            raise AzureException('Please specify data source file...')

        if source.startswith("http:") or source.startswith("https:"):
            url_info = get_remote_file_info(source)
            if self.ctx.config.get('source_format', "") == "parquet" or \
               url_info.get('file_ext', "").endswith(".parquet"):
                dataset = Dataset.Tabular.from_parquet_files(path=source)
            else:        
                dataset = Dataset.Tabular.from_delimited_files(path=source)

            dataset_name = url_info.get('file_name')+url_info.get('file_ext')
        else:
            with fsclient.with_s3_downloaded_or_local_file(source) as local_path:
                ds = self.ws.get_default_datastore()

                if self.ctx.config.path and not local_path.startswith("/"):
                    local_path = os.path.join(self.ctx.config.path, local_path)

                ds.upload_files(files=[local_path], relative_root=None,
                    target_path=None, overwrite=True, show_progress=True)
                dataset_name = os.path.basename(local_path)
                if dataset_name.endswith(".parquet") or self.ctx.config.get('source_format', "") == "parquet":
                    dataset = Dataset.Tabular.from_parquet_files(path=ds.path(dataset_name))
                else:    
                    dataset = Dataset.Tabular.from_delimited_files(
                        path=ds.path(dataset_name))

        dataset.register(workspace = ws, name = dataset_name,
            create_new_version = True)
        self._select(dataset_name, validation)
        self.ctx.log('Created DataSet %s' % dataset_name)
        return {'dataset': dataset_name}

    @error_handler
    @authenticated
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
    @authenticated
    def select(self, name = None):
        self._select(name)
        self.ctx.log('Selected dataset %s' % name)
        return {'selected': name}

    def _select(self, name, validation):
        if validation:
            self.ctx.config.set('experiment/validation_dataset', name)
        else:
            self.ctx.config.set('dataset', name)

        self.ctx.config.write()

    def _get_ws(self, create_if_not_exist = False):
        if self.ws is None:
            self.ws = AzureProject(self.ctx)._get_ws(
                create_if_not_exist=create_if_not_exist)
        return self.ws

    def _columns(self, dataset = None, name = None):
        if not dataset:
            ws = self._get_ws()
            if name is None:
                name = self.ctx.config.get('dataset', None)
            if name is None:
                raise AzureException('Please specify dataset name...')
            dataset = Dataset.get_by_name(ws, name)

        df = dataset.take(1).to_pandas_dataframe()
        return df.columns.tolist()

