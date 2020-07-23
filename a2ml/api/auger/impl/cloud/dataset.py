import os
import time
import json
import requests
import shortuuid
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ElementTree

from .cluster import AugerClusterApi
from .project_file import AugerProjectFileApi
from .cluster_task import AugerClusterTaskApi
from ..exceptions import AugerException

from  a2ml.api.utils import fsclient
from  a2ml.api.utils.file_uploader import FileUploader, NewlineProgressPercentage

SUPPORTED_FORMATS = ['.csv', '.arff', '.gz', '.bz2', '.zip', '.xz', '.json', '.xls', '.xlsx', '.feather', '.h5', '.hdf5', '.parquet']


class AugerDataSetApi(AugerProjectFileApi):
    """Auger DataSet API."""

    def __init__(self, ctx, project_api=None,
        data_set_name=None, data_set_id=None):
        super(AugerDataSetApi, self).__init__(
            ctx, project_api, data_set_name, data_set_id)

    def do_upload_file(self, data_source_file, data_set_name=None, local_data_source=True):
        # data_source_file, local_data_source = \
        #     AugerDataSetApi.verify(data_source_file, self.ctx.config.path)

        if local_data_source:
            file_url = self._upload_to_cloud(data_source_file)
            file_name = os.path.basename(data_source_file)
            if data_set_name:
                self.object_name = data_set_name
            else:
                self.object_name = self._get_data_set_name(file_name)
        else:
            file_url = data_source_file
            url_path = urllib.parse.urlparse(file_url).path
            file_name = os.path.basename(url_path)
            self.object_name = file_name

        return file_url, file_name    

    def create(self, data_source_file, data_set_name=None, local_data_source=True):
        file_url, file_name = self.do_upload_file(data_source_file, data_set_name=data_set_name, local_data_source=local_data_source)

        try:
            return super().create(file_url, file_name)
        except Exception as exc:
            if 'en.errors.project_file.url_not_uniq' in str(exc):
                raise AugerException(
                    'DataSet already exists for %s' % file_url)
            raise exc

    def download(self, path_to_download):
        remote_file = self.properties().get('url')
        unused, ext = os.path.splitext(remote_file)
        filename, unused = os.path.splitext(self.name)
        local_file = os.path.abspath(
            os.path.join(path_to_download, filename+ext))

        cluster_mode = self.parent_api.parent_api.get_cluster_mode()
        if cluster_mode == 'single_tenant':
            s3_signed_url = AugerClusterTaskApi(self.ctx, self.project,
                'pipeline_functions.packager.tasks.generate_presigned_url').\
                create(json.dumps([remote_file]))
        else:
            remote_file = os.path.basename(remote_file)
            s3_signed_url = self.rest_api.call('get_project_file_url', {
                'project_id': self.parent_api.oid,
                'file_path': remote_file}).get('url')

        if not os.path.exists(path_to_download):
            os.makedirs(path_to_download)

        urllib.request.urlretrieve(s3_signed_url, local_file)

        return local_file

    def _get_readable_name(self):
        # patch readable name
        return 'DataSet'

    @staticmethod
    def verify(data_source_file, config_path=None):
        if urllib.parse.urlparse(data_source_file).scheme in ['http', 'https']:
            return data_source_file, False

        if not fsclient.is_s3_path(data_source_file):
            if config_path is None:
                config_path = os.getcwd()

            data_source_file = os.path.join(config_path, data_source_file)
            if not fsclient.is_s3_path(data_source_file):
                data_source_file = os.path.abspath(data_source_file)

        filename, file_extension = os.path.splitext(data_source_file)
        if not file_extension in SUPPORTED_FORMATS:
            raise AugerException(
                'Source file has to be one of the supported fomats: %s' %
                ', '.join(SUPPORTED_FORMATS))

        if not fsclient.is_file_exists(data_source_file):
            raise AugerException(
                'Can\'t find file to import: %s' % data_source_file)

        return data_source_file, True

    def _upload_to_cloud(self, file_to_upload):
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
        cluster_api = AugerClusterApi(
            self.ctx, self.parent_api, cluster_id)
        cluster_properties = cluster_api.properties()

        file_uploader_service = cluster_properties.get('file_uploader_service')
        upload_token = file_uploader_service.get('params').get('auger_token')
        upload_url = '%s?auger_token=%s' % (
            file_uploader_service.get('url'), upload_token)

        file_url = self._upload_file(file_to_upload, upload_url)
        self.ctx.log(
            'Uploaded local file to Auger Cloud file: %s' % file_url)
        return file_url

    def _upload_file(self, file_name, url):
        with open(file_name, 'rb') as f:
            r = requests.post(url, data=f)

        if r.status_code == 200:
            rp = urllib.parse.parse_qs(r.text)
            return ('files/%s' % rp.get('path')[0].split('files/')[-1])
        else:
            raise AugerException(
                'HTTP error [%s] while uploading file to Auger Cloud...' % r.status_code)

    def _upload_to_multi_tenant(self, file_to_upload):
        file_path = 'workspace/projects/%s/files/%s-%s' % \
            (self.parent_api.object_name, shortuuid.uuid(),
             os.path.basename(file_to_upload))

        res = self.rest_api.call('create_project_file_url', {
            'project_id': self.parent_api.object_id,
            'file_path': file_path,
            'file_size': fsclient.get_file_size(file_to_upload)
        })

        if res is None:
            raise AugerException(
                'Error while uploading file to Auger Cloud...')

        if 'multipart' in res:
            upload_details = res['multipart']
            config = upload_details['config']

            uploader = FileUploader(
                upload_details['bucket'],
                config['endpoint'],
                config['access_key'],
                config['secret_key'],
                config['security_token']
            )

            with fsclient.open_file(file_to_upload, 'rb', encoding=None, auto_decompression=False) as f:
                return uploader.multipart_upload_obj(
                    f,
                    upload_details['key'],
                    callback=NewlineProgressPercentage(file_to_upload)
                )
        else:
            url = res['url']
            file_path = res['fields']['key']
            with fsclient.open_file(file_to_upload, 'rb', encoding=None, auto_decompression=False) as f:
                files = {'file': (file_path, f)}
                res = requests.post(url, data=res['fields'], files=files)

            if res.status_code == 201 or res.status_code == 200:
                bucket = urllib.parse.urlparse(url).path #netloc.split('.')[0]
                return 's3:/%s/%s' % (bucket, file_path)
            else:
                if res.status_code == 400 and b'EntityTooLarge' in res.content:
                    max_size = ElementTree.fromstring(res.content).find('MaxSizeAllowed').text
                    max_size_mb = int(max_size) / 1024 / 1024
                    raise AugerException('Data set size is limited to %.1f MB' % max_size_mb)
                else:
                    raise AugerException(
                        'HTTP error [%s] "%s" while uploading file'
                            ' to Auger Cloud...' % (res.status_code, res.content))

    def _get_data_set_name(self, file_name):
        fname, fext = os.path.splitext(file_name)
        return self._get_uniq_object_name(fname, fext)
