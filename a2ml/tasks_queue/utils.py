import uuid

from collections import OrderedDict
from a2ml.api.utils import fsclient

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
        all_local_files = fsclient.listFolder(os.path.join(local_dir, file_name+".*"), wild=True, removeFolderName=True)
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
            fsclient.removeFile(local_file_path)
        else:
            download_file = False

    if download_file:
        logging.info("Download to local file path: %s"%local_file_path)
        fsclient.downloadFile(remote_path, local_file_path)

    return local_file_path
