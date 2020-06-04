import uuid
import dateutil
from collections import OrderedDict
from collections.abc import Iterable
import time

from a2ml.api.utils import fsclient


def to_list(obj):
    if obj:
        if isinstance(obj, Iterable) and not isinstance(obj, str):
            return list(obj)
        else:
            return [obj]
    else:
        return []

def dict_dig(obj, *path):
    curr = obj
    i = 0

    while curr and i < len(path) and isinstance(curr, dict):
        curr = curr.get(path[i], None)
        i += 1

    return curr

def get_uid():
    return uuid.uuid4().hex[:15].upper()

def get_uid4():
    return str(uuid.uuid4())

def remove_dups_from_list(ar):
    return list(OrderedDict.fromkeys(ar))

def process_arff_line(line, date_attrs):
    if "@attribute" in line.lower():
        parts = line.split(maxsplit=3)
        if len(parts) > 2 and parts[2].lower() == 'date':
            line = parts[0]+ ' ' + parts[1] + ' string\n'
            date_field = parts[1].strip("\"\'")
            date_format = parts[3].strip("\"\'\n")

            date_attrs[date_field] = date_format

    return line

def download_file(remote_path, local_dir, file_name, force_download=False):
    local_file_path = ""
    download_file = True
    remote_file_info = {}

    logging.info("download_file: %s, %s, %s, %s"%(remote_path, local_dir, file_name, force_download))
    if file_name:
        all_local_files = fsclient.list_folder(os.path.join(local_dir, file_name+".*"), wild=True, remove_folder_name=True)
        #print(all_local_files)
        if all_local_files:
            local_file_path = os.path.join( local_dir, all_local_files[0])

    if not local_file_path:
        remote_file_info = get_remote_file_info(remote_path)
        if not remote_file_info:
            raise Exception("Remote path does not exist or unaccessible: %s"%(remote_path))

        if  file_name:
            local_file_path = os.path.join(local_dir,
                file_name+remote_file_info.get('file_ext'))
        else:
            local_file_path = os.path.join(local_dir,
                remote_file_info.get('file_name') + remote_file_info.get('file_ext'))

    if fsclient.isFileExists(local_file_path):
        etag_changed = False
        file_size_changed = False

        if force_download:
            logging.info("Force download file again.")

        if force_download or etag_changed or file_size_changed:
            fsclient.remove_file(local_file_path)
        else:
            download_file = False

    if download_file:
        logging.info("Download to local file path: %s"%local_file_path)
        fsclient.download_file(remote_path, local_file_path)

    return local_file_path

# by default value from other dict overwrites value in d
def merge_dicts(d, other, concat_func=lambda v, ov: ov):
    from collections import Mapping

    for k, v in other.items():
        d_v = d.get(k)
        if isinstance(v, Mapping) and isinstance(d_v, Mapping):
            merge_dicts(d_v, v, concat_func)
        else:
            if k in d:
                d[k] = concat_func(d[k], v)
            else:
                d[k] = v

    return d

def convert_to_date(date):
    if type(date) is str:
        return dateutil.parser.parse(date).date()
    elif type(date) is time.time:
        return date.date()
    else:
        return date

