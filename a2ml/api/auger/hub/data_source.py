import os
import time
import requests
import shortuuid
import urllib.parse

from a2ml.api.auger.hub.cluster import AugerClusterApi
from a2ml.api.auger.hub.utils.exception import AugerException
from a2ml.api.auger.hub.project_file import AugerProjectFileApi

SUPPORTED_FORMATS = ['.csv', '.arff']


class AugerDataSourceApi(AugerProjectFileApi):
    """Wrapper around ProjectFileApi for Auger Data Source."""

    def __init__(self, project_api=None,
        data_source_name=None, data_source_id=None):
        super(AugerDataSourceApi, self).__init__(
            project_api, data_source_name, data_source_id)
        # patch request path
        self._set_api_request_path('AugerProjectFileApi')

    def create(self, data_source_file, data_source_name=None):
        data_source_file, local_data_source = \
            AugerDataSourceApi.verify(data_source_file)

        if local_data_source:
            file_url = self._upload_to_hub(data_source_file)
            file_name = os.path.basename(data_source_file)
            if data_source_name:
                self.object_name = data_source_name
            else:
                self.object_name = self._get_data_source_name(file_name)
        else:
            file_url = data_source_file
            url_path = urllib.parse.urlparse(file_url).path
            file_name = os.path.basename(url_path)
            self.object_name = file_name

        try:
            return super().create(file_url, file_name)
        except Exception as exc:
            if 'en.errors.project_file.url_not_uniq' in str(exc):
                raise AugerException(
                    'Data Source already exists for %s' % file_url)
            raise exc

    def get_readable_name(self):
        # patch readable name
        return 'Data Source'

    @staticmethod
    def verify(data_source_file):
        if urllib.parse.urlparse(data_source_file).scheme in ['http', 'https']:
            return data_source_file, False

        data_source_file = os.path.abspath(
            os.path.join(os.getcwd(), data_source_file))

        filename, file_extension = os.path.splitext(data_source_file)
        if not file_extension in SUPPORTED_FORMATS:
            raise AugerException(
                'Source file has to be one of the supported fomats: %s' %
                ', '.join(SUPPORTED_FORMATS))

        if not os.path.isfile(data_source_file):
            raise AugerException(
                'Can\'t find file to import: %s' % data_source_file)

        return data_source_file, True

    def _upload_to_hub(self, file_to_upload):
        cluster_mode = self.parent_api.parent_api.get_cluster_mode()
        if cluster_mode == 'single_tenant':
            return self._upload_to_single_tenant(file_to_upload)
        else:
            return self._upload_to_multi_tenant(file_to_upload)

    def _upload_to_single_tenant(self, file_to_upload):
        # get file_uploader_service from the cluster
        # and upload data to that service
        project_properties = self.parent_api.properties()
        cluster_id = project_properties.get('cluster_id')
        cluster_api = AugerClusterApi(self.parent_api, cluster_id)
        cluster_properties = cluster_api.properties()

        file_uploader_service = cluster_properties.get('file_uploader_service')
        upload_token = file_uploader_service.get('params').get('auger_token')
        upload_url = '%s?auger_token=%s' % (
            file_uploader_service.get('url'), upload_token)

        file_url = self._upload_file(file_to_upload, upload_url)
        self.hub_client.ctx.log(
            'Uploaded local file to Auger Hub file: %s' % file_url)
        return file_url

    def _upload_to_multi_tenant(self, file_to_upload):
        print('uploading to multi tenant')
        return None

    def _upload_file(self, file_name, url):
        with open(file_name, 'rb') as f:
            r = requests.post(url, data=f)

        if r.status_code == 200:
            rp = urllib.parse.parse_qs(r.text)
            return ('files/%s' % rp.get('path')[0].split('files/')[-1])
        else:
            raise AugerException(
                'HTTP error [%s] while uploadin file to Auger Hub...' % r.status_code)

    def _get_data_source_name(self, file_name):
        fname, fext = os.path.splitext(file_name)
        return self._get_uniq_object_name(fname, fext)
