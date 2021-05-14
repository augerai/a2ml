import uuid
import dateutil
from collections import OrderedDict
from collections.abc import Iterable
import time
import os
import logging
import pandas as pd
import contextlib

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

def url_encode(path):
    try:
        from urllib.parse import urlparse, parse_qs, quote
    except ImportError:
        from urlparse import urlparse, parse_qs, quote

    return quote(path, safe='#&%:/?*=\'')

def parse_url(remote_path):
    try:
        from urllib.parse import urlparse, parse_qs, quote
    except ImportError:
        from urlparse import urlparse, parse_qs, quote

    uri = urlparse(remote_path)
    params = parse_qs(uri.query)

    return uri.path, params

def get_remote_file_info(remote_path):
    from urllib.request import urlopen
    import urllib
    import codecs

    try:
        from urllib.parse import urlparse, parse_qs
    except ImportError:
        from urlparse import urlparse, parse_qs

    file_info  = {}
    remote_path1 = url_encode(remote_path)
    # logging.info("Get info for file from url: %s" % remote_path1)

    req = urlopen(remote_path1)
    #print(req.info())

    # Make local path
    contentDisp = req.getheader('Content-Disposition')
    contentType = req.getheader('Content-Type')
    fileext = ''
    if contentType:
        if contentType == 'application/x-gzip':
            fileext = '.gz'
        elif contentType == 'text/csv':
            fileext = '.csv'

    filename = ''
    if contentDisp:
        items = contentDisp.split(';')
        for item in items:
            item = item.strip()
            if item.startswith("filename=\""):
                filename = item[10:-1]
                break
            elif item.startswith("filename="):
                filename = item[9:]
                break

    if not filename:
        uri = urlparse(remote_path)
        params = parse_qs(uri.query)
        if len(params.get('id', []))>0:
            filename = params['id'][0]+fileext
        else:
            if len(uri.path)>0 and len(os.path.basename(uri.path))>0:
                filename = os.path.basename(uri.path)
            else:
                filename = get_uid()+fileext

    remote_file_size = 0
    try:
        remote_file_size = int(req.getheader('Content-Length'))
    except:
        pass

    remote_file_etag = ''
    try:
        remote_file_etag = req.getheader('ETag').strip("\"\'")
    except:
        pass

    req.close()

    file_info = {
        'file_name': "",
        'file_ext': "",
        'file_size': remote_file_size,
        'file_etag': remote_file_etag
    }

    dot_index = filename.find('.')
    if dot_index>=0:
        file_info['file_name'] = filename[:dot_index]
        file_info['file_ext'] = filename[dot_index:]
    else:
        file_info['file_name'] = filename

    return file_info

def download_file(remote_path, local_dir, file_name, force_download=False):
    local_file_path = ""
    download_file = True
    remote_file_info = {}

    #logging.info("download_file: %s, %s, %s, %s"%(remote_path, local_dir, file_name, force_download))
    if file_name:
        all_local_files = fsclient.list_folder(os.path.join(local_dir, file_name+".*"), wild=True, remove_folder_name=True)
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

    if fsclient.is_file_exists(local_file_path):
        etag_changed = False
        file_size_changed = False

        if force_download:
            logging.info("Force download file again.")

        if force_download or etag_changed or file_size_changed:
            fsclient.remove_file(local_file_path)
        else:
            download_file = False

    if download_file:
        #logging.info("Download to local file path: %s"%local_file_path)
        fsclient.download_file(remote_path, local_file_path)

    return local_file_path

# by default value from other dict overwrites value in d
def merge_dicts(d, other, concat_func=lambda v, ov: ov):
    from collections.abc import Mapping

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

@contextlib.contextmanager
def convert_source(source, name):
    if source is not None and isinstance(source, pd.DataFrame):
        with fsclient.save_atomic("%s.parquet"%name, move_file=False) as local_path:
            source.to_parquet(local_path, index=False, compression="gzip")
            yield local_path
    else:
        yield source

def retry_helper(func, retry_errors=[], num_try=10, delay=10, ctx=None):
    nTry = 0
    while True:
        try:
            return func()
        except Exception as exc:
            retry_exc = False
            if not retry_errors:
                retry_exc = True
            else:    
                for retry_error in retry_errors:
                    if retry_error in str(exc):
                        retry_exc = True
                        break

            if retry_exc and nTry < num_try:
                if ctx:
                    ctx.log("Retry '%s', error: '%s'. Sleep and try again. Num try: %s"%(func, str(exc), nTry))
                else:
                    logging.error("Retry '%s', error: '%s'. Sleep and try again. Num try: %s"%(func, str(exc), nTry))

                nTry += 1
                time.sleep(delay*nTry)
            else:
                raise                

def sort_arrays(ar1, ar2, top_n=None, desc=True):
    p = ar1.argsort()
    if desc:
        p = p[::-1]
    if top_n:
        p = p[:top_n]

    return ar1[p], ar2[p]

def getsizeof_deep(obj):
    import gc
    import sys

    sz = 0
    try:
        marked = {id(obj)}
        obj_q = [obj]

        while obj_q:
            sz += sum(map(sys.getsizeof, obj_q))

            # Lookup all the object referred to by the object in obj_q.
            # See: https://docs.python.org/3.7/library/gc.html#gc.get_referents
            all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

            # Filter object that are already marked.
            # Using dict notation will prevent repeated objects.
            new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

            # The new obj_q will be the ones that were not marked,
            # and we will update marked with their ids so we will
            # not traverse them again.
            obj_q = new_refr.values()
            marked.update(new_refr.keys())
    except:
        logging.exception("getsizeof_deep failed.")
        sz = None

    return sz
