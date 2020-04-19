from .cloud.dataset import AugerDataSetApi
from .exceptions import AugerException


class DataSet(AugerDataSetApi):
    """Auger Cloud Data Set(s) management"""

    def __init__(self, ctx, project, data_set_name=None):
        super(DataSet, self).__init__(
            ctx, project, data_set_name)
        self.project = project

    def create(self, data_source_file):
        if data_source_file is None:
            raise AugerException('Please specify data source file...')

        data_source_file, local_data_source = \
            AugerDataSetApi.verify(data_source_file, self.ctx.config.path)

        if not self.project.is_running():
            self.ctx.log('Starting Project to process request...')
            self.project.start()

        super().create(data_source_file, self.object_name, local_data_source=local_data_source)
        return self

    def download(self, path_to_download):
        if path_to_download is None:
            raise AugerException('Please specify path to download...')

        if not self.project.is_running():
            self.ctx.log('Starting Project to process request...')
            self.project.start()

        return super().download(path_to_download)
