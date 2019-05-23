import os
import requests
import shortuuid
import urllib.parse
from requests_toolbelt import MultipartEncoder

from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.cluster import AugerClusterApi
from a2ml.api.auger.hub.project_file import AugerProjectFileApi


SUPPORTED_FORMATS = ['.csv', '.arff']

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

            # ensure there are org, project and cluster to work with
            self.ensure_org_and_project()
            self.start_project()

            if self.cluster_mode == 'single_tenant':
                self._upload_to_single_tenant(file_to_upload)
            else:
                self._upload_to_multi_tenant(file_to_upload)

        except Exception as exc:
            self.ctx.log(str(exc))

    def _upload_to_single_tenant(self, file_to_upload):
        cluster_api = AugerClusterApi(self.hub_client, self.cluster_id)
        cluster = cluster_api.properties()

        # get file_uploader_service from the cluster
        # and upload data to that service
        file_uploader_service = cluster.get('file_uploader_service')
        upload_token = file_uploader_service.get('params').get('auger_token')
        upload_url = '%s?auger_token=%s' % (file_uploader_service.get('url'), upload_token)
        file_url = self._upload_file(file_to_upload, upload_url)
        self.ctx.log('Uploaded source file to Auger Hub file: %s' % file_url)

        # create project_file business object on the Project
        basename = os.path.basename(file_to_upload)
        fn, fe = os.path.splitext(basename)
        data_source_name = '%s-%s%s' % (fn, shortuuid.uuid(),fe)
        res = AugerProjectFileApi(self.hub_client).create(
            self.project_id, data_source_name, basename, file_url)
        self.ctx.log('Created data source %s on Auger Hub.' % data_source_name)

    def _upload_to_multi_tenant(self, file_to_upload):
        print('uploading to multi tenant')


    def _get_source_file(self):
        file_to_upload = self.ctx.config['config'].get('data/source', None)

        if file_to_upload is None:
            raise Exception(
                'Please specify in config.yaml file to import to Auger...')

        file_to_upload = os.path.abspath(
            os.path.join(os.getcwd(), file_to_upload))

        filename, file_extension = os.path.splitext(file_to_upload)
        if not file_extension in SUPPORTED_FORMATS:
            raise Exception(
                'Source file has to be one of the supported fomats: %s' %
                ', '.join(SUPPORTED_FORMATS))

        if not os.path.isfile(file_to_upload):
            raise Exception(
                'Can\'t find file to import: %s' % file_to_upload)

        return file_to_upload

    def _upload_file(self, file_name, url):
        basename = os.path.basename(file_name)

        m = MultipartEncoder(fields={
            'file':(basename, open(file_name, 'rb'), "application/octet-stream")})
        r = requests.post(url, data=m, headers={'Content-Type': m.content_type})

        if r.status_code == 200:
            rp = urllib.parse.parse_qs(r.text)
            return ('files/%s' % rp.get('path')[0].split('files/')[-1])
        else:
            raise Exception(
                'HTTP error [%s] while uploadin file to Auger Hub...' % r.status_code)
