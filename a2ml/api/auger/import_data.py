from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.config import AugerConfig
from auger.api.cloud.data_set import AugerDataSetApi


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

        data_set_api = AugerDataSetApi(self.ctx, self.project_api)
        data_set_api.create(file_to_upload)
        AugerConfig(self.ctx).set_data_set(data_set_api.object_name)

        self.ctx.log(
            'Created DataSet %s on Auger Cloud.' % \
             data_set_api.object_name)
        self.ctx.log(
            'DataSet name stored in auger.yaml/dataset')

    def _get_source_file(self):
        file_to_upload = self.ctx.config['config'].get('source', None)

        if file_to_upload is None:
            raise Exception(
                'Please specify source in config.yaml '
                'to import to Auger Cloud...')

        return AugerDataSetApi.verify(file_to_upload)[0]
