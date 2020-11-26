import contextlib
import logging
import os
import shutil
import tempfile
import time

from .local_fsclient import LocalFSClient


def is_s3_path(path):
    return path.startswith("s3:/")


def _get_fsclient_bypath(path):
    if is_s3_path(path):
        from .s3_fsclient import S3FSClient
        return S3FSClient()
    else:
        return LocalFSClient()

def get_file_base_name(file_name):
    if '.' in file_name:
        separator_index = file_name.index('.')
        base_name = file_name[:separator_index]
        return base_name
    else:
        return file_name

def get_path_base_name(path):
    file_name = os.path.basename(path)
    return get_file_base_name(file_name)


def create_folder(path):
    client = _get_fsclient_bypath(path)
    client.create_folder(path)


def create_parent_folder(path):
    client = _get_fsclient_bypath(path)
    client.create_folder(get_parent_folder(path))


def get_parent_folder(path):
    return os.path.dirname(path)


def remove_folder(path, remove_self=True):
    client = _get_fsclient_bypath(path)
    client.remove_folder(path, remove_self)


def remove_file(path, wild=False):
    client = _get_fsclient_bypath(path)
    client.remove_file(path, wild)


def get_smart_open_transport_params(path):
    if is_s3_path(path):
        client = _get_fsclient_bypath(path)
        return client.get_smart_open_transport_params()

    return None


def open_file(path, mode, num_tries=20, encoding='utf-8', auto_decompression=True):
    import warnings

    if is_s3_path(path) and 'r' in mode:
        client = _get_fsclient_bypath(path)
        client.wait_for_path(path)

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        import smart_open

        nTry = 0
        while True:
            try:
                # TODO: support append mode for s3
                return smart_open.open(
                    path,
                    mode,
                    encoding=encoding,
                    ignore_ext=not auto_decompression,
                    transport_params=get_smart_open_transport_params(path)
                )
            except Exception as e:
                if nTry >= num_tries:
                    raise

            if 'w' in mode:
                remove_file(path)

            nTry = nTry + 1
            time.sleep(1)


def s3fs_open(path, mode='rb'):
    if is_s3_path(path):
        client = _get_fsclient_bypath(path)
        return client.s3fs_open(path, mode)

    return path


def list_folder(path, wild=False, remove_folder_name=True, meta_info=False):
    client = _get_fsclient_bypath(path)

    if wild:
        if not client.is_folder_exists(get_parent_folder(path)):
            return []
    else:
        if not client.is_folder_exists(path):
            return []

    return client.list_folder(path, wild=wild, remove_folder_name=remove_folder_name, meta_info=meta_info)


def get_mtime(path):
    client = _get_fsclient_bypath(path)
    return client.get_mtime(path)


def get_file_size(path):
    client = _get_fsclient_bypath(path)
    return client.get_file_size(path)

# @classmethod
# def openFile(cls, path, mode):
#     client = cls._get_fsclient_bypath(path)
#     return client.open(path, mode)


def is_file_exists(path):
    client = _get_fsclient_bypath(path)
    return client.is_file_exists(path)


def is_folder_exists(path):
    client = _get_fsclient_bypath(path)
    return client.is_folder_exists(path)


def read_text_file(path):
    client = _get_fsclient_bypath(path)
    return client.read_text_file(path)


def write_text_file(path, data, atomic=False, mode="w"):
    client = _get_fsclient_bypath(path)
    client.write_text_file(path, data, atomic=atomic, mode=mode)


def write_json_file(path, data, atomic=False, allow_nan=False):
    from .json_utils import json_dumps_np
    write_text_file(path, json_dumps_np(
        data, allow_nan=allow_nan), atomic=atomic)


def update_json_file(path, data, atomic=False, allow_nan=False):
    from .json_utils import json_dumps_np
    fileData = read_json_file(path)
    fileData.update(data)
    write_text_file(path, json_dumps_np(
        fileData, allow_nan=allow_nan), atomic=atomic)


def read_json_file(path, check_if_exist=True, if_wait_for_file=False):
    import json

    if not is_s3_path(path):
        list_folder(get_parent_folder(path))

    wait_for_file(path, if_wait_for_file=if_wait_for_file)

    if check_if_exist and not is_file_exists(path):
        return {}

    nTry = 0
    while True:
        json_text = read_text_file(path)
        try:
            return json.loads(json_text)
        except Exception as e:
            logging.error("Load json failed: %s.Text: %s" %
                          (repr(e), json_text))
            if nTry > 10:
                raise

            nTry += 1
            time.sleep(2)

    return {}


def wait_for_file(path, if_wait_for_file, num_tries=30, interval_sec=1):
    if if_wait_for_file:
        nTry = 0
        while nTry <= num_tries:
            if is_file_exists(path):
                break

            if path != "/mnt/ready.txt":
                wait_for_fs_ready()

            if is_file_exists(path):
                break

            logging.info("File %s does not exist. Wait for %s sec" %
                         (path, interval_sec))

            nTry = nTry + 1
            time.sleep(interval_sec)

        return is_file_exists(path)

    return True


def wait_for_fs_ready():
    if not os.environ.get('S3_DATA_PATH') and os.environ.get('AUGER_ROOT_DIR', '').startswith('/mnt'):
        return wait_for_file("/mnt/ready.txt", if_wait_for_file=True, num_tries=30, interval_sec=10)

    return True


def load_json_files(paths):
    result = []
    for path in paths:
        try:
            result.append(read_json_file(path))
        except Exception as e:
            logging.exception("loadJSONFiles failed.")

    return result


def copy_file(path_src, path_dst, check_if_exist=True):

    if check_if_exist:
        client = _get_fsclient_bypath(path_src)
        if not client.is_file_exists(path_src):
            return

    client = _get_fsclient_bypath(path_dst)
    client.copy_file(path_src, path_dst)


def copy_files(path_src, path_dst):
    client = _get_fsclient_bypath(path_src)
    client.copy_files(path_src, path_dst)


def archive_folder(path_src, fmt='zip'):
    if is_s3_path(path_src):
        localClient = LocalFSClient()

        with localClient.save_atomic(path_src) as local_path:
            logging.info("archiveDir local path:%s" % local_path)

            clientS3 = _get_fsclient_bypath(path_src)
            clientS3.download_folder(path_src, local_path)

            localClient.archive_folder(local_path, fmt)

            clientS3.move_file(local_path+'.zip', path_src+'.zip')
            return

    client = _get_fsclient_bypath(path_src)
    client.archive_folder(path_src, fmt)


def copy_folder(path_src, path_dst):
    if is_folder_exists(path_dst):
        remove_folder(path_dst)

    if is_s3_path(path_dst):
        client = _get_fsclient_bypath(path_dst)
        client.copy_folder(path_src, path_dst)
    else:
        client = _get_fsclient_bypath(path_src)
        client.copy_folder(path_src, path_dst)


def _save_to_pickle(obj, path, compress):
    import joblib

    joblib.dump(obj, path, compress=compress, protocol=4)

def _save_to_feather(obj, path, compress):
    from pyarrow import feather

    feather.write_feather(obj, path, compression=compress)

def save_object_to_file(obj, path, fmt="pickle"):
    
    remove_file(path)
    create_parent_folder(path)

    try:
        compress = 0
        if path.endswith('.gz'):
            compress = ('gzip', 3)
        elif path.endswith('.zstd'):
            compress = "zstd"
        elif path.endswith('.lz4'):
            compress = "lz4"

        if is_s3_path(path):
            with save_atomic(path) as local_path:
                if fmt == "pickle":
                    _save_to_pickle(obj, local_path, compress=compress)
                elif fmt == "feather":
                    _save_to_feather(obj, local_path, compress=compress)
        else:
            if fmt == "pickle":
                _save_to_pickle(obj, path, compress=compress)
            elif fmt == "feather":
                _save_to_feather(obj, path, compress=compress)

    except:
        remove_file(path)
        raise


@contextlib.contextmanager
def save_atomic(path, move_file=True):
    localClient = LocalFSClient()

    with localClient.save_atomic(path) as local_path:
        yield local_path

        if move_file:
            client = _get_fsclient_bypath(path)
            client.move_file(local_path, path)


@contextlib.contextmanager
def save_local(path, move_file=True):
    if is_s3_path(path):
        localClient = LocalFSClient()

        with localClient.save_atomic(path) as local_path:
            yield local_path

            if move_file:
                client = _get_fsclient_bypath(path)
                client.move_file(local_path, path)
    else:
        yield path


@contextlib.contextmanager
def with_cur_dir(dir_path):
    create_folder(dir_path)

    old_path = os.getcwd()
    os.chdir(dir_path)
    yield
    os.chdir(old_path)

def move_file(path_src, path_dst):
    #print(path_src, path_dst)

    client = _get_fsclient_bypath(path_dst)
    client.move_file(path_src, path_dst)


def download_file(path, local_path):
    if path.startswith("http:") or path.startswith("https:"):
        client = _get_fsclient_bypath(local_path)
        client.download_file(path, local_path)
    elif is_s3_path(path):
        client = _get_fsclient_bypath(path)
        client.download_file(path, local_path)
    else:
        copy_file(path, local_path)

@contextlib.contextmanager
def with_s3_downloaded_or_local_file(source_path):
    if source_path.startswith("s3:"):
        tmp_dir = tempfile.mkdtemp()
        try:
            tmp_file = os.path.join(tmp_dir, os.path.basename(source_path))
            download_file(source_path, tmp_file)
            yield tmp_file
        finally:
            shutil.rmtree(tmp_dir)
    else:
        yield source_path


def load_object_from_file(path, use_local_cache=False):
    import joblib
    import urllib.parse

    path_to_load = None
    if is_s3_path(path):
        if use_local_cache:
            temp_path = "/temp"
            if os.environ.get("AUGER_LOCAL_TMP_DIR", ''):
                temp_path = os.environ.get("AUGER_LOCAL_TMP_DIR", '')

            local_path = os.path.join(temp_path, urllib.parse.urlparse(path).path )
            logging.info("Local cache path: %s"%local_path)
            if not is_file_exists(local_path):
                local_lock_path = local_path + '.lock'
                create_parent_folder(local_lock_path)
                f_lock = None
                try:
                    f_lock = open(local_lock_path, 'x')
                except Exception as e:
                    #logging.exception("Open lock file failed.")
                    pass

                if f_lock:
                    try:
                        if not is_file_exists(local_path):
                            with save_atomic(local_path) as local_tmp_path:
                                logging.info("Download file from s3 to: %s, temp folder: %s" % (
                                    local_path, local_tmp_path))
                                download_file(path, local_tmp_path)
                    finally:
                        f_lock.close()
                        remove_file(local_lock_path)
                else:
                    wait_for_file(local_path, True,
                                  num_tries=300, interval_sec=10)

            path_to_load = local_path
        else:
            with save_atomic(path, move_file=False) as local_tmp_path:
                download_file(path, local_tmp_path)
                return joblib.load(local_tmp_path)
    else:
        path_to_load = path

    return joblib.load(path_to_load)

def load_npobject_from_file(path):
    import numpy as np

    if is_s3_path(path):
        with save_atomic(path, move_file=False) as local_path:
            download_file(path, local_path)
            return np.load(local_path, allow_pickle=True)

    return np.load(path, allow_pickle=True)

def _read_feather(path, features=None):
    from pyarrow import feather

    if path.endswith(".gz") or path.endswith(".zip"):
        with open_file(path, 'rb', encoding=None) as local_file:
            return feather.read_feather(local_file, columns=features, use_threads=bool(True))

    return feather.read_feather(path, columns=features, use_threads=bool(True))

def load_db_from_feather_file(path, features=None):
    if is_s3_path(path):
        with save_atomic(path, move_file=False) as local_path:
            download_file(path, local_path)
            return _read_feather(local_path, features)

    return _read_feather(path, features)

def _read_parquet(path, features=None):
    import pandas as pd

    return pd.read_parquet(path, columns=features)

def load_db_from_parquet_file(path, features=None):
    if is_s3_path(path):
        with save_atomic(path, move_file=False) as local_path:
            download_file(path, local_path)
            return _read_parquet(local_path, features)

    return _read_parquet(path, features)

def is_abs_path(path):
    import platform

    if not path:
        return False

    if is_s3_path(path):
        return True

    if path.startswith("http:") or path.startswith("https:"):
        return True

    if platform.system().lower() == 'windows':
        return ':\\' in path or ':/' in path

    return path[0] == "/" or path[0] == "\\"


def merge_folder_files(path, remove_folder=True):
    if is_file_exists(path):
        return

    res = os.path.splitext(path)
    path_no_ext = res[0]
    extension = res[1]
    if not is_folder_exists(path_no_ext):
        return

    client = _get_fsclient_bypath(path)
    files = list(client.list_folder(path_no_ext))

    with open_file(path, 'w') as file_output:
        for idx, file in enumerate(files):
            if file.endswith(extension):
                with open_file(os.path.join(path_no_ext, file), 'rb') as file_input:
                    data_file = file_input.read()
                    if extension == ".json":
                        data_file = _process_merged_json(
                            data_file, idx, len(files))

                    file_output.write(data_file)

    if remove_folder:
        client.remove_folder(path_no_ext)


def _process_merged_json(data_file, idx, total_len):
    remove_last = False
    remove_first = False

    if idx == 0:
        remove_last = True
    elif idx == total_len-1:
        remove_first = True
    else:
        remove_last = True
        remove_first = True

    if remove_last:
        index = data_file.rindex(']')
        if index >= 0:
            data_file = data_file[:index] + "," + data_file[index + 1:]
    if remove_first:
        index = data_file.index('[')
        if index >= 0:
            data_file = data_file[:index] + data_file[index + 1:]

    return data_file
