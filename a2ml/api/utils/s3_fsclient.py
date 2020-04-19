import os
import datetime
from dateutil.tz import tzutc
import mimetypes
import logging


class S3FSClient:

    def _get_relative_path(self, path):
        try:
            from urllib.parse import urlparse
        except ImportError:
            from urlparse import urlparse

        relPath = path
        uri = urlparse(path)
        self.s3BucketName = uri.netloc

        self.client = self._create_botos3_client()
        relPath = uri.path[1:]

        relPath = relPath.replace("//", "/")
        if relPath.endswith("/"):
            relPath = relPath[:-1]

        return relPath

    @staticmethod
    def _create_botos3_client():
        import boto3

        endpoint_url = os.environ.get('S3_ENDPOINT_URL')

        client = None
        if endpoint_url:
            client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                config=boto3.session.Config(signature_version='s3v4')
            )
        else:
            client = boto3.client(
                's3',
                config=boto3.session.Config(signature_version='s3v4')
            )

        return client

    def get_smart_open_transport_params(self):
        transport_params = None
        endpoint_url = os.environ.get('S3_ENDPOINT_URL')

        if endpoint_url:
            transport_params = {
                'resource_kwargs': {
                    'endpoint_url': endpoint_url,
                }
            }

        return transport_params

    def wait_for_path(self, path):
        path = self._get_relative_path(path)
        if 'object_exists' in self.client.waiter_names:
            waiter = self.client.get_waiter('object_exists')
            waiter.config.delay = 2
            waiter.config.max_attempts = 50

            logging.info("S3FSClient: waiting for max %s sec for object: %s" % (
                waiter.config.delay*waiter.config.max_attempts, path))
            waiter.wait(Bucket=self.s3BucketName, Key=path)

    def s3fs_open(self, path, mode):
        from s3fs.core import S3FileSystem

        endpoint_url = os.environ.get('S3_ENDPOINT_URL')
        client_kwargs = {}
        if endpoint_url:
            client_kwargs = {'endpoint_url': endpoint_url}

        if 'r' in mode:
            self.wait_for_path(path)

        s3 = S3FileSystem(anon=False, default_fill_cache=False,
                          client_kwargs=client_kwargs)
        return s3.open(path, mode=mode)

    def list_folder(self, path, wild=False, removeFolderName=False, meta_info=False):
        import fnmatch
        from urllib.parse import unquote

        path = self._get_relative_path(path)
        path_filter = None
        if path and wild:
            parts = path.split('/')
            path = '/'.join(parts[:-1])
            path_filter = parts[-1]

        if path:
            path = path + "/" if not path.endswith("/") else path

        #print("s3BucketName: %s;Path:%s; path_filter:%s"%(self.s3BucketName, path, path_filter))

        ContinuationToken = None
        result = []
        while True:
            if ContinuationToken:
                listFiles = self.client.list_objects_v2(
                    Bucket=self.s3BucketName, Prefix=path, Delimiter='/', ContinuationToken=ContinuationToken)
            else:
                listFiles = self.client.list_objects_v2(
                    Bucket=self.s3BucketName, Prefix=path, Delimiter='/')

            ContinuationToken = listFiles.get('NextContinuationToken', None)
            files = None
            folders = None
            if listFiles is not None:
                files = listFiles.get('Contents')
                folders = listFiles.get('CommonPrefixes')

            if files is not None:
                for file in files:
                    if file.get('Key') != path:
                        file_path = unquote(file.get('Key')[len(path):])
                        if meta_info:
                            result.append({'path': file_path,
                                           'last_modified': self._get_seconds_from_epoch(file.get('LastModified')), 'size': file.get('Size', 0)})
                        else:
                            result.append(file_path)

            if folders is not None:
                for folder in folders:
                    if folder.get('Prefix') != path:
                        folder_path = unquote(folder.get('Prefix')[len(path):])
                        if meta_info:
                            result.append({'path': folder_path,
                                           'last_modified': self._get_seconds_from_epoch(folder.get('LastModified')), 'size': folder.get('Size', 0)})
                        else:
                            result.append(folder_path)

            if not ContinuationToken:
                break

        if path_filter:
            if meta_info:
                result = [item for item in result if fnmatch.fnmatch(
                    item['path'], path_filter)]
            else:
                result = fnmatch.filter(result, path_filter)

        return result

    def create_folder(self, path):
        path = self._get_relative_path(path)
        path = path + "/" if not path.endswith("/") else path

        # If no path we shouldn't create it
        if path != "/":
            self.client.put_object(Bucket=self.s3BucketName, Key=path)

    def create_parent_folder(self, path):
        parent = os.path.dirname(path)
        self.create_folder(parent)

    def remove_folder(self, path, remove_self=True):
        path = self._get_relative_path(path)
        self._s3_removeFolder(path, remove_self)

    def remove_file(self, path, wild=False):
        if wild:
            files = self.list_folder(path, wild)
            path = self._get_relative_path(path)
            for file in files:
                path_to_remove = os.path.join(os.path.dirname(path), file)
                # print(path_to_remove)
                self.client.delete_object(
                    Bucket=self.s3BucketName, Key=path_to_remove)

            #raise Exception("S3FSClient::remove_file wild is not implemented:%s"%path)
        else:
            path = self._get_relative_path(path)
            self.client.delete_object(Bucket=self.s3BucketName, Key=path)

    def _s3_removeFolder(self, path, remove_self=True):
        path = path + "/" if not path.endswith("/") else path

        # print("Remove:%s"%path)
        ContinuationToken = None
        while True:
            if ContinuationToken:
                listFiles = self.client.list_objects_v2(
                    Bucket=self.s3BucketName, Prefix=path, Delimiter='/', ContinuationToken=ContinuationToken)
            else:
                listFiles = self.client.list_objects_v2(
                    Bucket=self.s3BucketName, Prefix=path, Delimiter='/')

            # print(listFiles)
            ContinuationToken = listFiles.get('NextContinuationToken', None)
            files = None
            folders = None
            if listFiles is not None:
                files = listFiles.get('Contents')
                folders = listFiles.get('CommonPrefixes')

            if files is not None:
                for file in files:
                    #print("Delete path:%s"%file.get('Key'))
                    self.client.delete_object(
                        Bucket=self.s3BucketName, Key=file.get('Key'))

            if folders is not None:
                for folder in folders:
                    self._s3_removeFolder(folder.get(
                        'Prefix'), remove_self=False)

            if not ContinuationToken:
                break

        if remove_self:
            self.client.delete_object(Bucket=self.s3BucketName, Key=path[:-1])

    def _s3_moveFile(self, oldName, newName):
        self.client.copy_object(Bucket=self.s3BucketName, CopySource={
                                'Bucket': self.s3BucketName, 'Key': oldName}, Key=newName)
        self.client.delete_object(Bucket=self.s3BucketName, Key=oldName)

    def is_file_exists(self, path):
        path = self._get_relative_path(path)
        exists = False
        try:
            res = self.client.head_object(Bucket=self.s3BucketName, Key=path)
            exists = True
        except Exception as e:
            pass

        return exists

    @staticmethod
    def _get_seconds_from_epoch(date_data):
        res = 0
        try:
            if date_data:
                epoch = datetime.datetime(1970, 1, 1, tzinfo=tzutc())
                res = (date_data - epoch).total_seconds()
        except Exception as e:
            #logging.exception("_get_seconds_from_epoch failed.")
            pass

        return res

    def get_mtime(self, path):
        path = self._get_relative_path(path)
        res = None
        try:
            obj = self.client.head_object(Bucket=self.s3BucketName, Key=path)
            res = self._get_seconds_from_epoch(obj.get('LastModified'))
        except Exception as e:
            #logging.exception("getMTime failed.")
            pass

        return res

    def get_file_size(self, path):
        path = self._get_relative_path(path)
        res = 0
        try:
            obj = self.client.head_object(Bucket=self.s3BucketName, Key=path)
            res = obj.get('ContentLength')
        except Exception as e:
            #logging.exception("get_file_size failed.")
            pass

        return res

    def is_folder_exists(self, path):
        path = self._get_relative_path(path)
        listFiles = self.client.list_objects(
            Bucket=self.s3BucketName, Prefix=path + "/", Delimiter='/')
        if listFiles is not None:
            content = listFiles.get('Contents')
            if content is None:
                listFiles = listFiles.get('CommonPrefixes')
            else:
                listFiles = content

        # print(listFiles)
        return listFiles is not None

    def read_text_file(self, path):
        from .LocalFSClient import LocalFSClient

        with LocalFSClient().save_atomic(path) as local_tmp_path:
            self.download_file(path, local_tmp_path)
            return LocalFSClient().read_text_file(local_tmp_path)

        # obj = self.client.get_object(Bucket=self.s3BucketName, Key=path)
        # return obj['Body'].read()

    def write_text_file(self, path, data, atomic=False):
        path = self._get_relative_path(path)
        mimetype, _ = mimetypes.guess_type(path)
        if mimetype is None:
            self.client.put_object(
                Body=data, Bucket=self.s3BucketName, Key=path)
        else:
            self.client.put_object(
                Body=data, Bucket=self.s3BucketName, Key=path, ContentType=mimetype)

    def copy_file_remote(self, path_src, path_dst):
        path = self._get_relative_path(path_src)
        copy_source = {
            'Bucket': self.s3BucketName,
            'Key': path
        }

        path = self._get_relative_path(path_dst)
        self.client.copy(copy_source, self.s3BucketName, path)

    def copy_file(self, path_src, path_dst):
        if path_src.startswith("s3") and path_dst.startswith("s3"):
            self.copy_file_remote(path_src, path_dst)
        elif path_dst.startswith("s3"):
            path = self._get_relative_path(path_dst)
            self._s3_upload_file(path_src, path)
        elif path_src.startswith("s3"):
            self.download_file(path_src, path_dst)

    def _s3_upload_file(self, path_local, path_s3):
        import boto3

        s3_config = boto3.s3.transfer.TransferConfig(use_threads=False)

        mimetype, _ = mimetypes.guess_type(path_local)
        if mimetype is None:
            self.client.upload_file(
                path_local, Bucket=self.s3BucketName, Key=path_s3, Config=s3_config)
        else:
            self.client.upload_file(path_local, Bucket=self.s3BucketName, Key=path_s3, Config=s3_config,
                                    ExtraArgs={"ContentType": mimetype}
                                    )

    def copy_files(self, path_src, path_dst):
        files = self.list_folder(path_src, wild=True)
        for file in files:
            self.copy_file(os.path.join(os.path.dirname(
                path_src), file), os.path.join(path_dst, file))

    def copy_folder(self, path_src, path_dst):
        from .FSClient import FSClient

        files = FSClient().list_folder(path_src)
        for file in files:
            full_src = os.path.join(path_src, file)
            if FSClient().is_file_exists(full_src):
                self.copy_file(full_src, os.path.join(path_dst, file))
            else:
                self.copy_folder(full_src, os.path.join(path_dst, file))

    def download_file(self, path, local_path):
        from .LocalFSClient import LocalFSClient
        from .FSClient import FSClient
        import boto3
        try:
            from urllib.parse import urlparse
        except ImportError:
            from urlparse import urlparse

        if path.startswith("http:") or path.startswith("https:"):
            s3_path = self._get_relative_path(local_path)

            uri = urlparse(path)

            with LocalFSClient().save_atomic(uri.path) as temp_file:
                LocalFSClient().downloadFile(path, temp_file)
                self._s3_upload_file(temp_file, s3_path)

                #FSClient().waitForFile(local_path, wait_for_file=True, num_tries=3000, interval_sec=20)
            # with FSClient().open(path, "rb", encoding=None) as fd:
            #     self.client.upload_fileobj(fd, Bucket=self.s3BucketName, Key=s3_path)
        else:
            path = self._get_relative_path(path)
            LocalFSClient().create_parent_folder(local_path)
            self.client.download_file(
                Bucket=self.s3BucketName, Key=path, Filename=local_path)

    def download_folder(self, path, local_path):
        files = self.list_folder(path)
        for file in files:
            if file.endswith('/'):
                self.download_folder(os.path.join(
                    path, file), os.path.join(local_path, file))
            else:
                self.copy_file(os.path.join(path, file),
                               os.path.join(local_path, file))

    def move_file(self, path_src, path_dst):
        self.copy_file(path_src, path_dst)

        if path_src.startswith("s3"):
            self.remove_file(path_src)
        else:
            from .LocalFSClient import LocalFSClient
            LocalFSClient().remove_file(path_src)
