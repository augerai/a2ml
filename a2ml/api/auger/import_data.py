from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.data_source import AugerDataSourceApi
from a2ml.api.auger.config import AugerConfig


class AugerImport(AugerBase):
    """Import data into Auger."""

    def __init__(self, ctx):
        super(AugerImport, self).__init__(ctx)

    @AugerBase._error_handler
    def import_data(self):
        # verify avalability of auger credentials
        self.credentials.verify()

        # verify there is a source file for importing
        file_to_upload = self._get_source_file()

        self.ctx.log('Importing file %s' % file_to_upload)

        self.start_project()

        data_source_api = AugerDataSourceApi(self.project_api)
        data_source_api.create(file_to_upload)
        AugerConfig(self.ctx).set_data_source(data_source_api.object_name)

        self.ctx.log(
            'Created Data Source %s on Auger Hub.' % \
             data_source_api.object_name)
        self.ctx.log(
            'Data Source name stored in auger.yaml/data_source/name')

    def _get_source_file(self):
        file_to_upload = self.ctx.config['config'].get('source', None)

        if file_to_upload is None:
            raise Exception(
                'Please specify in config.yaml file to import to Auger...')

        return AugerDataSourceApi.verify(file_to_upload)[0]
