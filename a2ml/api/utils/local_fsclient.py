import contextlib
import errno
import logging
import os
import os.path
import shutil
import tempfile
import glob
import platform


class LocalFSClient:

    def remove_folder(self, path, remove_self=True):
        shutil.rmtree(path, ignore_errors=True)
        if not remove_self:
            self.create_folder(path)

    def remove_file(self, path, wild=False):
        try:
            if wild:
                for fl in glob.glob(path):
                    os.remove(fl)
            else:
                os.remove(path)
        except OSError:
            pass

    def is_file_exists(self, path):
        return os.path.isfile(path)

    def is_folder_exists(self, path):
        return os.path.exists(path)

    def create_folder(self, path):
        if not self.is_folder_exists(path):
            os.makedirs(path)

        # try:
        # except OSError:
        #     pass
            #logging.exception("createFolder failed")
        self.list_folder(self.get_parent_folder(path))

    def create_parent_folder(self, path):
        parent = os.path.dirname(path)
        self.create_folder(parent)

    def get_parent_folder(self, path):
        return os.path.dirname(path)

    def read_text_file(self, path):
        import codecs

        self.list_folder(self.get_parent_folder(path))
        with codecs.open(path, "r", encoding='utf-8') as file:
            return file.read()

    def write_text_file(self, path, data, atomic=False):
        self.create_parent_folder(path)

        if atomic:
            with self.open_atomic(path, "w") as file:
                file.write(data)
        else:
            from a2ml.api.utils import fsclient
            self.remove_file(path)

            with fsclient.open_file(path, "w") as file:
                try:
                    file.write(data)
                finally:
                    file.flush()  # flush file buffers
                    os.fsync(file.fileno())

        self.read_text_file(path)

    def list_folder(self, path, wild=False, removeFolderName=False, meta_info=False):
        res = []
        try:
            if wild:
                glob_res = glob.glob(path)
                if removeFolderName:
                    len_parent = len(os.path.dirname(path))+1
                    for file in glob_res:
                        res.append(file[len_parent:])
                else:
                    res = glob_res
            else:
                res = os.listdir(path)
        except OSError:
            pass

        if meta_info:
            result_meta = []
            parent_folder = path
            if wild:
                parent_folder = os.path.dirname(path)

            for file_path in res:
                result_meta.append({'path': file_path,
                                    'last_modified': self.getMTime(os.path.join(parent_folder, file_path)),
                                    'size': self.getFileSize(os.path.join(parent_folder, file_path))})

            res = result_meta

        return res

    def get_mtime(self, path):
        return os.path.getmtime(path)

    def get_file_size(self, path):
        return os.path.getsize(path)

    @contextlib.contextmanager
    def open_atomic(self, path, mode):
        parent = self.get_parent_folder(os.path.abspath(path))
        self.list_folder(parent)

        temp_dir = self.get_temp_folder()
        try:
            temp_path = os.path.join(temp_dir, os.path.basename(path))
            with open(temp_path, mode) as f:
                try:
                    yield f
                finally:
                    f.flush()  # flush file buffers
                    os.fsync(f.fileno())  # ensure all data are written to disk
            if platform.system() == "Windows":
                if os.path.exists(path):
                    os.remove(path)

            os.rename(temp_path, path)  # atomic move to target place
        finally:
            self.remove_folder(temp_dir)

    def get_temp_folder(self):
        if os.environ.get('AUGER_LOCAL_TMP_DIR'):
            self.create_folder(os.environ.get('AUGER_LOCAL_TMP_DIR'))

        return tempfile.mkdtemp(dir=os.environ.get('AUGER_LOCAL_TMP_DIR'))

    @contextlib.contextmanager
    def save_atomic(self, path):
        temp_dir = self.get_temp_folder()
        try:
            temp_path = os.path.join(temp_dir, os.path.basename(path))
            yield temp_path
        finally:
            self.remove_folder(temp_dir)

    def move_file(self, path_src, path_dst):
        if platform.system() == "Windows":
            if os.path.exists(path_dst):
                os.remove(path_dst)

        os.rename(path_src, path_dst)  # atomic move to target place

    def copy_file(self, path_src, path_dst):
        if self.is_file_exists(path_dst):
            self.remove_file(path_dst)

        shutil.copy2(path_src, path_dst)

    def copy_files(self, path_src, path_dst):
        if self.is_file_exists(path_dst):
            self.remove_file(path_dst)

        self.create_folder(path_dst)

        for fl in glob.glob(path_src):
            shutil.copy(fl, path_dst)

    def copy_folder(self, path_src, path_dst):
        shutil.copytree(path_src, path_dst)

    def archive_folder(self, path_src, format):
        shutil.make_archive(path_src, format, path_src)

    def download_file(self, path, local_path):
        from urllib.request import urlretrieve
        from auger_ml.Utils import url_encode

        self.create_parent_folder(local_path)
        if local_path and local_path.startswith("/var/src"):
            # For tests
            urlretrieve(url_encode(path), local_path)
        else:
            local_filename, headers = urlretrieve(url_encode(path))
            self.move_file(local_filename, local_path)
