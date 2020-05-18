from .impl.dataset import DataSet
from .impl.decorators import with_project
from a2ml.api.utils.decorators import error_handler, authenticated
from .impl.cloud.rest_api import RestApi
from .credentials import Credentials
from .config import AugerConfig


class AugerDataset(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.credentials.api_url, self.credentials.token)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def list(self, project):
        count = 0
        selected = self.ctx.config.get('dataset', None)
        for dataset in iter(DataSet(self.ctx, project).list()):
            self.ctx.log(
                ('[%s] ' % ('x' if selected == dataset.get('name') else ' ')) +
                dataset.get('name')
            )
            count += 1
        self.ctx.log('%s DataSet(s) listed' % str(count))
        return {'datasets': DataSet(self.ctx, project).list()}

    @error_handler
    @authenticated
    @with_project(autocreate=True)
    def create(self, project, source = None, validation=False):
        dataset = self._create(project, source, validation)
        self.ctx.log('Created DataSet %s' % dataset.name)
        return {'created': dataset.name}

    def _create(self, project, source = None, validation=False):
        if source is None:
            source = self.ctx.config.get('source', None)
        dataset = DataSet(self.ctx, project).create(source)
        AugerConfig(self.ctx).set_data_set(dataset.name, source, validation)

        return dataset

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def delete(self, project, name):
        if name is None:
            name = self.ctx.config.get('dataset', None)
        DataSet(self.ctx, project, name).delete()
        if name == self.ctx.config.get('dataset', None):
            AugerConfig(self.ctx).set_data_set(None, None, False).set_experiment(None, None)
        self.ctx.log('Deleted dataset %s' % name)
        return {'deleted': name}

    @error_handler
    def select(self, name):
        old_name = self.ctx.config.get('dataset', None)
        if name != old_name:
            AugerConfig(self.ctx).set_data_set(name, None, False).set_experiment(None, None)
        self.ctx.log('Selected DataSet %s' % name)
        return {'selected': name}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def download(self, project, name, path_to_download):
        if name is None:
            name = self.ctx.config.get('dataset', None)
        file_name = DataSet(self.ctx, project, name).download(path_to_download)
        self.ctx.log('Downloaded dataset %s to %s' % (name, file_name))
        return {'dowloaded': name, 'file': file_name}
