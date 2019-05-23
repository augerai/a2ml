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
            file_to_upload, local_data_source = self._get_source_file()

            self.ctx.log('Importing file %s' % file_to_upload)

            self.start_project()

            if local_data_source:
                file_url = self._upload_to_hub(file_to_upload)
                file_name = os.path.basename(file_to_upload)
                ds_name = self._get_data_source_name(file_name)
            else:
                file_url = file_to_upload
                url_path = urllib.parse.urlparse(file_url).path
                file_name = os.path.basename(url_path)
                ds_name = file_name

            self._create_data_source(
                ds_name, file_name, file_url, local_data_source)

        except Exception as exc:
            # TODO refactor into reusable exception handler
            # with comprehensible user output
            self.ctx.log(str(exc))

    def _get_data_source_name(self, file_name):
        project_file_api = AugerProjectFileApi(
            self.hub_client, self.project_id)

        all_similar_names, count = [], 0
        fname, fext = os.path.splitext(file_name)
        for item in iter(project_file_api.list()):
            if fname in item.get('name'):
                all_similar_names.append(item.get('name'))
                count += 1

        if count == 0:
            return file_name

        max_tries = count + 100
        while count < max_tries:
            name = '%s-%s%s' % (fname, count, fext)
            if name in all_similar_names:
                count += 1
            else:
                return name

        return '%s-%s%s' % (fname, shortuuid.uuid(), fext)

    def _create_data_source(self,
        data_source_name, file_name, file_url, local_data_source):
        """Create project_file business object on the Project"""

        project_file_api = AugerProjectFileApi(self.hub_client, self.project_id)

        try:
            project_file_api.create(data_source_name, file_name, file_url)
            self.ctx.log(
                'Created data source %s on Auger Hub.' % data_source_name)
        except Exception as exc:
            if 'en.errors.project_file.url_not_uniq' in str(exc):
                raise Exception('Data Source already exists for %s' % file_url)
            else:
                raise exc

    def _upload_to_hub(self, file_to_upload):
        if self.cluster_mode == 'single_tenant':
            return self._upload_to_single_tenant(file_to_upload)
        else:
            return self._upload_to_multi_tenant(file_to_upload)

    def _upload_to_single_tenant(self, file_to_upload):
        # get file_uploader_service from the cluster
        # and upload data to that service
        cluster_api = AugerClusterApi(self.hub_client, self.cluster_id)
        cluster = cluster_api.properties()

        file_uploader_service = cluster.get('file_uploader_service')
        upload_token = file_uploader_service.get('params').get('auger_token')
        upload_url = '%s?auger_token=%s' % (
            file_uploader_service.get('url'), upload_token)

        file_url = self._upload_file(file_to_upload, upload_url)
        self.ctx.log('Uploaded local file to Auger Hub file: %s' % file_url)
        return file_url

    def _upload_to_multi_tenant(self, file_to_upload):
        print('uploading to multi tenant')
        return None

    def _get_source_file(self):
        file_to_upload = self.ctx.config['config'].get('data/source', None)

        if file_to_upload is None:
            raise Exception(
                'Please specify in config.yaml file to import to Auger...')

        if urllib.parse.urlparse(file_to_upload).scheme in ['http', 'https']:
            return file_to_upload, False

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

        return file_to_upload, True

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
