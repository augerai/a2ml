import os
import time
import requests
import shortuuid
import urllib.parse

from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.data_source import AugerDataSourceApi


class AugerImport(AugerBase):
    """Import data into Auger."""

    def __init__(self, ctx):
        super(AugerImport, self).__init__(ctx)

    def import_data(self):
        try:
            # verify avalability of auger credentials
            self.credentials.verify()

            # verify there is a source file for importing
            file_to_upload = self._get_source_file()

            self.ctx.log('Importing file %s' % file_to_upload)

            self.start_project()

            data_source_api = AugerDataSourceApi(
                self.hub_client, self.project_api)
            data_source_api.create(file_to_upload)

            self.ctx.log(
                'Created Data Source %s on Auger Hub.' % \
                 data_source_api.object_name)

        except Exception as exc:
            # TODO refactor into reusable exception handler
            # with comprehensible user output
            # import traceback
            # traceback.print_exc()
            self.ctx.log(str(exc))

    def _get_source_file(self):
        file_to_upload = self.ctx.config['config'].get('data/source', None)

        if file_to_upload is None:
            raise Exception(
                'Please specify in config.yaml file to import to Auger...')

        return AugerDataSourceApi.verify(file_to_upload)[0]
