import os.path
import shutil
import tempfile
import time
import threading
import unittest
import os
import pytest
import datetime

from  a2ml.api.utils import fsclient

pytestmark = pytest.mark.usefixtures('config_context')

def get_tests_temp_localdir():
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')
    path = os.path.abspath('./tests/temp')
    if worker_id is not None:
        path = os.path.join(path, worker_id)

    return path

class TestFSClient(unittest.TestCase):

    def _get_test_paths(self):
        paths = []
        paths.append(get_tests_temp_localdir())
        # if os.environ.get('AWS_ACCESS_KEY_ID'):
        #     paths.append('s3://auger-demo-datasets/auto-test')
                
        return paths

    def test_list_folder(self):
        for path in self._get_test_paths():
            if not fsclient.is_s3_path(path):
                path = os.path.abspath('./tests/fixtures')

            res = fsclient.list_folder(path)
            self.assertTrue(len(res) > 0)
            self.assertTrue(type(res[0]) == str)

            if not fsclient.is_s3_path(path):
                res = fsclient.list_folder(path+"/*.arff", wild=True, meta_info=True)
                self.assertTrue(res[-1]['path'].endswith(".arff"))
                self.assertNotEqual(res[0]['size'], 0)
                self.assertNotEqual(res[0]['last_modified'], 0)

    def test_list_folder_2(self):
        for path in self._get_test_paths():
            if not fsclient.is_s3_path(path):
                path = os.path.abspath('./tests/fixtures')

            res = fsclient.list_folder(path, remove_folder_name=True, meta_info=True)
            self.assertFalse(res[0]['path'].startswith(path))

            res = fsclient.list_folder(path+"/*.*", remove_folder_name=True, wild=True)
            self.assertFalse(res[0].startswith(path))
            self.assertFalse("*.*" in res[0])

            res = fsclient.list_folder(path, remove_folder_name=True, meta_info=True)
            self.assertFalse(res[0]['path'].startswith(path))

            res = fsclient.list_folder(path+"/*.*", remove_folder_name=True, meta_info=True, wild=True)
            self.assertFalse(res[0]['path'].startswith(path))
            self.assertFalse("*.*" in res[0]['path'])

            res = fsclient.list_folder(path, remove_folder_name=False, meta_info=True)
            self.assertTrue(res[0]['path'].startswith(path))

            res = fsclient.list_folder(path+"/*.*", remove_folder_name=False, wild=True)
            self.assertTrue(res[0].startswith(path))
            self.assertFalse("*.*" in res[0])

            res = fsclient.list_folder(path, remove_folder_name=False, meta_info=True)
            self.assertTrue(res[0]['path'].startswith(path))

            res = fsclient.list_folder(path+"/*.*", remove_folder_name=False, meta_info=True, wild=True)
            self.assertTrue(res[0]['path'].startswith(path))
            self.assertFalse("*.*" in res[0]['path'])

    # def test_list_folder_s3ex(self):
    #     if os.environ.get('AWS_ACCESS_KEY_ID_TEST'):
    #         path = 's3://auger-experiments'

    #         res = fsclient.list_folder(path+"/datasets/openml/data_xml/datset_99*.*", wild=True, meta_info=True)
    #         self.assertEqual(len(res), 10)
    #         self.assertEqual(res[0]['path'], 'datset_990.xml')
    #         self.assertEqual(res[0]['size'], 1101)
    #         self.assertNotEqual(res[0]['last_modified'], 0)

    # def test_removefile_s3ex(self):
    #     if os.environ.get('AWS_ACCESS_KEY_ID'):
    #         path = 's3://auger-demo-datasets'

    #         fsclient.remove_file(path+"/auto-test/channels/test_channel/datacache/advanced_model/traindata*", wild=True)

    def test_create_folder(self):
        for path in self._get_test_paths():
            path += "/testdir"
            fsclient.remove_folder(path)
            self.assertFalse(fsclient.is_folder_exists(path))

            fsclient.create_folder(path)
            self.assertTrue(fsclient.is_folder_exists(path))

    def test_copy_folder(self):
        for path in self._get_test_paths():
            path += "/testdir"
            fsclient.remove_folder(path)
            fsclient.create_folder(path)

            self.assertFalse(fsclient.is_file_exists(os.path.join(path, 'client.py'))) 
            fsclient.copy_folder( os.path.abspath('./tests/fixtures/test_folder'), path)
            self.assertTrue(fsclient.is_file_exists(os.path.join(path, 'client.py'))) 

            print(fsclient.list_folder(path))
            
    def test_create_parent_folder(self):
        for path in self._get_test_paths():
            path += "/testdir"
            fsclient.remove_folder(path)
            self.assertFalse(fsclient.is_folder_exists(path))

            fsclient.create_parent_folder(path+"/secondlevel")
            self.assertTrue(fsclient.is_folder_exists(path))
            self.assertFalse(fsclient.is_folder_exists(path+"/secondlevel"))

    def test_load_json(self):
        for path in self._get_test_paths():
            path = os.path.join(path, "test.json")
            fsclient.remove_file(path)
            self.assertFalse(fsclient.is_file_exists(path))

            data = {'param1': "value1", 'ar': [
                "item1", "item2"], "d": {"p2": "val2"}}
            fsclient.write_json_file(path, data)
            self.assertTrue(fsclient.is_file_exists(path))

            file_time = fsclient.get_mtime(path)
            #print(file_time)
            self.assertTrue(file_time)

            file_size = fsclient.get_file_size(path)
            print(file_size)
            self.assertTrue(file_size > 0)

            res = fsclient.read_json_file(path)
            self.assertEqual(data, res)

            for key in res.keys():
                self.assertTrue(type(key) == str)

    def test_open_text(self):
        for path in self._get_test_paths():
            path = os.path.join(path, "test.txt")
            fsclient.remove_file(path)
            self.assertFalse(fsclient.is_file_exists(path))

            data = "TEST DATA"
            with fsclient.open_file(path, 'w') as f:
                f.write(data)

            self.assertTrue(fsclient.is_file_exists(path))

            data_file = None
            with fsclient.open_file(path, 'r') as f:
                data_file = f.read()
            
            self.assertEqual(data, data_file)

    def test_saveload_object(self):
        for path in self._get_test_paths():
            path = os.path.join(path, "test.obj.gz")

            fsclient.remove_file(path)
            self.assertFalse(fsclient.is_file_exists(path))
            
            data = {'key': 'test', 'key1': 'test1'}
            fsclient.save_object_to_file(data, path)
            self.assertTrue(fsclient.is_file_exists(path))

            data2 = fsclient.load_object_from_file(path)
            self.assertEqual(data, data2)

    def test_saveatomic(self):
        for path in self._get_test_paths():
            path = os.path.join(path, "test.json")
            fsclient.remove_file(path)
            self.assertFalse(fsclient.is_file_exists(path))

            data = {'param1': "value1", 'ar': [
                "item1", "item2"], "d": {"p2": "val2"}}

            with fsclient.save_atomic(path) as temp_filepath:
                fsclient.write_json_file(temp_filepath, data)

            self.assertTrue(fsclient.is_file_exists(path))
            res = fsclient.read_json_file(path)
            self.assertEqual(data, res)

    # def test_load_json_file_pandas(self):
    #     from auger_ml.data_source.data_source_api_pandas import DataSourceAPIPandas

    #     path = 's3://auger-demo-datasets/auto-test'
    #     file_path = os.path.join(path, "datasets_info.json")
    #     fsclient.remove_file(file_path)
    #     self.assertFalse(fsclient.is_file_exists(file_path))

    #     url = 'https://drive.google.com/uc?export=download&id=1vDYksd8rb20uCnPX9iRyft6PaFgrhwkO'
    #     ds_infos = DataSourceAPIPandas({'data_path': url, 
    #         'augerInfo': {'dataTmpPath': path}})
    #     ds_infos.load(use_cache=False)
    #     print(ds_infos)

    # def test_load_arff_file_pandas(self):
    #     from auger_ml.data_source.data_source_api_pandas import DataSourceAPIPandas
        
    #     path = 's3://auger-demo-datasets/auto-test'
    #     file_path = os.path.join(path, "php5OMDBD.arff")
    #     fsclient.remove_file(file_path)
    #     self.assertFalse(fsclient.is_file_exists(file_path))

    #     url = 'https://www.openml.org/data/v1/download/17953251/dataset_40971.arff'
    #     ds_infos = DataSourceAPIPandas({'data_path': url, 
    #         'augerInfo': {'dataTmpPath': path}})
    #     ds_infos.load(use_cache=False)
    #     print(ds_infos)

    # def test_download_file(self):
    #     from auger_ml.Utils import download_file

    #     for path in self._get_test_paths():
    #         # url = 'https://s3-us-west-2.amazonaws.com/auger-experiments/datasets/examples/covtype.csv.gz'
    #         # path = os.path.join(path, "covtype.csv.gz")
    #         url = 'https://drive.google.com/uc?export=download&id=1vDYksd8rb20uCnPX9iRyft6PaFgrhwkO'
    #         file_path = os.path.join(path, "datasets_info.json")
    #         fsclient.remove_file(file_path)
    #         self.assertFalse(fsclient.is_file_exists(file_path))

    #         #fsclient.downloadFile(url, path)
    #         local_file_path = download_file(url, local_dir=path, force_download=False)

    #         self.assertTrue(fsclient.is_file_exists(file_path))
    #         self.assertTrue(fsclient.getFileSize(file_path) > 0)
    #         print(fsclient.getFileSize(file_path))
